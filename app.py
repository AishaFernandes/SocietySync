import json
import logging
import uuid
from functools import wraps

import boto3
import psycopg2
import psycopg2.errors
import psycopg2.extras
from botocore.config import Config
from flask import (Flask, flash, g, jsonify, redirect, render_template_string,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

BUCKET = config.S3_BUCKET
s3 = boto3.client("s3", region_name="eu-north-1", config=Config(signature_version="s3v4"))
ALLOWED_EXT = {"png", "jpg", "jpeg", "pdf", "txt"}

log = logging.getLogger("societysync")
log.setLevel(logging.INFO)
_h = logging.FileHandler("/var/log/societysync/app.log")
_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(_h)

STATUSES = ("open", "in_progress", "resolved")

sns = boto3.client("sns", region_name="eu-north-1")
TOPIC_ARN = config.SNS_TOPIC_ARN


def _clean(t):
    return "".join(str(t).split()).encode("ascii", "ignore").decode()


def email_subject(event_type, d):
    if event_type == "notice_created":
        return ("New notice: " + _clean(d.get("title", "")))[:100]
    if event_type == "complaint_created":
        return ("New complaint #%s: %s" % (d.get("id"), _clean(d.get("subject", ""))))[:100]
    return ("SocietySync: " + event_type)[:100]


def email_text(event_type, d):
    if event_type == "notice_created":
        return ("A new notice has been posted on SocietySync.\n\n"
                "Title: %s\n\n%s\n\nLog in to read it on the notice board."
                % (d.get("title", ""), d.get("body", "")))
    if event_type == "complaint_created":
        return ("A new complaint has been raised on SocietySync.\n\n"
                "Complaint #%s: %s\nRaised by: %s\n\nLog in to review it and update its status."
                % (d.get("id"), d.get("subject", ""), d.get("by", "a resident")))
    return json.dumps(d)


def publish_event(event_type, **data):
    """Publish to SNS; a messaging problem must never break the web request."""
    try:
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=email_subject(event_type, data),
            MessageStructure="json",
            Message=json.dumps({
                "default": json.dumps({"event": event_type, **data}),
                "email": email_text(event_type, data)
            })
        )
        log.info("published event: %s", event_type)
    except Exception as e:
        log.error("sns publish failed: %s", e)


# database helpers
def db():
    if "db" not in g:
        g.db = psycopg2.connect(**config.DB, cursor_factory=psycopg2.extras.RealDictCursor)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def q(sql, args=(), one=False, commit=False):
    with db().cursor() as cur:
        cur.execute(sql, args)
        rows = cur.fetchall() if cur.description else None
        if commit:
            db().commit()
        if one:
            return rows[0] if rows else None
        return rows


# auth helpers
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "uid" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*a, **kw):
        if session.get("role") != "admin":
            return "Admins only", 403
        return f(*a, **kw)
    return wrapper


# templates
from ui import BASE, COMPLAINTS, LOGIN, NOTICES, REGISTER


def page(tpl, **ctx):
    return render_template_string(BASE, body=render_template_string(tpl, **ctx))


# routes
@app.route("/health")
def health():
    try:
        q("SELECT 1")
        return jsonify(status="ok", db=True)
    except Exception as e:
        log.error("health check failed: %s", e)
        return jsonify(status="error", db=False), 500


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        email = f["email"].strip().lower()
        try:
            q("INSERT INTO users (name, email, password_hash, flat_no) VALUES (%s,%s,%s,%s)",
              (f["name"], email, generate_password_hash(f["password"]), f.get("flat_no")),
              commit=True)
        except psycopg2.errors.UniqueViolation:
            db().rollback()
            flash("That email is already registered.")
            return redirect(url_for("register"))
        log.info("user registered: %s", email)
        flash("Registered. Please log in.")
        return redirect(url_for("login"))
    return page(REGISTER)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        u = q("SELECT * FROM users WHERE email=%s", (email,), one=True)
        if u and check_password_hash(u["password_hash"], request.form["password"]):
            session.update(uid=u["id"], name=u["name"], role=u["role"])
            log.info("login ok: %s", email)
            return redirect(url_for("index"))
        log.warning("login failed: %s", email)
        flash("Wrong email or password.")
    return page(LOGIN)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    notices = q("SELECT n.*, u.name AS author FROM notices n JOIN users u ON u.id = n.created_by ORDER BY n.created_at DESC")
    return page(NOTICES, notices=notices)


@app.route("/notices", methods=["POST"])
@admin_required
def create_notice():
    n = q("INSERT INTO notices (title, body, created_by) VALUES (%s,%s,%s) RETURNING id",
          (request.form["title"], request.form["body"], session["uid"]), one=True, commit=True)
    log.info("notice created id=%s", n["id"])
    publish_event("notice_created", id=n["id"], title=request.form["title"], body=request.form["body"])
    flash("Notice posted.")
    return redirect(url_for("index"))


@app.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():
    if request.method == "POST":
        key = None
        f = request.files.get("attachment")
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_EXT:
                flash("File type not allowed (png, jpg, pdf, txt only).")
                return redirect(url_for("complaints"))
            key = f"complaints/{session['uid']}/{uuid.uuid4().hex}-{secure_filename(f.filename)}"
            s3.upload_fileobj(f, BUCKET, key, ExtraArgs={
                "ContentType": f.mimetype or "application/octet-stream",
                "ServerSideEncryption": "AES256"})
            log.info("uploaded s3://%s/%s", BUCKET, key)
        c = q("""INSERT INTO complaints (user_id, subject, description, attachment_key)
                 VALUES (%s,%s,%s,%s) RETURNING id""",
              (session["uid"], request.form["subject"], request.form.get("description"), key),
              one=True, commit=True)
        log.info("complaint created id=%s user=%s", c["id"], session["uid"])
        publish_event("complaint_created", id=c["id"], subject=request.form["subject"],
                      user_id=session["uid"], by=session["name"])
        flash("Complaint submitted.")
        return redirect(url_for("complaints"))

    base = """SELECT c.*, u.name, u.flat_no FROM complaints c JOIN users u ON u.id = c.user_id"""
    if session["role"] == "admin":
        rows = q(base + " ORDER BY c.id DESC")
    else:
        rows = q(base + " WHERE c.user_id=%s ORDER BY c.id DESC", (session["uid"],))
    return page(COMPLAINTS, complaints=rows, statuses=STATUSES)


@app.route("/complaints/<int:cid>/status", methods=["POST"])
@admin_required
def complaint_status(cid):
    s = request.form["status"]
    if s not in STATUSES:
        return "Bad status", 400
    q("UPDATE complaints SET status=%s, updated_at=now() WHERE id=%s", (s, cid), commit=True)
    log.info("complaint %s status -> %s", cid, s)
    return redirect(url_for("complaints"))


@app.route("/complaints/<int:cid>/attachment")
@login_required
def attachment(cid):
    c = q("SELECT user_id, attachment_key FROM complaints WHERE id=%s", (cid,), one=True)
    if not c or not c["attachment_key"]:
        return "Not found", 404
    if session["role"] != "admin" and c["user_id"] != session["uid"]:
        return "Forbidden", 403
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": c["attachment_key"]}, ExpiresIn=300)
    log.info("presigned download complaint=%s user=%s", cid, session["uid"])
    return redirect(url)