from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import os
from datetime import datetime
from db.database import get_connection

# Defines routes in a separate file
# main.py will attach this router into the main app
router = APIRouter()

# Uploaded videos 
# exist_ok=True means don't crash in case folder already exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Upload video
@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    # Generate unique ID for task
    task_id = str(uuid.uuid4())

    #Builds path
    video_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")

    # Read the file contents and save it to disk
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)    

    # Open a connection to the database
    conn = get_connection()
    cursor = conn.cursor()

    # Insert a new row into the tasks table
    cursor.execute(
        "INSERT INTO tasks (id, status, created_at) VALUES (?, ?, ?)",
        (task_id, "pending", datetime.utcnow().isoformat())
    )

    # Save and close the database connection
    conn.commit()
    conn.close()

    # Return the task ID immediately
    # The video is still processing in the background
    return {"task_id": task_id, "status": "pending"}

# Get task info
@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    # Open a connection to the database
    conn = get_connection()
    cursor = conn.cursor()

    # Look up task using ID
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))

    # Looks for first matching row
    # If nothing is found it returns None
    row = cursor.fetchone()

    conn.close()

    # If no task was found with that ID, return a 404 error
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # row is a tuple like ("pending",) so row[0] gets the actual status value
    return {"task_id": task_id, "status": row[0]}

# Get task results
@router.get("/result/{task_id}")
def get_result(task_id: str):
    import json

    # Open a connection to the database
    conn = get_connection()
    cursor = conn.cursor()

    # First check if the task exists at all
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    # If no task return a 404
    if not task:
        conn.close()
        raise HTTPException (status_code=404)
    
    # If the task exists but isn't done yet, tell the user to wait
    # We check task[0] because fetchone() returns a tuple like ("processing",)
    if task[0] != "done":
        conn.close()
        return {"task_id": task_id, "status": task[0], "result": None}
    
    # fetch result from table
    cursor.execute("SELECT result_json FROM results WHERE task_id = ?", (task_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # result[0] is a JSON string stored in the database
    # json.loads() converts it back into a Python dict
    return {"task_id": task_id, "status": "done", "result": json.loads(result[0])}