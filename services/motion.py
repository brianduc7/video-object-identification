def classify_motion(tracked_objects):
    # Takes tracked objects and adds motion_history to each one
    # motion_history is a list of intervals showing when the object
    # was moving vs stationary throughout the video
    # Example:
    # [
    #   { "frame_range": [0, 90], "state": "moving" },
    #   { "frame_range": [91, 222], "state": "stationary" }
    # ]

    # How many pixels the centroid must move to be considered moving
    MOVEMENT_THRESHOLD = 5

    for obj_id, obj in tracked_objects.items():
        frame_positions = obj["frame_positions"]

        # Need at least 2 frames to compare movement
        if len(frame_positions) < 2:
            continue

        # Get frame numbers in order
        frame_numbers = sorted(frame_positions.keys())

        # Build a list of states per frame by comparing centroid positions
        # Example: [("moving", 0), ("moving", 1), ("stationary", 2)]
        frame_states = []

        for i in range(1, len(frame_numbers)):
            prev_frame = frame_numbers[i - 1]
            curr_frame = frame_numbers[i]

            prev_centroid = frame_positions[prev_frame]["centroid"]
            curr_centroid = frame_positions[curr_frame]["centroid"]

            # Calculate how far the centroid moved between frames
            # This is just the straight line distance between two points
            dx = curr_centroid[0] - prev_centroid[0]
            dy = curr_centroid[1] - prev_centroid[1]
            distance = (dx**2 + dy**2) ** 0.5

            # If distance is above threshold the object is moving
            if distance > MOVEMENT_THRESHOLD:
                frame_states.append((curr_frame, "moving"))
            else:
                frame_states.append((curr_frame, "stationary"))

        # Now compress the per-frame states into intervals
        # Instead of one entry per frame we group consecutive same states together
        # Example: frames 0-90 all moving becomes one entry { "frame_range": [0, 90], "state": "moving" }
        if not frame_states:
            continue

        motion_history = []
        interval_start = frame_states[0][0]
        current_state = frame_states[0][1]

        for i in range(1, len(frame_states)):
            frame_num, state = frame_states[i]

            if state != current_state:
                # State changed - save the completed interval
                motion_history.append({
                    "frame_range": [interval_start, frame_states[i - 1][0]],
                    "state": current_state
                })
                # Start a new interval
                interval_start = frame_num
                current_state = state

        # Save the last interval
        motion_history.append({
            "frame_range": [interval_start, frame_states[-1][0]],
            "state": current_state
        })

        obj["motion_history"] = motion_history

    return tracked_objects
