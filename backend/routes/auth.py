from flask import Blueprint, request, jsonify, session
import bcrypt
from pymongo.errors import DuplicateKeyError
from db import get_db
from models.user import make_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "All fields are required."}), 400
    if len(username) > 50:
        return jsonify({"error": "Username must be 50 characters or fewer."}), 400
    if len(email) > 254:
        return jsonify({"error": "Email address is too long."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if len(password) > 128:
        return jsonify({"error": "Password must be 128 characters or fewer."}), 400

    db = get_db()
    if db.users.find_one({"email": email}):
        return jsonify({"error": "An account with that email already exists."}), 409
    if db.users.find_one({"username": username}):
        return jsonify({"error": "That username is already taken."}), 409

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        result = db.users.insert_one(make_user(username, email, password_hash))
    except DuplicateKeyError:
        return jsonify({"error": "An account with that email or username already exists."}), 409

    session["user_id"] = str(result.inserted_id)
    session["username"] = username
    return jsonify({"username": username}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    db = get_db()
    user = db.users.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = str(user["_id"])
    session["username"] = user["username"]
    return jsonify({"username": user["username"]}), 200


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out."}), 200


@auth_bp.get("/me")
def me():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"user_id": session["user_id"], "username": session["username"]}), 200
