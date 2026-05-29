import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from db import init_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

_cookie_secure = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=_cookie_secure,
)

CORS(app, supports_credentials=True, origins=_cors_origins)

init_db(app)

app.register_blueprint(auth_bp)
app.register_blueprint(tasks_bp)

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true", port=5000)
