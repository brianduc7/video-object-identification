import cv2
import os


def extract_keyframes(task_id, frames, tracked_objects):
    # Saves screenshot images at important moments in the video
    # Two types of keyframes we save:
    # 1. When an object transitions from stationary to moving
    # 2. When an interaction starts

    # Create a folder for this task's keyframes
    keyframe_dir = os.path.join("keyframes", task_id)
    os.makedirs(keyframe_dir, exist_ok=True)

    # Build a lookup so we can quickly get a frame by its number
    # Instead of looping through all frames every time
    frame_lookup = {frame_number: frame for frame_number, frame in frames}

    for obj_id, obj in tracked_objects.items():

        # Type 1 - save frame when object goes from stationary to moving
        motion_history = obj.get("motion_history", [])

        for i in range(1, len(motion_history)):
            prev_state = motion_history[i - 1]["state"]
            curr_state = motion_history[i]["state"]

            # Check if state changed from stationary to moving
            if prev_state == "stationary" and curr_state == "moving":
                # The transition frame is the start of the moving interval
                transition_frame = motion_history[i]["frame_range"][0]

                if transition_frame in frame_lookup:
                    frame = frame_lookup[transition_frame]
                    filename = f"obj{obj_id}_motion_frame{transition_frame}.jpg"
                    filepath = os.path.join(keyframe_dir, filename)
                    cv2.imwrite(filepath, frame)

        # Type 2 - save frame when an interaction starts
        interactions = obj.get("interactions", [])

        for interaction in interactions:
            interaction_start = interaction["frame_start"]

            if interaction_start in frame_lookup:
                frame = frame_lookup[interaction_start]
                filename = f"obj{obj_id}_interaction_frame{interaction_start}.jpg"
                filepath = os.path.join(keyframe_dir, filename)
                cv2.imwrite(filepath, frame)
