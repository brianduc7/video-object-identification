def calculate_iou(bbox1, bbox2):
    # Calculates how much two bounding boxes overlap
    # Returns a number between 0 and 1
    # 0 = no overlap, 1 = identical boxes
    # We use this to decide if two detections in different frames are the same object
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # Find the overlapping rectangle
    inter_x1 = max(x1_1, x1_2)
    inter_y1 = max(y1_1, y1_2)
    inter_x2 = min(x2_1, x2_2)
    inter_y2 = min(y2_1, y2_2)

    # Calculate area of the overlap
    inter_width = max(0, inter_x2 - inter_x1)
    inter_height = max(0, inter_y2 - inter_y1)
    intersection_area = inter_width * inter_height

    # Calculate area of each box
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    # Union = total area covered by both boxes minus the overlap
    union_area = area1 + area2 - intersection_area

    if union_area == 0:
        return 0.0

    return intersection_area / union_area


def get_centroid(bbox):
    # Returns the center point of a bounding box
    # Used to track where an object is positioned over time
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    return (cx, cy)


def track_objects(all_detections):
    # Takes raw per-frame detections and assigns each unique object
    # a consistent ID across all frames
    # Returns a dict where key is object_id and value is all object data

    # Stores all confirmed objects we are tracking
    tracked_objects = {}

    # Counter - each new object gets the next number
    next_id = 1

    # Stores the most recent bbox for each tracked object
    # so we can compare it against detections in the next frame
    active_tracks = {}

    for frame_data in all_detections:
        frame_number = frame_data["frame_number"]
        detections = frame_data["detections"]

        # Track which detections got matched to existing objects
        matched_detection_indices = set()

        # Try to match each active track to a detection in this frame
        for obj_id, track in active_tracks.items():
            best_iou = 0
            best_match_index = None

            for i, detection in enumerate(detections):
                # Only match objects of the same class
                # a cup cannot become a bottle between frames
                if detection["class"] != track["class"]:
                    continue

                iou = calculate_iou(track["bbox"], detection["bbox"])

                if iou > best_iou:
                    best_iou = iou
                    best_match_index = i

            # If best match has IoU above 0.3 it is the same object
            if best_iou > 0.3 and best_match_index is not None:
                matched_detection_indices.add(best_match_index)

                # Update track with new position
                matched_bbox = detections[best_match_index]["bbox"]
                active_tracks[obj_id]["bbox"] = matched_bbox

                # Save this frame position in the object history
                tracked_objects[obj_id]["frame_positions"][frame_number] = {
                    "bbox": matched_bbox,
                    "centroid": get_centroid(matched_bbox)
                }

        # Any unmatched detection is a new object
        for i, detection in enumerate(detections):
            if i not in matched_detection_indices:
                # Skip people - handled separately in interaction.py
                if detection["class"] == "person":
                    continue

                # Assign new unique ID
                obj_id = next_id
                next_id += 1

                tracked_objects[obj_id] = {
                    "object_id": obj_id,
                    "class": detection["class"],
                    "motion_history": [],
                    "interactions": [],
                    "frame_positions": {
                        frame_number: {
                            "bbox": detection["bbox"],
                            "centroid": get_centroid(detection["bbox"])
                        }
                    }
                }

                active_tracks[obj_id] = {
                    "bbox": detection["bbox"],
                    "class": detection["class"]
                }

    return tracked_objects
