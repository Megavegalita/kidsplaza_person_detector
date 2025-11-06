#!/usr/bin/env python3
"""
Zone-based person counter module.

This module provides functionality to count people entering and exiting
defined zones (polygon or line-based).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def point_in_polygon(
    point: Tuple[float, float], polygon: List[Tuple[float, float]]
) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm.

    Args:
        point: (x, y) coordinates of the point
        polygon: List of (x, y) coordinates defining polygon vertices

    Returns:
        True if point is inside polygon, False otherwise
    """
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def line_crossing(
    prev_point: Tuple[float, float],
    curr_point: Tuple[float, float],
    line_start: Tuple[float, float],
    line_end: Tuple[float, float],
    side: str = "above",
) -> bool:
    """
    Check if a point crosses a line from a specific side.

    Args:
        prev_point: Previous point (x, y)
        curr_point: Current point (x, y)
        line_start: Line start point (x, y)
        line_end: Line end point (x, y)
        side: Which side to check ('above', 'below', 'left', 'right')

    Returns:
        True if line was crossed, False otherwise
    """
    # Convert to numpy for easier computation
    prev = np.array(prev_point)
    curr = np.array(curr_point)
    line_s = np.array(line_start)
    line_e = np.array(line_end)

    # Vector from line start to end
    line_vec = line_e - line_s

    # Vector from line start to previous and current points
    prev_vec = prev - line_s
    curr_vec = curr - line_s

    # Cross product to determine side
    prev_cross = np.cross(line_vec, prev_vec)
    curr_cross = np.cross(line_vec, curr_vec)

    # Check if crossing occurred (sign change)
    if prev_cross * curr_cross >= 0:
        return False  # Same side, no crossing

    # Determine which side we're checking
    if side == "above":
        # Above means positive cross product (assuming y increases downward)
        return prev_cross < 0 and curr_cross > 0
    elif side == "below":
        return prev_cross > 0 and curr_cross < 0
    elif side == "left":
        # Left means negative cross product
        return prev_cross > 0 and curr_cross < 0
    elif side == "right":
        return prev_cross < 0 and curr_cross > 0

    return False


class ZoneCounter:
    """
    Zone-based person counter.

    Tracks people entering and exiting defined zones (polygon or line-based)
    and maintains counts per zone.

    Supports both absolute coordinates and percentage-based coordinates:
    - Absolute: Fixed pixel coordinates (e.g., [[0, 0], [960, 0], [960, 1080], [0, 1080]])
    - Percentage: Relative to frame size (e.g., [[0, 0], [50, 0], [50, 100], [0, 100]])
      Use "coordinate_type": "percentage" for dynamic zones that adapt to any resolution.

    Examples:
        # Absolute coordinates (for specific resolution)
        zone_abs = {
            "zone_id": "zone_1",
            "name": "Left Half",
            "type": "polygon",
            "coordinate_type": "absolute",  # or omit for default
            "points": [[0, 0], [960, 0], [960, 1080], [0, 1080]]
        }

        # Percentage coordinates (adapts to any resolution)
        zone_percent = {
            "zone_id": "zone_1",
            "name": "Left Half",
            "type": "polygon",
            "coordinate_type": "percentage",
            "points": [[0, 0], [50, 0], [50, 100], [0, 100]]  # 50% = left half
        }

        counter = ZoneCounter([zone_percent])
    """

    def __init__(self, zones: List[Dict[str, Any]]) -> None:
        """
        Initialize zone counter.

        Args:
            zones: List of zone configuration dictionaries
                Supports both absolute coordinates and percentage-based coordinates
                Use "coordinate_type": "percentage" for percentage-based zones

        Raises:
            ValueError: If zone configuration is invalid
        """
        self.zones = self._validate_and_parse_zones(zones)
        self.zone_counts: Dict[str, Dict[str, int]] = {}
        self.track_positions: Dict[int, Dict[str, Tuple[float, float]]] = {}
        self.track_zone_state: Dict[int, Dict[str, bool]] = {}
        self.track_zone_frame_count: Dict[
            int, Dict[str, int]
        ] = {}  # Flickering protection
        self.track_zone_counted: Dict[
            int, Dict[str, str]
        ] = {}  # Track last counted event: "enter" or "exit" or None
        self.disappeared_tracks: Dict[
            int, Dict[str, Any]
        ] = {}  # Track disappeared tracks for position matching
        self._frame_size: Optional[Tuple[int, int]] = None  # (width, height)
        self._position_match_threshold: float = (
            100.0  # Pixels - max distance to match tracks
        )

        # Initialize counts for each zone
        for zone in self.zones:
            zone_id = zone["zone_id"]
            self.zone_counts[zone_id] = {
                "enter": 0,
                "exit": 0,
                "total": 0,
                "current": 0,  # Current count of tracks in zone
            }
            logger.info(f"Initialized zone: {zone_id} ({zone['name']})")

        logger.info(f"ZoneCounter initialized with {len(self.zones)} zones")

    def _validate_and_parse_zones(
        self, zones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate and parse zone configurations.

        Supports both absolute and percentage coordinates:
        - Absolute: Use pixel coordinates directly (default if coordinate_type omitted)
        - Percentage: Use 0-100 values that scale with frame resolution

        Args:
            zones: List of zone configuration dictionaries.
                Required fields: zone_id, name, type
                Optional: coordinate_type ("absolute" or "percentage", default: "absolute")
                For polygon: points (list of [x, y] coordinates)
                For line: start_point, end_point ([x, y] coordinates)

        Returns:
            List of validated and parsed zone dictionaries

        Raises:
            ValueError: If zone configuration is invalid
        """
        parsed_zones = []

        for zone in zones:
            # Required fields
            if "zone_id" not in zone:
                raise ValueError("Zone must have 'zone_id'")
            if "name" not in zone:
                raise ValueError("Zone must have 'name'")
            if "type" not in zone:
                raise ValueError("Zone must have 'type'")

            zone_id = zone["zone_id"]
            zone_name = zone["name"]
            zone_type = zone["type"]

            if zone_type == "polygon":
                if "points" not in zone:
                    raise ValueError(f"Polygon zone {zone_id} must have 'points'")
                points = zone["points"]
                if len(points) < 3:
                    raise ValueError(
                        f"Polygon zone {zone_id} must have at least 3 points"
                    )

                # Check coordinate type
                coordinate_type = zone.get("coordinate_type", "absolute")

                if coordinate_type == "percentage":
                    # Store percentage values, will convert to absolute when frame size known
                    parsed_points = [tuple(map(float, pt)) for pt in points]
                    parsed_zone = {
                        "zone_id": zone_id,
                        "name": zone_name,
                        "type": "polygon",
                        "coordinate_type": "percentage",
                        "points_percent": parsed_points,  # Store as percentage
                        "direction": zone.get("direction", "bidirectional"),
                        "enter_threshold": zone.get("enter_threshold", 0.5),
                        "exit_threshold": zone.get("exit_threshold", 0.5),
                    }
                else:
                    # Absolute coordinates
                    parsed_points = [tuple(map(float, pt)) for pt in points]
                    parsed_zone = {
                        "zone_id": zone_id,
                        "name": zone_name,
                        "type": "polygon",
                        "coordinate_type": "absolute",
                        "points": parsed_points,
                        "direction": zone.get("direction", "bidirectional"),
                        "enter_threshold": zone.get("enter_threshold", 0.5),
                        "exit_threshold": zone.get("exit_threshold", 0.5),
                    }

            elif zone_type == "line":
                if "start_point" not in zone or "end_point" not in zone:
                    raise ValueError(
                        f"Line zone {zone_id} must have 'start_point' and 'end_point'"
                    )

                # Validate direction if provided
                direction = zone.get("direction", "one_way")
                valid_directions = [
                    "one_way",
                    "left_to_right",
                    "right_to_left",
                    "top_to_bottom",
                    "bottom_to_top",
                ]
                if direction not in valid_directions:
                    raise ValueError(
                        f"Line zone {zone_id} has invalid direction '{direction}'. "
                        f"Valid values: {valid_directions}"
                    )

                # Check coordinate type
                coordinate_type = zone.get("coordinate_type", "absolute")

                if coordinate_type == "percentage":
                    # Store percentage values
                    parsed_zone = {
                        "zone_id": zone_id,
                        "name": zone_name,
                        "type": "line",
                        "coordinate_type": "percentage",
                        "start_point_percent": tuple(map(float, zone["start_point"])),
                        "end_point_percent": tuple(map(float, zone["end_point"])),
                        "direction": direction,
                        "side": zone.get("side", "above"),  # Legacy support
                        "enter_threshold": zone.get("enter_threshold", 1),
                        "exit_threshold": zone.get("exit_threshold", 1),
                    }
                else:
                    # Absolute coordinates
                    parsed_zone = {
                        "zone_id": zone_id,
                        "name": zone_name,
                        "type": "line",
                        "coordinate_type": "absolute",
                        "start_point": tuple(map(float, zone["start_point"])),
                        "end_point": tuple(map(float, zone["end_point"])),
                        "direction": direction,
                        "side": zone.get("side", "above"),  # Legacy support
                        "enter_threshold": zone.get("enter_threshold", 1),
                        "exit_threshold": zone.get("exit_threshold", 1),
                    }

            else:
                raise ValueError(f"Unknown zone type: {zone_type}")

            parsed_zones.append(parsed_zone)

        return parsed_zones

    def _get_track_centroid(
        self, detection: Dict[str, Any]
    ) -> Optional[Tuple[float, float]]:
        """
        Get centroid of track from detection bbox.

        Args:
            detection: Detection dictionary with bbox

        Returns:
            (x, y) centroid coordinates or None if bbox invalid
        """
        bbox = detection.get("bbox")
        if bbox is None:
            return None

        # Handle numpy array or list
        if hasattr(bbox, "__len__"):
            if len(bbox) < 4:
                return None
        else:
            return None

        # Handle both [x1, y1, x2, y2] and [x, y, w, h] formats
        if len(bbox) == 4:
            x1, y1, x2, y2 = bbox[:4]
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            return (cx, cy)

        return None

    def _get_zone_points(
        self, zone: Dict[str, Any], frame_width: int, frame_height: int
    ) -> List[Tuple[float, float]]:
        """
        Get absolute points for zone (convert percentage if needed).

        Args:
            zone: Zone configuration dictionary
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            List of absolute (x, y) points
        """
        if zone.get("coordinate_type") == "percentage":
            # Convert percentage to absolute
            points_percent = zone.get("points_percent", [])
            return [
                (x_percent * frame_width / 100.0, y_percent * frame_height / 100.0)
                for x_percent, y_percent in points_percent
            ]
        else:
            # Already absolute
            return zone.get("points", [])

    def _update_current_count(self, zone_id: str) -> None:
        """
        Recalculate current count for a zone based on actual track states.

        Args:
            zone_id: Zone ID to update
        """
        current = 0
        for track_id, zone_states in self.track_zone_state.items():
            if zone_states.get(zone_id, False):
                current += 1
        self.zone_counts[zone_id]["current"] = current

    def _get_line_points(
        self, zone: Dict[str, Any], frame_width: int, frame_height: int
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get absolute line points for zone (convert percentage if needed).

        Args:
            zone: Zone configuration dictionary
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            Tuple of (start_point, end_point) in absolute coordinates
        """
        if zone.get("coordinate_type") == "percentage":
            # Convert percentage to absolute
            start_percent = zone.get("start_point_percent", (0, 0))
            end_percent = zone.get("end_point_percent", (0, 0))
            start = (
                start_percent[0] * frame_width / 100.0,
                start_percent[1] * frame_height / 100.0,
            )
            end = (
                end_percent[0] * frame_width / 100.0,
                end_percent[1] * frame_height / 100.0,
            )
            return (start, end)
        else:
            # Already absolute
            return (zone.get("start_point"), zone.get("end_point"))

    def _check_zone_polygon(
        self,
        point: Tuple[float, float],
        zone: Dict[str, Any],
        frame_width: int,
        frame_height: int,
    ) -> bool:
        """
        Check if point is inside polygon zone.

        Args:
            point: (x, y) coordinates
            zone: Zone configuration dictionary
            frame_width: Frame width (for percentage conversion)
            frame_height: Frame height (for percentage conversion)

        Returns:
            True if point is inside polygon
        """
        points = self._get_zone_points(zone, frame_width, frame_height)
        return point_in_polygon(point, points)

    def _check_zone_line(
        self,
        prev_point: Tuple[float, float],
        curr_point: Tuple[float, float],
        zone: Dict[str, Any],
        frame_width: int,
        frame_height: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if point crossed line zone and detect movement direction relative to line.

        Args:
            prev_point: Previous point (x, y)
            curr_point: Current point (x, y)
            zone: Zone configuration dictionary
            frame_width: Frame width (for percentage conversion)
            frame_height: Frame height (for percentage conversion)

        Returns:
            Tuple of (crossed: bool, movement_direction: Optional[str])
            - crossed: True if line was crossed
            - movement_direction: "forward" if moving in same direction as line, "backward" if opposite, None if not crossed
        """
        start_point, end_point = self._get_line_points(zone, frame_width, frame_height)

        # Convert to numpy for easier computation
        prev = np.array(prev_point)
        curr = np.array(curr_point)
        line_s = np.array(start_point)
        line_e = np.array(end_point)

        # Vector from line start to end (line direction)
        line_vec = line_e - line_s
        line_length_sq = np.dot(line_vec, line_vec)

        # Handle degenerate case (zero-length line)
        if line_length_sq < 1e-6:
            return (False, None)

        # Vector of person movement
        movement_vec = curr - prev

        # Vector from line start to previous and current points
        prev_vec = prev - line_s
        curr_vec = curr - line_s

        # Cross product to determine which side of line (2D cross product = scalar)
        prev_cross = float(np.cross(line_vec, prev_vec))
        curr_cross = float(np.cross(line_vec, curr_vec))

        # Check if crossing occurred (sign change)
        crossing_detected = False
        movement_direction = None

        if abs(prev_cross) < 1e-6 or abs(curr_cross) < 1e-6:
            # One point is collinear with line - check if it's crossing the segment
            # Project points onto line to check if crossing segment
            t_prev = (
                np.dot(prev_vec, line_vec) / line_length_sq if line_length_sq > 0 else 0
            )
            t_curr = (
                np.dot(curr_vec, line_vec) / line_length_sq if line_length_sq > 0 else 0
            )

            # Check if crossing segment boundaries (0 <= t <= 1)
            if (t_prev < 0 and 0 <= t_curr <= 1) or (t_prev > 1 and 0 <= t_curr <= 1):
                crossing_detected = True
            elif (0 <= t_prev <= 1 and t_curr < 0) or (0 <= t_prev <= 1 and t_curr > 1):
                crossing_detected = True

            if crossing_detected:
                # Determine movement direction relative to line direction
                # Dot product of movement_vec and line_vec
                dot_product = np.dot(movement_vec, line_vec)
                movement_direction = "forward" if dot_product > 0 else "backward"

        elif prev_cross * curr_cross < 0:
            # Sign change - crossing detected
            # Check if crossing point is within line segment
            # Parameter t for intersection point on line
            t = prev_cross / (prev_cross - curr_cross)

            if 0 <= t <= 1:
                crossing_detected = True
                # Determine movement direction relative to line direction
                # Use dot product of movement vector and line vector
                dot_product = np.dot(movement_vec, line_vec)
                movement_direction = "forward" if dot_product > 0 else "backward"

        if not crossing_detected:
            # No crossing - use legacy behavior for backward compatibility
            if "direction" in zone and zone.get("direction") not in ["one_way", None]:
                # New direction-based mode: return False with no direction
                return (False, None)
            else:
                # Legacy mode: use side parameter
                crossed = line_crossing(
                    prev_point,
                    curr_point,
                    start_point,
                    end_point,
                    zone.get("side", "above"),
                )
                return (crossed, None)

        return (True, movement_direction)

    def update(
        self, detections: List[Dict[str, Any]], frame: np.ndarray, frame_num: int = 0
    ) -> Dict[str, Any]:
        """
        Update counter with new detections.

        Args:
            detections: List of detection dictionaries with track_id and bbox
            frame: Current frame (for visualization and percentage conversion)
            frame_num: Current frame number (for matching disappeared tracks)

        Returns:
            Dictionary with counts and event information
        """
        # Store frame number for matching logic
        self._frame_num = frame_num

        # Update frame size for percentage-based zones
        if frame is not None and len(frame.shape) >= 2:
            frame_height, frame_width = frame.shape[:2]
            self._frame_size = (frame_width, frame_height)
        else:
            frame_width = self._frame_size[0] if self._frame_size else 1920
            frame_height = self._frame_size[1] if self._frame_size else 1080

        current_track_ids = set()
        events = []

        # First, build current_track_ids set
        for detection in detections:
            track_id = detection.get("track_id")
            if track_id is not None:
                current_track_ids.add(track_id)

        # Clean up stale tracks FIRST and store for matching
        stale_tracks = set(self.track_positions.keys()) - current_track_ids
        for stale_track_id in stale_tracks:
            # Store disappeared track info for position matching
            stale_centroid = self.track_positions.get(stale_track_id, {}).get(
                "centroid"
            )
            if stale_centroid:
                # Store last_movement for line zones
                zone_states_with_movement = {}
                for zone_id in self.track_zone_state.get(stale_track_id, {}):
                    zone_states_with_movement[zone_id] = self.track_zone_state.get(
                        stale_track_id, {}
                    ).get(zone_id)
                    # Also store last_movement if exists
                    last_mov_key = f"{zone_id}_last_movement"
                    if last_mov_key in self.track_zone_state.get(stale_track_id, {}):
                        zone_states_with_movement[
                            last_mov_key
                        ] = self.track_zone_state.get(stale_track_id, {}).get(
                            last_mov_key
                        )

                self.disappeared_tracks[stale_track_id] = {
                    "position": stale_centroid,
                    "frame": frame_num if hasattr(self, "_frame_num") else 0,
                    "zone_states": zone_states_with_movement,
                    "zone_counted": self.track_zone_counted.get(
                        stale_track_id, {}
                    ).copy(),
                    "zone_frame_count": self.track_zone_frame_count.get(
                        stale_track_id, {}
                    ).copy(),
                }
                logger.debug(
                    f"Track {stale_track_id} disappeared at {stale_centroid}, stored for matching"
                )

        # Try to match new tracks with disappeared tracks by position
        # Do this BEFORE processing detections to transfer state early
        matched_stale_ids = set()
        current_frame = frame_num if hasattr(self, "_frame_num") else 0

        for detection in detections:
            new_track_id = detection.get("track_id")
            if new_track_id is None:
                continue

            # Check if this is a newly appearing track (not in existing positions)
            is_new_track = new_track_id not in self.track_positions

            new_centroid = self._get_track_centroid(detection)
            if new_centroid is None:
                continue

            # Find closest disappeared track within threshold
            best_match = None
            best_distance = float("inf")

            for stale_track_id, stale_info in list(self.disappeared_tracks.items()):
                if stale_track_id in matched_stale_ids:
                    continue  # Already matched to another track

                stale_pos = stale_info["position"]
                distance = np.sqrt(
                    (new_centroid[0] - stale_pos[0]) ** 2
                    + (new_centroid[1] - stale_pos[1]) ** 2
                )

                # Only match if:
                # 1. Within distance threshold (configurable, default 100px)
                # 2. Disappeared recently (within last 10 frames)
                # 3. This is a new track (not already tracked in previous frames)
                frame_diff = current_frame - stale_info["frame"]
                if (
                    distance < self._position_match_threshold
                    and distance < best_distance
                    and frame_diff <= 10
                    and is_new_track
                ):
                    best_match = stale_track_id
                    best_distance = distance

            # If found match, transfer state to new track BEFORE processing
            if best_match is not None:
                stale_info = self.disappeared_tracks[best_match]
                logger.info(
                    f"Matched new track {new_track_id} with disappeared track {best_match} "
                    f"(distance: {best_distance:.1f}px, frame_diff: {current_frame - stale_info['frame']})"
                )

                # Transfer zone states and flags to prevent duplicate counting
                if new_track_id not in self.track_zone_state:
                    self.track_zone_state[new_track_id] = {}
                if new_track_id not in self.track_zone_counted:
                    self.track_zone_counted[new_track_id] = {}
                if new_track_id not in self.track_zone_frame_count:
                    self.track_zone_frame_count[new_track_id] = {}

                # Transfer all zone states including last_direction
                for key, value in stale_info["zone_states"].items():
                    self.track_zone_state[new_track_id][key] = value

                # Transfer counted flags
                for zone_id, counted in stale_info["zone_counted"].items():
                    self.track_zone_counted[new_track_id][zone_id] = counted

                # Transfer frame counts
                for zone_id, frame_count in stale_info["zone_frame_count"].items():
                    self.track_zone_frame_count[new_track_id][zone_id] = frame_count

                # Also transfer previous position to avoid false crossing detection
                # CRITICAL: Store stale position AND current position to properly handle crossing detection
                if "position" in stale_info:
                    if new_track_id not in self.track_positions:
                        self.track_positions[new_track_id] = {}
                    # Store stale position as previous position for next frame
                    # This ensures continuity when checking crossing
                    self.track_positions[new_track_id]["centroid"] = stale_info[
                        "position"
                    ]
                    # Store current position separately to track movement
                    self.track_positions[new_track_id]["matched_at"] = new_centroid
                    # Mark this track as just matched - skip crossing check for N frames to stabilize
                    if new_track_id not in self.track_zone_state:
                        self.track_zone_state[new_track_id] = {}
                    self.track_zone_state[new_track_id]["_just_matched"] = current_frame
                    # Also store which side of line the track was on when it disappeared
                    # This helps prevent false crossing detection
                    for zone in self.zones:
                        if zone.get("type") == "line":
                            zone_id = zone["zone_id"]
                            stale_pos = stale_info["position"]
                            # Check which side of line the stale position was on
                            start_point, end_point = self._get_line_points(
                                zone, frame_width, frame_height
                            )
                            line_vec = np.array(end_point) - np.array(start_point)
                            stale_vec = np.array(stale_pos) - np.array(start_point)
                            stale_cross = float(np.cross(line_vec, stale_vec))
                            stale_side = (
                                "left"
                                if stale_cross < 0
                                else "right"
                                if stale_cross > 0
                                else "on"
                            )
                            self.track_zone_state[new_track_id][
                                f"{zone_id}_matched_side"
                            ] = stale_side

                # Remove matched disappeared track
                del self.disappeared_tracks[best_match]
                matched_stale_ids.add(best_match)

        # Process each detection for zone checking
        for detection in detections:
            track_id = detection.get("track_id")
            if track_id is None:
                continue
            centroid = self._get_track_centroid(detection)
            if centroid is None:
                continue

            # Get previous position
            prev_centroid = self.track_positions.get(track_id, {}).get("centroid")
            prev_centroid = (
                prev_centroid or centroid
            )  # Use current as prev if no history

            # Check each zone
            for zone in self.zones:
                zone_id = zone["zone_id"]
                zone_type = zone["type"]

                # Get previous zone state (confirmed state, not raw)
                prev_confirmed_in_zone = self.track_zone_state.get(track_id, {}).get(
                    zone_id, False
                )

                # Initialize tracking structures
                if track_id not in self.track_zone_frame_count:
                    self.track_zone_frame_count[track_id] = {}
                if zone_id not in self.track_zone_frame_count[track_id]:
                    self.track_zone_frame_count[track_id][zone_id] = 0

                if track_id not in self.track_zone_counted:
                    self.track_zone_counted[track_id] = {}
                if zone_id not in self.track_zone_counted[track_id]:
                    self.track_zone_counted[track_id][
                        zone_id
                    ] = None  # None, "enter", or "exit"

                # Check current zone state (with frame size for percentage conversion)
                if zone_type == "polygon":
                    curr_in_zone = self._check_zone_polygon(
                        centroid, zone, frame_width, frame_height
                    )
                    crossing_direction = None
                elif zone_type == "line":
                    crossed, crossing_direction = self._check_zone_line(
                        prev_centroid, centroid, zone, frame_width, frame_height
                    )
                    curr_in_zone = crossed
                else:
                    curr_in_zone = False
                    crossing_direction = None

                # Handle line zones with direction-based counting
                if zone_type == "line":
                    direction_config = zone.get("direction", "one_way")

                    # Check if using direction-based mode
                    if direction_config not in ["one_way", None]:
                        # Direction-based line crossing logic
                        # movement_direction: "forward" = same direction as line (start->end), "backward" = opposite
                        # Config direction defines which movement direction = IN

                        # For left_to_right: line goes left->right, forward movement = left->right = IN
                        # For right_to_left: line goes left->right, backward movement = right->left = IN
                        # For top_to_bottom: line goes top->bottom, forward movement = top->bottom = IN
                        # For bottom_to_top: line goes top->bottom, backward movement = bottom->top = IN

                        expected_enter_movement = None
                        expected_exit_movement = None

                        if direction_config == "left_to_right":
                            # Line goes from left to right, forward movement = IN
                            expected_enter_movement = "forward"
                            expected_exit_movement = "backward"
                        elif direction_config == "right_to_left":
                            # Line goes from left to right, backward movement = IN
                            expected_enter_movement = "backward"
                            expected_exit_movement = "forward"
                        elif direction_config == "top_to_bottom":
                            # Line goes from top to bottom, forward movement = IN
                            expected_enter_movement = "forward"
                            expected_exit_movement = "backward"
                        elif direction_config == "bottom_to_top":
                            # Line goes from top to bottom, backward movement = IN
                            expected_enter_movement = "backward"
                            expected_exit_movement = "forward"

                        if expected_enter_movement is not None:
                            # Direction-based mode
                            last_counted = self.track_zone_counted[track_id][zone_id]
                            last_movement_direction = self.track_zone_state.get(
                                track_id, {}
                            ).get(f"{zone_id}_last_movement")

                            # Skip if track was just matched - wait for stable movement before counting
                            just_matched_frame = self.track_zone_state.get(
                                track_id, {}
                            ).get("_just_matched")
                            if just_matched_frame is not None:
                                frames_since_match = frame_num - just_matched_frame
                                # Skip crossing check for 2 frames after match to stabilize
                                if frames_since_match < 2:
                                    logger.debug(
                                        f"Track {track_id} just matched {frames_since_match} frames ago, skipping crossing check"
                                    )
                                    # Clear flag after waiting period
                                    if frames_since_match >= 1:
                                        self.track_zone_state[track_id][
                                            "_just_matched"
                                        ] = None
                                    continue
                                else:
                                    # Clear flag after waiting period
                                    self.track_zone_state[track_id][
                                        "_just_matched"
                                    ] = None

                            # Only process if crossing detected AND movement direction changed
                            # This prevents duplicate events when track is matched/reappears
                            if (
                                crossing_direction is not None
                                and crossing_direction != last_movement_direction
                            ):
                                # Additional check: ensure we have valid previous position and actual movement
                                # If prev_centroid is same as current (track just matched), skip to avoid false positive
                                if (
                                    prev_centroid is not None
                                    and prev_centroid != centroid
                                ):
                                    # Additional check: ensure minimum movement distance to avoid noise
                                    movement_distance = np.sqrt(
                                        (centroid[0] - prev_centroid[0]) ** 2
                                        + (centroid[1] - prev_centroid[1]) ** 2
                                    )
                                    min_movement_threshold = 5.0  # pixels - minimum movement to count crossing

                                    if movement_distance >= min_movement_threshold:
                                        if (
                                            crossing_direction
                                            == expected_enter_movement
                                        ):
                                            # Enter event (moving in IN direction)
                                            if last_counted != "enter":
                                                self.zone_counts[zone_id]["enter"] += 1
                                                self.zone_counts[zone_id]["total"] += 1
                                                self.track_zone_counted[track_id][
                                                    zone_id
                                                ] = "enter"
                                                if (
                                                    track_id
                                                    not in self.track_zone_state
                                                ):
                                                    self.track_zone_state[track_id] = {}
                                                self.track_zone_state[track_id][
                                                    f"{zone_id}_last_movement"
                                                ] = crossing_direction
                                                events.append(
                                                    {
                                                        "type": "enter",
                                                        "zone_id": zone_id,
                                                        "zone_name": zone["name"],
                                                        "track_id": track_id,
                                                    }
                                                )
                                                logger.info(
                                                    f"Track {track_id} entered zone {zone_id} ({zone['name']}) - movement: {crossing_direction}"
                                                )
                                        elif (
                                            crossing_direction == expected_exit_movement
                                        ):
                                            # Exit event (moving in OUT direction)
                                            if last_counted != "exit":
                                                self.zone_counts[zone_id]["exit"] += 1
                                                self.zone_counts[zone_id]["total"] -= 1
                                                self.track_zone_counted[track_id][
                                                    zone_id
                                                ] = "exit"
                                                if (
                                                    track_id
                                                    not in self.track_zone_state
                                                ):
                                                    self.track_zone_state[track_id] = {}
                                                self.track_zone_state[track_id][
                                                    f"{zone_id}_last_movement"
                                                ] = crossing_direction
                                                events.append(
                                                    {
                                                        "type": "exit",
                                                        "zone_id": zone_id,
                                                        "zone_name": zone["name"],
                                                        "track_id": track_id,
                                                    }
                                                )
                                                logger.info(
                                                    f"Track {track_id} exited zone {zone_id} ({zone['name']}) - movement: {crossing_direction}"
                                                )
                                    else:
                                        logger.debug(
                                            f"Track {track_id} movement too small ({movement_distance:.1f}px < {min_movement_threshold}px), skipping"
                                        )
                                else:
                                    # Track just matched/reappeared at same position - don't count as crossing
                                    logger.debug(
                                        f"Track {track_id} matched/reappeared at same position, skipping crossing check"
                                    )

                            # Continue to next zone (position will be updated at end of detection loop)
                            continue  # Skip polygon/legacy logic below

                # Polygon zone logic (or legacy line zone logic)
                # Flickering protection: Use threshold to prevent rapid state changes
                enter_threshold = zone.get("enter_threshold", 1)  # Default: 1 frame
                exit_threshold = zone.get("exit_threshold", 1)  # Default: 1 frame

                # Track consecutive frames inside/outside for threshold
                if curr_in_zone:
                    # Increment if inside
                    if self.track_zone_frame_count[track_id][zone_id] >= 0:
                        self.track_zone_frame_count[track_id][zone_id] += 1
                    else:
                        # Was exiting, reset and start counting inside
                        self.track_zone_frame_count[track_id][zone_id] = 1
                else:
                    # Decrement if outside (negative = outside frames)
                    if self.track_zone_frame_count[track_id][zone_id] > 0:
                        # Was inside, start counting outside
                        self.track_zone_frame_count[track_id][zone_id] = -1
                    elif self.track_zone_frame_count[track_id][zone_id] < 0:
                        # Continue counting outside frames
                        self.track_zone_frame_count[track_id][zone_id] -= 1
                    else:
                        # Already at 0 (never was in zone)
                        self.track_zone_frame_count[track_id][zone_id] = 0

                # Only consider state change if threshold is met
                confirmed_curr_in_zone = (
                    curr_in_zone
                    and self.track_zone_frame_count[track_id][zone_id]
                    >= enter_threshold
                )
                # For exit, we need to check that we've been outside long enough
                # AND that we were previously inside (confirmed)
                outside_frames = (
                    abs(self.track_zone_frame_count[track_id][zone_id])
                    if self.track_zone_frame_count[track_id][zone_id] < 0
                    else 0
                )
                confirmed_exit = (
                    not curr_in_zone
                    and prev_confirmed_in_zone
                    and outside_frames >= exit_threshold
                )

                # Get last counted event for this track/zone
                last_counted = self.track_zone_counted[track_id][zone_id]

                # Detect ENTER: must be outside before, now inside, and haven't counted enter yet
                if not prev_confirmed_in_zone and confirmed_curr_in_zone:
                    # Only count if we haven't already counted this enter event
                    if last_counted != "enter":
                        # Entered zone
                        self.zone_counts[zone_id]["enter"] += 1
                        self.zone_counts[zone_id]["total"] += 1
                        # Mark that we've counted this enter
                        self.track_zone_counted[track_id][zone_id] = "enter"
                        events.append(
                            {
                                "type": "enter",
                                "zone_id": zone_id,
                                "zone_name": zone["name"],
                                "track_id": track_id,
                            }
                        )
                        logger.info(
                            f"Track {track_id} entered zone {zone_id} ({zone['name']})"
                        )

                # Detect EXIT: must be inside before, now outside, and haven't counted exit yet
                elif prev_confirmed_in_zone and confirmed_exit:
                    # Only count if we haven't already counted this exit event
                    # CRITICAL: Check last_counted AFTER we update it to prevent race condition
                    if last_counted != "exit":
                        # Exited zone
                        self.zone_counts[zone_id]["exit"] += 1
                        self.zone_counts[zone_id]["total"] -= 1
                        # CRITICAL: Mark as counted FIRST before any other operations
                        self.track_zone_counted[track_id][zone_id] = "exit"
                        # CRITICAL: Update state immediately to False to prevent duplicate counting
                        if track_id not in self.track_zone_state:
                            self.track_zone_state[track_id] = {}
                        self.track_zone_state[track_id][zone_id] = False
                        events.append(
                            {
                                "type": "exit",
                                "zone_id": zone_id,
                                "zone_name": zone["name"],
                                "track_id": track_id,
                            }
                        )
                        logger.info(
                            f"Track {track_id} exited zone {zone_id} ({zone['name']})"
                        )
                    else:
                        # Already counted exit - ensure state is False to prevent further triggers
                        if track_id not in self.track_zone_state:
                            self.track_zone_state[track_id] = {}
                        self.track_zone_state[track_id][zone_id] = False

                # Update zone state (use confirmed state, not raw)
                if track_id not in self.track_zone_state:
                    self.track_zone_state[track_id] = {}

                # Only update state if we haven't just counted an exit (state already updated above)
                if not (
                    prev_confirmed_in_zone and confirmed_exit and last_counted != "exit"
                ):
                    # Update state to confirmed state (after threshold check)
                    self.track_zone_state[track_id][zone_id] = confirmed_curr_in_zone

                # Reset counted flag when crossing boundary in opposite direction
                # This allows counting again when track crosses boundary the other way
                current_counted = self.track_zone_counted[track_id][zone_id]
                if confirmed_curr_in_zone and prev_confirmed_in_zone is False:
                    # Just confirmed entered - reset exit flag to allow new cycles
                    if current_counted == "exit":
                        self.track_zone_counted[track_id][zone_id] = None

            # Update position history
            if track_id not in self.track_positions:
                self.track_positions[track_id] = {}
            self.track_positions[track_id]["centroid"] = centroid

        # Recalculate current counts for all zones from actual states
        for zone in self.zones:
            self._update_current_count(zone["zone_id"])

        # Only count exit for unmatched stale tracks (that haven't been matched to new tracks)
        for stale_track_id in stale_tracks:
            # Skip if this track was matched to a new track
            if stale_track_id in matched_stale_ids:
                continue
            # Skip if already removed from disappeared_tracks
            if stale_track_id not in self.disappeared_tracks:
                continue

            for zone in self.zones:
                zone_id = zone["zone_id"]
                if self.track_zone_state.get(stale_track_id, {}).get(zone_id, False):
                    # Track was in zone and not matched - count as exit
                    self.track_zone_state[stale_track_id][zone_id] = False
                    self.zone_counts[zone_id]["exit"] += 1
                    self.zone_counts[zone_id]["total"] -= 1
                    self.zone_counts[zone_id]["current"] = max(
                        0, self.zone_counts[zone_id]["current"] - 1
                    )
                    events.append(
                        {
                            "type": "exit",
                            "zone_id": zone_id,
                            "zone_name": zone["name"],
                            "track_id": stale_track_id,
                            "reason": "track_disappeared",
                        }
                    )
                    logger.debug(
                        f"Track {stale_track_id} exited zone {zone_id} ({zone['name']}) - track disappeared (unmatched)"
                    )

            # Clean up unmatched disappeared track after processing
            del self.disappeared_tracks[stale_track_id]

        # Clean up old disappeared tracks (older than 30 frames)
        current_frame = frame_num if hasattr(self, "_frame_num") else 0
        for stale_track_id, stale_info in list(self.disappeared_tracks.items()):
            frame_diff = current_frame - stale_info["frame"]
            if frame_diff > 30:
                del self.disappeared_tracks[stale_track_id]

        return {
            "counts": self.zone_counts.copy(),
            "events": events,
            "active_tracks": len(current_track_ids),
        }

    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """
        Get current counts for all zones.

        Returns:
            Dictionary mapping zone_id to count dictionary
        """
        return self.zone_counts.copy()

    def reset(self, zone_id: Optional[str] = None) -> None:
        """
        Reset counts for zone(s).

        Args:
            zone_id: Zone ID to reset (None = reset all zones)
        """
        if zone_id is None:
            # Reset all zones
            for z_id in self.zone_counts:
                self.zone_counts[z_id] = {
                    "enter": 0,
                    "exit": 0,
                    "total": 0,
                    "current": 0,
                }
            self.track_positions.clear()
            self.track_zone_state.clear()
            self.track_zone_frame_count.clear()
            self.track_zone_counted.clear()
            logger.info("Reset all zone counts")
        else:
            # Reset specific zone
            if zone_id in self.zone_counts:
                self.zone_counts[zone_id] = {
                    "enter": 0,
                    "exit": 0,
                    "total": 0,
                    "current": 0,
                }
                # Clear zone state for all tracks
                for track_id in self.track_zone_state:
                    if zone_id in self.track_zone_state[track_id]:
                        del self.track_zone_state[track_id][zone_id]
                for track_id in self.track_zone_frame_count:
                    if zone_id in self.track_zone_frame_count[track_id]:
                        del self.track_zone_frame_count[track_id][zone_id]
                for track_id in self.track_zone_counted:
                    if zone_id in self.track_zone_counted[track_id]:
                        del self.track_zone_counted[track_id][zone_id]
                logger.info(f"Reset counts for zone {zone_id}")
            else:
                logger.warning(f"Zone {zone_id} not found for reset")

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw zones and counts on frame.

        Args:
            frame: Frame to draw on

        Returns:
            Frame with zones and counts drawn
        """
        frame = frame.copy()

        # Get frame size for percentage conversion
        if frame is not None and len(frame.shape) >= 2:
            frame_height, frame_width = frame.shape[:2]
        else:
            frame_width = self._frame_size[0] if self._frame_size else 1920
            frame_height = self._frame_size[1] if self._frame_size else 1080

        for zone in self.zones:
            zone_id = zone["zone_id"]
            zone_name = zone["name"]
            counts = self.zone_counts[zone_id]

            if zone["type"] == "polygon":
                # Get absolute points (convert percentage if needed)
                points = self._get_zone_points(zone, frame_width, frame_height)
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                # Draw filled polygon with transparency
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], (0, 255, 0))
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

                # Draw point numbers (0, 1, 2, 3...) at each vertex
                for idx, point in enumerate(points):
                    x, y = int(point[0]), int(point[1])
                    # Draw circle at point
                    cv2.circle(
                        frame, (x, y), 8, (255, 255, 0), -1
                    )  # Yellow filled circle
                    cv2.circle(frame, (x, y), 8, (0, 0, 0), 2)  # Black border
                    # Draw point number
                    text = str(idx)
                    (text_width, text_height), baseline = cv2.getTextSize(
                        text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                    )
                    text_x = x - text_width // 2
                    text_y = y + text_height // 2
                    cv2.putText(
                        frame,
                        text,
                        (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 0),  # Black text
                        2,
                    )

                # Draw label at centroid
                centroid = np.mean(pts, axis=0)[0]
                # Prefer daily counts if available (from DailyPersonCounter wrapper - synced across channels)
                # Prefer global counts if present; otherwise fallback to local In/Out
                global_enter = counts.get("global_enter")
                global_exit = counts.get("global_exit")
                global_unique = counts.get("global_unique_persons")
                if global_enter is not None and global_exit is not None:
                    parts = [f"Global In:{int(global_enter)} Out:{int(global_exit)}"]
                    if global_unique is not None:
                        parts.append(f"Unique:{int(global_unique)}")
                    parts.append(f"Current:{counts['current']}")
                    label = f"{zone_name}: " + " ".join(parts)
                else:
                    label = (
                        f"{zone_name}: In:{counts['enter']} Out:{counts['exit']} "
                        f"Current:{counts['current']}"
                    )
                cv2.putText(
                    frame,
                    label,
                    (int(centroid[0]), int(centroid[1])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            elif zone["type"] == "line":
                # Get absolute points (convert percentage if needed)
                start_point, end_point = self._get_line_points(
                    zone, frame_width, frame_height
                )
                start = tuple(map(int, start_point))
                end = tuple(map(int, end_point))
                cv2.line(frame, start, end, (255, 0, 0), 2)

                # Draw point markers and numbers
                # Point 0 (start_point)
                cv2.circle(frame, start, 8, (255, 255, 0), -1)  # Yellow filled circle
                cv2.circle(frame, start, 8, (0, 0, 0), 2)  # Black border
                (text_width, text_height), _ = cv2.getTextSize(
                    "0", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                cv2.putText(
                    frame,
                    "0",
                    (start[0] - text_width // 2, start[1] + text_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    2,
                )

                # Point 1 (end_point)
                cv2.circle(frame, end, 8, (255, 255, 0), -1)  # Yellow filled circle
                cv2.circle(frame, end, 8, (0, 0, 0), 2)  # Black border
                (text_width, text_height), _ = cv2.getTextSize(
                    "1", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                cv2.putText(
                    frame,
                    "1",
                    (end[0] - text_width // 2, end[1] + text_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    2,
                )

                # Draw label at midpoint
                mid_x = (start[0] + end[0]) // 2
                mid_y = (start[1] + end[1]) // 2
                # Prefer daily counts if available (synced across channels)
                # Prefer global counts if present; otherwise fallback to local In/Out for line zones
                global_enter = counts.get("global_enter")
                global_exit = counts.get("global_exit")
                global_unique = counts.get("global_unique_persons")
                if global_enter is not None and global_exit is not None:
                    parts = [f"Global In:{int(global_enter)} Out:{int(global_exit)}"]
                    if global_unique is not None:
                        parts.append(f"Unique:{int(global_unique)}")
                    label = f"{zone_name}: " + " ".join(parts)
                else:
                    label = f"{zone_name}: In:{counts['enter']} Out:{counts['exit']}"
                cv2.putText(
                    frame,
                    label,
                    (mid_x, mid_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                )

        return frame
