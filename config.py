import boto3

_ssm = boto3.client("ssm", region_name="eu-north-1")


def _p(name, secret=False):
    return _ssm.get_parameter(Name=f"/societysync/{name}", WithDecryption=secret)["Parameter"]["Value"]


SECRET_KEY = _p("secret-key", True)
DB = dict(
    host=_p("db-host"),
    dbname=_p("db-name"),
    user=_p("db-user"),
    password=_p("db-password", True),
    sslmode="require",
    connect_timeout=5,
)