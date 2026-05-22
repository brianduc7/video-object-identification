import cv2

try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    hands_detector = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.5
    )
    MEDIAPIPE_AVAILABLE = True
except Exception:
    MEDIAPIPE_AVAILABLE = False


def get_hand_bbox(frame):
    # Returns bounding box around detected hand, or None if not found
    if not MEDIAPIPE_AVAILABLE:
        return None

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(rgb_frame)

    if not results.multi_hand_landmarks:
        return None

    height, width = frame.shape[:2]
    landmarks = results.multi_hand_landmarks[0].landmark

    x_coords = [int(lm.x * width) for lm in landmarks]
    y_coords = [int(lm.y * height) for lm in landmarks]

    return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]


def boxes_overlap(bbox1, bbox2):
    # Returns True if two bounding boxes overlap
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    if x2_1 < x1_2 or x2_2 < x1_1:
        return False
    if y2_1 < y1_2 or y2_2 < y1_1:
        return False
    return True


def detect_interactions(frames, tracked_objects):
    # Detects hand-object interactions for each frame
    PERSON_ID = 0
    interaction_frames = {obj_id: [] for obj_id in tracked_objects}

    for frame_number, frame in frames:
        hand_bbox = get_hand_bbox(frame)
        if hand_bbox is None:
            continue

        for obj_id, obj in tracked_objects.items():
            if frame_number not in obj["frame_positions"]:
                continue
            obj_bbox = obj["frame_positions"][frame_number]["bbox"]
            if boxes_overlap(hand_bbox, obj_bbox):
                interaction_frames[obj_id].append(frame_number)

    for obj_id, obj in tracked_objects.items():
        frames_with_interaction = sorted(interaction_frames[obj_id])
        if not frames_with_interaction:
            continue

        intervals = []
        start = frames_with_interaction[0]
        prev = frames_with_interaction[0]

        for i in range(1, len(frames_with_interaction)):
            curr = frames_with_interaction[i]
            if curr - prev > 5:
                intervals.append({
                    "interacted_by_person": PERSON_ID,
                    "frame_start": start,
                    "frame_end": prev
                })
                start = curr
            prev = curr

        intervals.append({
            "interacted_by_person": PERSON_ID,
            "frame_start": start,
            "frame_end": prev
        })

        obj["interactions"] = intervals

    return tracked_objects
