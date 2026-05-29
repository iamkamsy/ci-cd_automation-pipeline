import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from db import init_db

load_dotenv()

app = Flask(__name__)
_is_testing = os.environ.get("TESTING", "").lower() == "true"
_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    if _is_testing:
        _secret_key = "dev-secret-key-for-testing"
    else:
        raise RuntimeError("SECRET_KEY environment variable is required")
app.secret_key = _secret_key

_cookie_secure = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=_cookie_secure,
)

CORS(app, supports_credentials=True, origins=_cors_origins)

if not _is_testing:
    init_db(app)

app.register_blueprint(auth_bp)
app.register_blueprint(tasks_bp)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true", port=5000)
