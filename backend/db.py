from pymongo import MongoClient, ASCENDING
import os

_client: MongoClient | None = None


def init_db(app):
    """Create the MongoClient once at app startup and stash it on app.extensions."""
    global _client
    tls_insecure = os.environ.get("TLS_INSECURE", "false").lower() == "true"
    _client = MongoClient(
        os.environ["MONGO_URI"],
        tlsInsecure=tls_insecure,
    )
    db = _client[os.environ.get("DB_NAME", "taskmanager")]
    app.extensions["mongo_db"] = db
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("username", ASCENDING)], unique=True)


def get_db():
    return _client[os.environ.get("DB_NAME", "taskmanager")]
