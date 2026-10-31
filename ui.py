BASE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SocietySync</title>
<style>
:root{--bg:#f3f5f9;--card:#ffffff;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--brand:#2563eb;--brand-dark:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand);text-decoration:none}
a:hover{text-decoration:underline}
header{background:var(--card);border-bottom:1px solid var(--line)}
.bar{max-width:880px;margin:0 auto;padding:0 20px;height:60px;display:flex;align-items:center;gap:24px}
.brand{font-weight:700;font-size:18px;color:var(--ink);display:flex;align-items:center;gap:8px}
.brand:hover{text-decoration:none}
.logo{width:26px;height:26px;border-radius:7px;background:var(--brand);color:#fff;display:grid;place-items:center;font-size:14px}
nav{display:flex;gap:4px;flex:1}
nav a{padding:6px 12px;border-radius:8px;color:var(--muted);font-weight:500}
nav a:hover{background:var(--bg);text-decoration:none;color:var(--ink)}
nav a.active{background:#eaf1ff;color:var(--brand)}
.user{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--muted)}
.role{background:#eaf1ff;color:var(--brand);border-radius:999px;padding:1px 9px;font-size:12px;font-weight:600;text-transform:capitalize}
main{max-width:880px;margin:28px auto;padding:0 20px}
h1{font-size:24px;margin:0 0 18px}
h2{font-size:17px;margin:0 0 12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.narrow{max-width:420px;margin:40px auto}
label{display:block;font-size:13px;font-weight:600;margin:0 0 4px}
input[type=text],input[type=email],input[type=password],textarea,select{width:100%;padding:9px 11px;border:1px solid #d1d5db;border-radius:8px;font:inherit;background:#fff;color:var(--ink)}
input:focus,textarea:focus,select:focus{outline:2px solid #bfd3ff;border-color:var(--brand)}
textarea{min-height:90px;resize:vertical}
input[type=file]{font-size:14px}
.field{margin-bottom:14px}
button{background:var(--brand);color:#fff;border:0;border-radius:8px;padding:9px 16px;font:inherit;font-weight:600;cursor:pointer}
button:hover{background:var(--brand-dark)}
button.small{padding:6px 12px;font-size:13px}
.muted{color:var(--muted)}
.flash{background:#eaf1ff;border:1px solid #c7d8ff;color:#1e3a8a;padding:10px 14px;border-radius:8px;margin-bottom:16px}
.item{border-top:1px solid var(--line);padding:14px 0}
.item:first-child{border-top:0;padding-top:0}
.item h3{margin:0 0 4px;font-size:16px}
.body{white-space:pre-wrap;margin:4px 0 8px}
.meta{font-size:13px;color:var(--muted)}
.badge{display:inline-block;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:600;margin-left:8px;vertical-align:middle;text-transform:capitalize}
.b-open{background:#fef3c7;color:#92400e}
.b-in_progress{background:#dbeafe;color:#1e40af}
.b-resolved{background:#dcfce7;color:#166534}
.row{display:flex;gap:8px;align-items:center;margin-top:10px}
.row select{width:auto}
.empty{text-align:center;color:var(--muted);padding:20px 0}
footer{text-align:center;color:var(--muted);font-size:13px;padding:20px}
@media(max-width:600px){.bar{gap:10px;padding:0 12px}.user .n{display:none}}
</style>
</head>
<body>
<header><div class="bar">
<a class="brand" href="/"><span class="logo">S</span>SocietySync</a>
{% if session.uid %}
<nav>
<a href="/" class="{{ 'active' if request.path == '/' }}">Notices</a>
<a href="/complaints" class="{{ 'active' if request.path.startswith('/complaints') }}">Complaints</a>
</nav>
<div class="user"><span class="n">{{ session.name }}</span><span class="role">{{ session.role }}</span><a href="/logout">Logout</a></div>
{% else %}
<nav></nav>
<div class="user"><a href="/login">Login</a><a href="/register">Register</a></div>
{% endif %}
</div></header>
<main>
{% for m in get_flashed_messages() %}<div class="flash">{{ m }}</div>{% endfor %}
{{ body|safe }}
</main>
<footer>SocietySync &middot; Flask on AWS (EC2, RDS, S3, SNS/SQS)</footer>
</body>
</html>"""

REGISTER = """<div class="card narrow"><h2>Create your account</h2>
<form method="post">
<div class="field"><label>Full name</label><input type="text" name="name" required></div>
<div class="field"><label>Email</label><input type="email" name="email" required></div>
<div class="field"><label>Flat number</label><input type="text" name="flat_no"></div>
<div class="field"><label>Password</label><input type="password" name="password" required></div>
<button style="width:100%">Register</button>
<p class="muted" style="text-align:center;margin:14px 0 0">Already registered? <a href="/login">Log in</a></p>
</form></div>"""

LOGIN = """<div class="card narrow"><h2>Log in</h2>
<form method="post">
<div class="field"><label>Email</label><input type="email" name="email" required></div>
<div class="field"><label>Password</label><input type="password" name="password" required></div>
<button style="width:100%">Log in</button>
<p class="muted" style="text-align:center;margin:14px 0 0">New here? <a href="/register">Create an account</a></p>
</form></div>"""

NOTICES = """<h1>Notice board</h1>
{% if session.role == 'admin' %}<div class="card"><h2>Post a notice</h2>
<form method="post" action="/notices">
<div class="field"><label>Title</label><input type="text" name="title" required></div>
<div class="field"><label>Message</label><textarea name="body" required></textarea></div>
<button>Post notice</button></form></div>{% endif %}
<div class="card">
{% for n in notices %}<div class="item"><h3>{{ n.title }}</h3>
<div class="body">{{ n.body }}</div>
<div class="meta">Posted by {{ n.author }} &middot; {{ n.created_at.strftime('%d %b %Y %H:%M') }} UTC</div></div>
{% else %}<div class="empty">No notices yet.</div>{% endfor %}</div>"""

COMPLAINTS = """<h1>Complaints</h1>
<div class="card"><h2>Raise a complaint</h2>
<form method="post" enctype="multipart/form-data">
<div class="field"><label>Subject</label><input type="text" name="subject" required></div>
<div class="field"><label>Details</label><textarea name="description"></textarea></div>
<div class="field"><label>Attachment (optional)</label><input type="file" name="attachment" accept=".png,.jpg,.jpeg,.pdf,.txt"><div class="meta">PNG, JPG, PDF or TXT, up to 5 MB</div></div>
<button>Submit complaint</button></form></div>
<div class="card"><h2>{{ 'All complaints' if session.role == 'admin' else 'Your complaints' }}</h2>
{% for c in complaints %}<div class="item">
<h3>#{{ c.id }} {{ c.subject }}<span class="badge b-{{ c.status }}">{{ c.status.replace('_', ' ') }}</span></h3>
{% if c.description %}<div class="body">{{ c.description }}</div>{% endif %}
{% if c.attachment_key %}<div><a href="/complaints/{{ c.id }}/attachment" target="_blank">View attachment</a></div>{% endif %}
<div class="meta">{{ c.name }} (Flat {{ c.flat_no or '-' }}) &middot; {{ c.created_at.strftime('%d %b %Y %H:%M') }} UTC</div>
{% if session.role == 'admin' %}<form class="row" method="post" action="/complaints/{{ c.id }}/status">
<select name="status">{% for s in statuses %}<option value="{{ s }}" {{ 'selected' if s == c.status }}>{{ s.replace('_', ' ') }}</option>{% endfor %}</select>
<button class="small">Update</button></form>{% endif %}
</div>
{% else %}<div class="empty">No complaints yet.</div>{% endfor %}</div>"""