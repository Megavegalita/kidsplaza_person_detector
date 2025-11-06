#!/usr/bin/env python3
"""
Test script for direction-based line counter.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.modules.counter.zone_counter import ZoneCounter

def test_line_direction():
    """Test direction-based line crossing."""
    
    # Test case 1: Horizontal line, left_to_right
    zones = [
        {
            "zone_id": "line_1",
            "name": "Test Line",
            "type": "line",
            "coordinate_type": "absolute",
            "start_point": [100, 200],
            "end_point": [300, 200],
            "direction": "left_to_right",
            "enter_threshold": 1,
            "exit_threshold": 1,
        }
    ]
    
    counter = ZoneCounter(zones)
    
    # Simulate crossing from left to right (should be ENTER)
    # Start at (50, 200) - left of line
    # End at (250, 200) - right of line (crossed)
    prev_point = (50, 200)
    curr_point = (250, 200)
    
    crossed, direction = counter._check_zone_line(
        prev_point, curr_point, zones[0], 640, 480
    )
    
    print(f"Test 1 - Left to Right crossing:")
    print(f"  Crossed: {crossed}")
    print(f"  Direction: {direction}")
    print(f"  Expected: Crossed=True, Direction='forward'")
    assert crossed is True, "Should detect crossing"
    assert direction == "forward", f"Expected forward, got {direction}"
    print("  ✅ PASSED\n")
    
    # Test case 2: Crossing from right to left (should be EXIT)
    prev_point = (350, 200)
    curr_point = (150, 200)
    
    crossed, direction = counter._check_zone_line(
        prev_point, curr_point, zones[0], 640, 480
    )
    
    print(f"Test 2 - Right to Left crossing:")
    print(f"  Crossed: {crossed}")
    print(f"  Direction: {direction}")
    print(f"  Expected: Crossed=True, Direction='backward'")
    assert crossed is True, "Should detect crossing"
    assert direction == "backward", f"Expected backward, got {direction}"
    print("  ✅ PASSED\n")
    
    # Test case 3: No crossing (same side)
    prev_point = (50, 200)
    curr_point = (80, 200)
    
    crossed, direction = counter._check_zone_line(
        prev_point, curr_point, zones[0], 640, 480
    )
    
    print(f"Test 3 - No crossing (same side):")
    print(f"  Crossed: {crossed}")
    print(f"  Direction: {direction}")
    print(f"  Expected: Crossed=False, Direction=None")
    assert crossed == False, "Should not detect crossing"
    assert direction is None, f"Expected None, got {direction}"
    print("  ✅ PASSED\n")
    
    print("All tests passed! ✅")

if __name__ == "__main__":
    test_line_direction()

