import mediapipe as mp
import cv2

# Initialize MediaPipe hands detector
# MediaPipe is Google's library for detecting hand landmarks
mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=True,   # treat each frame independently
    max_num_hands=2,           # detect up to 2 hands
    min_detection_confidence=0.5
)


def get_hand_bbox(frame):
    # Runs MediaPipe on a single frame and returns a bounding box
    # around the detected hand if one is found
    # Returns None if no hand is detected

    # MediaPipe needs RGB, OpenCV gives us BGR so we convert
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(rgb_frame)

    if not results.multi_hand_landmarks:
        return None

    # Get the frame dimensions so we can convert landmarks to pixel coordinates
    # MediaPipe returns landmarks as percentages (0 to 1) not pixels
    height, width = frame.shape[:2]

    # Get all hand landmark coordinates for the first detected hand
    landmarks = results.multi_hand_landmarks[0].landmark

    # Convert landmarks from percentages to actual pixel coordinates
    x_coords = [int(lm.x * width) for lm in landmarks]
    y_coords = [int(lm.y * height) for lm in landmarks]

    # Build a bounding box around all the hand landmarks
    x1 = min(x_coords)
    y1 = min(y_coords)
    x2 = max(x_coords)
    y2 = max(y_coords)

    return [x1, y1, x2, y2]


def boxes_overlap(bbox1, bbox2):
    # Checks if two bounding boxes overlap at all
    # Returns True if they overlap, False if they don't
    # Used to check if a hand is touching an object
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # If one box is to the left of the other they don't overlap
    if x2_1 < x1_2 or x2_2 < x1_1:
        return False

    # If one box is above the other they don't overlap
    if y2_1 < y1_2 or y2_2 < y1_1:
        return False

    return True


def detect_interactions(frames, tracked_objects):
    # Goes through every frame and checks if the person's hand
    # is overlapping with any tracked object
    # Adds interaction intervals to each object

    # person_id is always 0 since we only track one person
    PERSON_ID = 0

    # For each object store which frames had an interaction
    # { obj_id: [frame1, frame2, frame3, ...] }
    interaction_frames = {obj_id: [] for obj_id in tracked_objects}

    for frame_number, frame in frames:
        # Get the hand bounding box for this frame
        hand_bbox = get_hand_bbox(frame)

        # If no hand detected skip this frame
        if hand_bbox is None:
            continue

        # Check each tracked object
        for obj_id, obj in tracked_objects.items():
            # Check if this object appears in this frame
            if frame_number not in obj["frame_positions"]:
                continue

            obj_bbox = obj["frame_positions"][frame_number]["bbox"]

            # If hand overlaps with the object bbox record the interaction
            if boxes_overlap(hand_bbox, obj_bbox):
                interaction_frames[obj_id].append(frame_number)

    # Now compress the per-frame interactions into intervals
    # Same idea as motion_history - group consecutive frames together
    for obj_id, obj in tracked_objects.items():
        frames_with_interaction = sorted(interaction_frames[obj_id])

        if not frames_with_interaction:
            continue

        intervals = []
        start = frames_with_interaction[0]
        prev = frames_with_interaction[0]

        for i in range(1, len(frames_with_interaction)):
            curr = frames_with_interaction[i]

            # If there is a gap of more than 5 frames end the current interval
            if curr - prev > 5:
                intervals.append({
                    "interacted_by_person": PERSON_ID,
                    "frame_start": start,
                    "frame_end": prev
                })
                start = curr

            prev = curr

        # Save the last interval
        intervals.append({
            "interacted_by_person": PERSON_ID,
            "frame_start": start,
            "frame_end": prev
        })

        obj["interactions"] = intervals

    return tracked_objects
