from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import os
import threading
from datetime import datetime
from db.database import get_connection
from services.video_processor import process_video

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (id, status, created_at) VALUES (?, ?, ?)",
        (task_id, "pending", datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    thread = threading.Thread(target=process_video, args=(task_id, video_path))
    thread.start()
    return {"task_id": task_id, "status": "pending"}

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": row[0]}

@router.get("/result/{task_id}")
def get_result(task_id: str):
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    if task[0] != "done":
        conn.close()
        return {"task_id": task_id, "status": task[0], "result": None}
    cursor.execute("SELECT result_json FROM results WHERE task_id = ?", (task_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"task_id": task_id, "status": "done", "result": json.loads(result[0])}