import math
import time


class ActivityDetector:
    """
    Determines the basic activity of a tracked object inside or outside restricted area.
    """

    def __init__(
        self,
        moving_threshold=20,
        fast_moving_threshold=150,
    ):
        self.moving_threshold = moving_threshold
        self.fast_moving_threshold = fast_moving_threshold
        self.previous_positions = {}
        self.inside_tracks = set()

    def update(
        self,
        track_id,
        center_x,
        center_y,
        inside_restricted_area,
    ):
        current_time = time.time()

        # First time this object enters the restricted area
        if inside_restricted_area and track_id not in self.inside_tracks:
            self.inside_tracks.add(track_id)
            self.previous_positions[track_id] = (center_x, center_y, current_time)
            return "entering_restricted_area", 0.0

        # Outside the restricted area
        if not inside_restricted_area:
            self.previous_positions[track_id] = (center_x, center_y, current_time)
            return "outside_restricted_area", 0.0

        # Inside the restricted area
        if track_id in self.previous_positions:
            prev_x, prev_y, prev_time = self.previous_positions[track_id]
            dt = current_time - prev_time
            distance = math.sqrt((center_x - prev_x) ** 2 + (center_y - prev_y) ** 2)
            speed = (distance / dt) if dt > 0 else 0.0
        else:
            speed = 0.0

        self.previous_positions[track_id] = (center_x, center_y, current_time)

        if speed > self.fast_moving_threshold:
            activity = "moving_fast_inside_restricted_area"
        elif speed > self.moving_threshold:
            activity = "moving_inside_restricted_area"
        else:
            activity = "stationary_inside_restricted_area"

        return activity, speed

    def remove_track(self, track_id):
        """Remove tracking state for track_id."""
        self.previous_positions.pop(track_id, None)
        self.inside_tracks.discard(track_id)
