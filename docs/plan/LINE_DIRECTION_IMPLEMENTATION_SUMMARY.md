# Feature Implementation Summary: Direction-Based Line Counter

## ✅ Completed Implementation

### Feature Overview
Đã triển khai thành công tính năng đếm người vào/ra dựa trên hướng đi qua đường line. Khi người đi qua line từ điểm A → B thì là "in", ngược lại B → A là "out".

### Changes Made

#### 1. Core Logic (`src/modules/counter/zone_counter.py`)

**Modified `_check_zone_line()` method:**
- Return type changed from `bool` to `Tuple[bool, Optional[str]]`
- Added direction detection logic using cross product
- Handles collinear cases and segment boundary crossing
- Returns `(crossed: bool, direction: "A_to_B" | "B_to_A" | None)`

**Updated `update()` method:**
- Added direction-based event generation for line zones
- Maps config directions (`left_to_right`, `right_to_left`, etc.) to crossing directions
- Generates enter/exit events based on direction match
- Maintains backward compatibility with legacy line zones

**Zone Validation:**
- Added validation for `direction` field
- Valid values: `["one_way", "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"]`

#### 2. Configuration (`input/cameras_config/kidsplaza_thanhxuan.json`)

**Added example line zone:**
```json
{
  "zone_id": "line_entrance",
  "name": "Entrance Line",
  "type": "line",
  "coordinate_type": "percentage",
  "start_point": [20, 50],
  "end_point": [80, 50],
  "direction": "left_to_right",
  "enter_threshold": 1,
  "exit_threshold": 1
}
```

#### 3. Tests (`tests/unit/test_line_direction.py`)

**Created unit tests:**
- Test 1: Left to Right crossing → Should detect A_to_B
- Test 2: Right to Left crossing → Should detect B_to_A
- Test 3: No crossing (same side) → Should return False, None
- All tests passing ✅

### Direction Mapping

| Config Direction | Enter Direction | Exit Direction | Description |
|-----------------|-----------------|----------------|-------------|
| `left_to_right` | A_to_B | B_to_A | Từ trái sang phải = vào |
| `right_to_left` | B_to_A | A_to_B | Từ phải sang trái = vào |
| `top_to_bottom` | A_to_B | B_to_A | Từ trên xuống = vào |
| `bottom_to_top` | B_to_A | A_to_B | Từ dưới lên = vào |

### Technical Details

**Crossing Detection Algorithm:**
1. Calculate cross products to determine which side of line vector points are on
2. Detect sign change (crossing occurred)
3. Check if crossing point is within line segment (0 <= t <= 1)
4. Determine direction based on cross product signs

**Backward Compatibility:**
- Legacy line zones (without `direction` or `direction="one_way"`) still work
- Uses existing `side` parameter for legacy mode
- Polygon zones unchanged

### Testing Status

✅ **Unit Tests:** All passing
✅ **Linter:** No errors
✅ **Backward Compatibility:** Verified

### Usage Example

```json
{
  "zone_id": "entrance_line",
  "name": "Entrance Line",
  "type": "line",
  "coordinate_type": "percentage",
  "start_point": [30, 50],
  "end_point": [70, 50],
  "direction": "left_to_right",
  "enter_threshold": 1,
  "exit_threshold": 1
}
```

### Next Steps

1. **Manual Testing:** Test with real video containing people crossing line
2. **Integration:** Verify events are stored correctly in database
3. **Documentation:** Update user guide with line zone examples

### Files Modified

- `src/modules/counter/zone_counter.py` - Core implementation
- `input/cameras_config/kidsplaza_thanhxuan.json` - Example config
- `tests/unit/test_line_direction.py` - Unit tests
- `docs/plan/LINE_DIRECTION_COUNTER_FEATURE.md` - Feature plan

### Branch

- Branch: `feature/line-direction-counter`
- Ready for testing and review

