from flask import Blueprint, request, jsonify, session
from bson import ObjectId
from db import get_db
from models.task import make_task
import re
from datetime import date

_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
MAX_NAME_LEN = 200
MAX_DESC_LEN = 2000


def _validate_fields(name: str, deadline: str, description: str):
    """Return an error string or None if all fields are valid."""
    if not name:
        return "Task name is required."
    if len(name) > MAX_NAME_LEN:
        return f"Task name must be {MAX_NAME_LEN} characters or fewer."
    if not deadline:
        return "Deadline is required."
    if not _DATE_RE.match(deadline):
        return "Deadline must be a valid date in YYYY-MM-DD format."
    try:
        parsed = date.fromisoformat(deadline)
    except ValueError:
        return "Deadline must be a valid date in YYYY-MM-DD format."
    if parsed < date.today():
        return "Deadline cannot be in the past."
    if not description:
        return "Description is required."
    if len(description) > MAX_DESC_LEN:
        return f"Description must be {MAX_DESC_LEN} characters or fewer."
    return None

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def _require_auth():
    """Return (user_id_str, None) or (None, error_response)."""
    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"error": "Not authenticated."}), 401)
    return user_id, None


def _serialize(task: dict) -> dict:
    return {
        "id": str(task["_id"]),
        "name": task["name"],
        "deadline": task["deadline"],
        "description": task["description"],
    }


@tasks_bp.get("")
def list_tasks():
    user_id, err = _require_auth()
    if err:
        return err

    db = get_db()
    tasks = list(
        db.tasks.find({"user_id": ObjectId(user_id)}).sort("deadline", 1)
    )
    return jsonify([_serialize(t) for t in tasks]), 200


@tasks_bp.post("")
def create_task():
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    deadline = (data.get("deadline") or "").strip()
    description = (data.get("description") or "").strip()

    err_msg = _validate_fields(name, deadline, description)
    if err_msg:
        return jsonify({"error": err_msg}), 400

    db = get_db()
    result = db.tasks.insert_one(make_task(user_id, name, deadline, description))
    task = db.tasks.find_one({"_id": result.inserted_id})
    return jsonify(_serialize(task)), 201


@tasks_bp.put("/<task_id>")
def update_task(task_id: str):
    user_id, err = _require_auth()
    if err:
        return err

    try:
        oid = ObjectId(task_id)
    except Exception:
        return jsonify({"error": "Invalid task ID."}), 400

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    deadline = (data.get("deadline") or "").strip()
    description = (data.get("description") or "").strip()

    err_msg = _validate_fields(name, deadline, description)
    if err_msg:
        return jsonify({"error": err_msg}), 400

    db = get_db()
    result = db.tasks.find_one_and_update(
        {"_id": oid, "user_id": ObjectId(user_id)},
        {"$set": {"name": name, "deadline": deadline, "description": description}},
        return_document=True,
    )
    if result is None:
        return jsonify({"error": "Task not found."}), 404
    return jsonify(_serialize(result)), 200


@tasks_bp.delete("/<task_id>")
def delete_task(task_id: str):
    user_id, err = _require_auth()
    if err:
        return err

    try:
        oid = ObjectId(task_id)
    except Exception:
        return jsonify({"error": "Invalid task ID."}), 400

    db = get_db()
    result = db.tasks.delete_one({"_id": oid, "user_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"message": "Deleted."}), 200
