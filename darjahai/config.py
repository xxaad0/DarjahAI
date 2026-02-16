import os

def str_to_bool(x):
    return str(x).lower() in ("1", "true", "yes", "on")

def set_pg(url: str | None)-> str|None:
    if not url:
        return url
    return url.replace("postgres://","postgresql://",1) if url.startswith("postgres://")else url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")


    SQLALCHEMY_DATABASE_URI = set_pg(
        os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or "sqlite:///darjahai.db"
    )  
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RESET_PASS_TOKEN_MAX_AGE = int(os.getenv("RESET_PASS_TOKEN_MAX_AGE", "3600"))
    RESET_PASS_SALT = os.getenv("RESET_PASS_SALT", "reset-pass")

    EMAIL_VERIFICATION_SALT = os.getenv("EMAIL_VERIFICATION_SALT", "verif-salt")
    EMAIL_VERIFICATION_TOKEN_MAX_AGE = int(os.getenv("EMAIL_VERIFICATION_TOKEN_MAX_AGE", "3600"))

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = str_to_bool(os.getenv("MAIL_USE_TLS", "true"))
    MAIL_USE_SSL = str_to_bool(os.getenv("MAIL_USE_SSL", "false"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    GPTKEY= os.getenv("GPTMINIAIKEY")
