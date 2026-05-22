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

## Repository Tree

video-object-identification/
├── main.py                    # starts the FastAPI app
├── requirements.txt
├── yolov8s.pt                 # YOLOv8 weights (downloaded on first run)
├── database.db                # SQLite db (created on first run)
├── api/
│   └── routes.py              # API endpoints
├── db/
│   └── database.py            # db connection and queries
├── models/
│   └── schemas.py             # request/response models
├── services/
│   ├── video_processor.py     # ties the pipeline together
│   ├── detector.py            # runs YOLO on each frame
│   ├── tracker.py             # tracks objects across frames
│   ├── motion.py              # stationary vs moving classification
│   ├── interaction.py         # detects person-object interaction
│   └── keyframe.py            # saves keyframe images
├── static/
│   └── index.html             # upload page
├── tests/
│   └── test_api.py
├── uploads/                   # uploaded videos (created on first run)
└── keyframes/                 # keyframes per task (created on first run)
    └── {task_id}/
        └── obj{n}_motion_frame{f}.jpg

## Seed Data

A sample video is included in `seed_data/` for testing. To use it:

1. Start the server
2. Open http://127.0.0.1:8000/static/index.html
3. Upload `seed_data/Sample Installation Video.mp4`
4. Copy the returned `task_id` and poll `GET /task/{task_id}` until status is `done`
5. Fetch results at `GET /result/{task_id}`

## API

POST /video — upload a video file, returns a task_id immediately
GET /task/{task_id} — check if processing is pending, processing, done, or error
GET /result/{task_id} — get the full JSON output once done

## Libraries

Python: primary language
FastAPI: chosen for async support, Swagger UI comes free
OpenCV: handles video reading and frame extraction
YOLOv8 (Ultralytics): solid pre-trained detection model that runs fine on CPU
MediaPipe: used for hand landmark detection, currently disabled due to compatibility issues
SQLite: no setup needed, good enough for tracking task state and storing results

## Running tests

    python -m pytest tests/test_api.py -v

## Test Results

$ python -m pytest tests/test_api.py -v

platform win32 -- Python 3.11.9, pytest-9.0.3
collected 9 items

tests/test_api.py::test_upload_video_no_file PASSED
tests/test_api.py::test_upload_video_with_file PASSED
tests/test_api.py::test_get_task_status_not_found PASSED
tests/test_api.py::test_get_task_status_valid PASSED
tests/test_api.py::test_get_result_not_done PASSED
tests/test_api.py::test_get_result_not_found PASSED
tests/test_api.py::test_classify_motion_moving PASSED
tests/test_api.py::test_classify_motion_stationary PASSED
tests/test_api.py::test_classify_motion_not_enough_frames PASSED

9 passed in 0.68s

## Tradeoffs

Processing runs in a background thread rather than a proper job queue like Celery. YOLO runs on CPU so processing is slower without a GPU. The IoU-based tracker can lose object IDs through occlusion. MediaPipe hand detection is disabled by default due to compatibility issues with the installed version interaction, detection defaults to empty.

## Assumptions

- Only one person appears in frame at a time; multi-person tracking was not required
- Every frame is processed with no sampling; processing time scales with video length
- Interaction is defined as bounding box overlap between a detected hand and a tracked object
- A gap of more than 5 frames between overlaps is treated as two separate interaction intervals
- Objects that disappear and reappear mid-video may be assigned a new tracking ID rather than recovering the original
- Videos are assumed to contain a single continuous activity with no scene cuts

## Time spent

Around 10 hours.