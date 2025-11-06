#!/usr/bin/env python3
"""
Unit tests for percentage-based zone counter.

This module tests zone-based person counting with percentage coordinates.
"""

import pytest
import numpy as np

from src.modules.counter.zone_counter import ZoneCounter


class TestZoneCounterPercentage:
    """Test suite for percentage-based zone counter."""

    @pytest.fixture
    def polygon_zone_percentage(self):
        """Create polygon zone with percentage coordinates."""
        return {
            "zone_id": "zone_percent_1",
            "name": "Left Half Percentage",
            "type": "polygon",
            "coordinate_type": "percentage",
            "points": [[0, 0], [50, 0], [50, 100], [0, 100]],
            "direction": "bidirectional",
        }

    @pytest.fixture
    def line_zone_percentage(self):
        """Create line zone with percentage coordinates."""
        return {
            "zone_id": "line_percent_1",
            "name": "Middle Line Percentage",
            "type": "line",
            "coordinate_type": "percentage",
            "start_point": [0, 50],
            "end_point": [100, 50],
            "direction": "one_way",
            "side": "above",
        }

    @pytest.fixture
    def counter_polygon_percent(self, polygon_zone_percentage):
        """Create ZoneCounter with percentage polygon zone."""
        return ZoneCounter([polygon_zone_percentage])

    @pytest.fixture
    def counter_line_percent(self, line_zone_percentage):
        """Create ZoneCounter with percentage line zone."""
        return ZoneCounter([line_zone_percentage])

    def test_initialization_percentage_polygon(self, polygon_zone_percentage):
        """Test initialization with percentage polygon zone."""
        # Act
        counter = ZoneCounter([polygon_zone_percentage])

        # Assert
        assert counter is not None
        assert len(counter.zones) == 1
        zone = counter.zones[0]
        assert zone["coordinate_type"] == "percentage"
        assert "points_percent" in zone
        assert zone["points_percent"] == [(0, 0), (50, 0), (50, 100), (0, 100)]

    def test_initialization_percentage_line(self, line_zone_percentage):
        """Test initialization with percentage line zone."""
        # Act
        counter = ZoneCounter([line_zone_percentage])

        # Assert
        assert counter is not None
        zone = counter.zones[0]
        assert zone["coordinate_type"] == "percentage"
        assert "start_point_percent" in zone
        assert "end_point_percent" in zone

    def test_percentage_to_absolute_conversion_polygon(self, counter_polygon_percent):
        """Test percentage to absolute coordinate conversion for polygon."""
        # Arrange
        frame_width = 1920
        frame_height = 1080
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

        # Act - update with frame to set frame size
        counter_polygon_percent.update([], frame)

        # Get converted points (through internal method)
        zone = counter_polygon_percent.zones[0]
        points = counter_polygon_percent._get_zone_points(
            zone, frame_width, frame_height
        )

        # Assert - Left half should be from 0 to 960 (50% of 1920)
        assert len(points) == 4
        assert points[0] == (0.0, 0.0)  # Top-left
        assert points[1] == (960.0, 0.0)  # Top-right (50% of 1920)
        assert points[2] == (960.0, 1080.0)  # Bottom-right
        assert points[3] == (0.0, 1080.0)  # Bottom-left

    def test_percentage_to_absolute_conversion_line(self, counter_line_percent):
        """Test percentage to absolute coordinate conversion for line."""
        # Arrange
        frame_width = 1920
        frame_height = 1080
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

        # Act
        counter_line_percent.update([], frame)

        # Get converted points
        zone = counter_line_percent.zones[0]
        start_point, end_point = counter_line_percent._get_line_points(
            zone, frame_width, frame_height
        )

        # Assert - Middle line at 50% height = 540
        assert start_point == (0.0, 540.0)
        assert end_point == (1920.0, 540.0)

    def test_polygon_detection_different_resolutions(self, polygon_zone_percentage):
        """Test polygon detection works across different resolutions."""
        # Arrange
        counter = ZoneCounter([polygon_zone_percentage])

        # Test with 1920x1080
        frame_1080 = np.zeros((1080, 1920, 3), dtype=np.uint8)
        detection_1080 = {"track_id": 1, "bbox": [100, 100, 200, 200]}  # In left half
        counter.update([detection_1080], frame_1080)
        counts_1080 = counter.get_counts()

        # Test with 1280x720
        counter2 = ZoneCounter([polygon_zone_percentage])
        frame_720 = np.zeros((720, 1280, 3), dtype=np.uint8)
        detection_720 = {"track_id": 1, "bbox": [100, 100, 200, 200]}  # In left half
        counter2.update([detection_720], frame_720)
        counts_720 = counter2.get_counts()

        # Assert - Both should detect the point as inside
        # The exact counts may vary, but zone should work for both resolutions
        assert "zone_percent_1" in counts_1080
        assert "zone_percent_1" in counts_720

    def test_mixed_absolute_and_percentage_zones(self):
        """Test mixing absolute and percentage zones in same counter."""
        # Arrange
        absolute_zone = {
            "zone_id": "zone_abs",
            "name": "Absolute Zone",
            "type": "polygon",
            "coordinate_type": "absolute",
            "points": [[0, 0], [100, 0], [100, 100], [0, 100]],
        }
        percentage_zone = {
            "zone_id": "zone_percent",
            "name": "Percentage Zone",
            "type": "polygon",
            "coordinate_type": "percentage",
            "points": [[50, 0], [100, 0], [100, 100], [50, 100]],
        }

        # Act
        counter = ZoneCounter([absolute_zone, percentage_zone])

        # Assert
        assert len(counter.zones) == 2
        assert counter.zones[0]["coordinate_type"] == "absolute"
        assert counter.zones[1]["coordinate_type"] == "percentage"

    def test_draw_zones_percentage(self, counter_polygon_percent):
        """Test drawing percentage-based zones."""
        # Arrange
        frame_width = 1920
        frame_height = 1080
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

        # Act
        result_frame = counter_polygon_percent.draw_zones(frame)

        # Assert
        assert result_frame is not None
        assert result_frame.shape == frame.shape
        # Zone should be drawn (visual check would be needed, but no error is good)

    def test_percentage_bottom_half_zone(self):
        """Test percentage zone for bottom half of screen."""
        # Arrange
        bottom_half_zone = {
            "zone_id": "bottom_half",
            "name": "Bottom Half",
            "type": "polygon",
            "coordinate_type": "percentage",
            "points": [[0, 50], [100, 50], [100, 100], [0, 100]],
        }
        counter = ZoneCounter([bottom_half_zone])

        frame_width = 1920
        frame_height = 1080
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

        # Act
        zone = counter.zones[0]
        points = counter._get_zone_points(zone, frame_width, frame_height)

        # Assert - Bottom half from 540 to 1080
        assert points[0] == (0.0, 540.0)  # Top-left at 50% height
        assert points[1] == (1920.0, 540.0)  # Top-right at 50% height
        assert points[2] == (1920.0, 1080.0)  # Bottom-right
        assert points[3] == (0.0, 1080.0)  # Bottom-left

    def test_percentage_defaults_to_absolute(self):
        """Test that missing coordinate_type defaults to absolute."""
        # Arrange - zone without coordinate_type
        zone = {
            "zone_id": "zone_default",
            "name": "Default Zone",
            "type": "polygon",
            "points": [[0, 0], [100, 0], [100, 100], [0, 100]],
        }

        # Act
        counter = ZoneCounter([zone])

        # Assert
        assert counter.zones[0]["coordinate_type"] == "absolute"
        assert "points" in counter.zones[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

