import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app
from services.motion import classify_motion

# TestClient lets us make fake HTTP requests to our API
# without actually running the server
client = TestClient(app)


# ---- API TESTS ----

def test_upload_video_no_file():
    # Should return 422 if no file is provided
    response = client.post("/video")
    assert response.status_code == 422


def test_upload_video_with_file(tmp_path):
    # Create a tiny fake video file just for testing
    # We just need something to upload - content doesn't matter for this test
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake video content")

    with open(fake_video, "rb") as f:
        response = client.post("/video", files={"file": ("test.mp4", f, "video/mp4")})

    # Should return 200 and a task_id
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_get_task_status_not_found():
    # Should return 404 for a task ID that doesn't exist
    response = client.get("/task/fake-task-id-12345")
    assert response.status_code == 404


def test_get_task_status_valid(tmp_path):
    # Upload a video first to create a real task
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake video content")

    with open(fake_video, "rb") as f:
        upload_response = client.post("/video", files={"file": ("test.mp4", f, "video/mp4")})

    task_id = upload_response.json()["task_id"]

    # Now check the status of that task
    response = client.get(f"/task/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] in ["pending", "processing", "done", "error"]


def test_get_result_not_done(tmp_path):
    # Upload a video to create a task
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake video content")

    with open(fake_video, "rb") as f:
        upload_response = client.post("/video", files={"file": ("test.mp4", f, "video/mp4")})

    task_id = upload_response.json()["task_id"]

    # Result should not be available yet since task is still pending
    response = client.get(f"/result/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is None


def test_get_result_not_found():
    # Should return 404 for a task ID that doesn't exist
    response = client.get("/result/fake-task-id-12345")
    assert response.status_code == 404


# ---- MOTION CLASSIFIER TESTS ----

def test_classify_motion_moving():
    # Object that moves a lot should be classified as moving
    # We simulate an object moving 50 pixels per frame
    tracked_objects = {
        1: {
            "object_id": 1,
            "class": "cup",
            "motion_history": [],
            "interactions": [],
            "frame_positions": {
                0: {"bbox": [0, 0, 50, 50], "centroid": (25, 25)},
                1: {"bbox": [50, 50, 100, 100], "centroid": (75, 75)},
                2: {"bbox": [100, 100, 150, 150], "centroid": (125, 125)},
            }
        }
    }

    result = classify_motion(tracked_objects)
    motion_history = result[1]["motion_history"]

    # Should have at least one moving interval
    states = [interval["state"] for interval in motion_history]
    assert "moving" in states


def test_classify_motion_stationary():
    # Object that barely moves should be classified as stationary
    # We simulate an object moving only 1 pixel per frame
    tracked_objects = {
        1: {
            "object_id": 1,
            "class": "bottle",
            "motion_history": [],
            "interactions": [],
            "frame_positions": {
                0: {"bbox": [0, 0, 50, 50], "centroid": (25, 25)},
                1: {"bbox": [1, 0, 51, 50], "centroid": (26, 25)},
                2: {"bbox": [1, 1, 51, 51], "centroid": (26, 26)},
            }
        }
    }

    result = classify_motion(tracked_objects)
    motion_history = result[1]["motion_history"]

    # Should have at least one stationary interval
    states = [interval["state"] for interval in motion_history]
    assert "stationary" in states


def test_classify_motion_not_enough_frames():
    # Object with only one frame should not crash
    # and should have empty motion history
    tracked_objects = {
        1: {
            "object_id": 1,
            "class": "cup",
            "motion_history": [],
            "interactions": [],
            "frame_positions": {
                0: {"bbox": [0, 0, 50, 50], "centroid": (25, 25)},
            }
        }
    }

    result = classify_motion(tracked_objects)
    assert result[1]["motion_history"] == []
