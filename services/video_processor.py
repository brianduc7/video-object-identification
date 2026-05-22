import cv2
import json
from db.database import get_connection


def get_video_metadata(video_path):
    # Open the video file with OpenCV
    cap = cv2.VideoCapture(video_path)

    # Total number of frames in the video
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Frames per second
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Width and height of each frame in pixels
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Duration = total frames divided by frames per second
    duration = round(frame_count / fps, 2) if fps > 0 else 0

    cap.release()

    return {
        "duration_seconds": duration,
        "frame_count": frame_count,
        "fps": round(fps, 2),
        "resolution": f"{width}x{height}"
    }


def extract_frames(video_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_number = 0

    while True:
        # ret is True if frame read successfully, False if video ended
        ret, frame = cap.read()

        if not ret:
            break

        frames.append((frame_number, frame))
        frame_number += 1

    cap.release()
    return frames


def update_task_status(task_id, status):
    # Updates the status of a task in the database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )
    conn.commit()
    conn.close()


def save_result(task_id, result):
    # Saves the final JSON result to the results table
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO results (task_id, result_json) VALUES (?, ?)",
        (task_id, json.dumps(result))
    )
    conn.commit()
    conn.close()


def process_video(task_id, video_path):
    # Main pipeline - called in background thread when video is uploaded
    try:
        update_task_status(task_id, "processing")

        # Step 1 - get video metadata
        video_metadata = get_video_metadata(video_path)

        # Step 2 - extract all frames
        frames = extract_frames(video_path)

        # Step 3 - detect objects in each frame
        from services.detector import detect_objects
        detections = detect_objects(frames)

        # Step 4 - track objects across frames with consistent IDs
        from services.tracker import track_objects
        tracked_objects = track_objects(detections)

        # Step 5 - classify each object as moving or stationary
        from services.motion import classify_motion
        tracked_objects = classify_motion(tracked_objects)

        # Step 6 - detect person and hand interactions with objects
        # from services.interaction import detect_interactions
        # tracked_objects = detect_interactions(frames, tracked_objects)

        # Step 7 - save keyframe screenshots
        from services.keyframe import extract_keyframes
        extract_keyframes(task_id, frames, tracked_objects)

        # Step 8 - build final JSON output
        result = {
            "videoMetadata": video_metadata,
            "objectsDetected": list(tracked_objects.values())
        }

        # Step 9 - build the final output
        # Remove frame_positions since it's internal data, not part of the spec
        objects_output = []
        for obj in tracked_objects.values():
            objects_output.append({
                "object_id": obj["object_id"],
                "class": obj["class"],
                "motion_history": obj["motion_history"],
                "interactions": obj["interactions"]
            })

        result = {
            "videoMetadata": video_metadata,
            "objectsDetected": objects_output
        }

        # Step 10 - save result and mark task as done
        save_result(task_id, result)
        update_task_status(task_id, "done")

    except Exception as e:
        print(f"Error processing video {task_id}: {e}")
        update_task_status(task_id, "error")