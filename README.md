# Video Object Identification

A service that analyzes a video and identifies the objects a person is interacting with.

## What it does
1. Detects objects in each frame using YOLOv8
2. Tracks each object across frames with a consistent ID
3. Classifies each object as moving or stationary
4. Detects when a person's hand interacts with an object
5. Returns structured JSON output describing everything found
6. Saves keyframe screenshots at key moments (bonus)

## Tech stack
- FastAPI - REST API framework
- OpenCV - video processing and frame extraction
- YOLOv8 (Ultralytics) - object detection
- MediaPipe - hand detection and tracking
- SQLite - task and result persistence
- pytest - testing

## Setup instructions

1. Clone the repo
git clone https://github.com/brianduc7/video-object-identification.git
cd video-object-identification

2. Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate

3. Install dependencies
pip install -r requirements.txt
pip install pytest httpx

4. Run the server
python -m uvicorn main:app --reload

5. Open the app
Visit http://127.0.0.1:8000/static/index.html
Visit http://127.0.0.1:8000/docs for Swagger UI

## API endpoints
POST   /video              Upload a video file, returns task_id
GET    /task/{task_id}     Check processing status
GET    /result/{task_id}   Get the full JSON result

## Running tests
python -m pytest tests/test_api.py -v

## Assumptions and tradeoffs
- Processing runs in a background thread not a proper job queue
- YOLO runs on CPU by default, slower without a GPU
- IoU-based tracking can lose object IDs through occlusion
- Only the first detected hand is used for interaction detection
- YOLO confidence threshold is 0.3, adjustable in services/detector.py

## Time spent
Approximately 8 hours.
