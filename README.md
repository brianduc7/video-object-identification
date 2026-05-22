# Video Object Identification

This service takes a video file and figures out what objects are in it, whether they're moving or sitting still, and whether a person interacts with them. You upload a video, get a task ID back, and poll for results while it processes in the background.

## How to run it

Clone the repo and set up a virtual environment:

    git clone https://github.com/brianduc7/video-object-identification.git
    cd video-object-identification
    python -m venv venv
    source venv/Scripts/activate

Install dependencies:

    pip install -r requirements.txt
    pip install pytest httpx

Start the server:

    python -m uvicorn main:app

Then open http://127.0.0.1:8000/docs to use the Swagger UI, or http://127.0.0.1:8000/static/index.html for the upload page.

## API

POST /video — upload a video file, returns a task_id immediately
GET /task/{task_id} — check if processing is pending, processing, done, or error
GET /result/{task_id} — get the full JSON output once done

## Running tests

    python -m pytest tests/test_api.py -v

## Stack

Python, FastAPI, OpenCV, YOLOv8 (Ultralytics), MediaPipe, SQLite

## Tradeoffs

Processing runs in a background thread rather than a proper job queue like Celery. YOLO runs on CPU so processing is slower without a GPU. The IoU-based tracker can lose object IDs through occlusion. MediaPipe hand detection is disabled by default due to compatibility issues with the installed version — interaction detection defaults to empty.

## Time spent

Around 8 hours.