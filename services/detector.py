from ultralytics import YOLO
import numpy as np

# Load the YOLOv8 model once when this file is imported
# "yolov8n.pt" is the smallest and fastest version — good for development
# It will automatically download the model weights the first time you run it
model = YOLO("yolov8s.pt")


def detect_objects(frames):
    """
    Runs YOLO object detection on every frame.
    Returns a list of detections, one entry per frame.

    Each entry looks like:
    {
        "frame_number": 42,
        "detections": [
            {
                "class": "cup",
                "confidence": 0.91,
                "bbox": [x1, y1, x2, y2]
            },
            ...
        ]
    }

    bbox is the bounding box — the four coordinates of the rectangle
    drawn around the detected object:
    x1, y1 = top left corner
    x2, y2 = bottom right corner
    """
    all_detections = []

    for frame_number, frame in frames:
        # Run YOLO on this single frame
        # verbose=False silences the per-frame console output
        results = model(frame, verbose=False)

        # results[0] contains all detections for this frame
        frame_detections = []

        for box in results[0].boxes:
            # box.xyxy gives the bounding box coordinates as a tensor
            # .cpu().numpy() converts it to a regular numpy array
            # [0] gets the first (and only) row
            bbox = box.xyxy.cpu().numpy()[0]

            # box.cls gives the class index (e.g. 39)
            # model.names maps that index to a label (e.g. "bottle")
            class_index = int(box.cls.cpu().numpy()[0])
            class_name = model.names[class_index]

            # box.conf gives the confidence score — how sure YOLO is
            # e.g. 0.91 means 91% confident this is a bottle
            confidence = float(box.conf.cpu().numpy()[0])

            # Skip detections YOLO isn't very confident about
            if confidence < 0.3:
                continue

            frame_detections.append({
                "class": class_name,
                "confidence": round(confidence, 2),
                "bbox": [
                    int(bbox[0]),  # x1
                    int(bbox[1]),  # y1
                    int(bbox[2]),  # x2
                    int(bbox[3])   # y2
                ]
            })

        all_detections.append({
            "frame_number": frame_number,
            "detections": frame_detections
        })

    return all_detections