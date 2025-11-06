# Feature: Direction-Based Line Crossing Counter

## Overview
Thêm tính năng đếm người vào/ra dựa trên hướng đi qua đường line, thay vì chỉ dùng polygon zone. Khi người đi qua line từ điểm A → B thì là "in", ngược lại B → A là "out".

## Requirements

### User Stories
1. **US-1**: Là admin, tôi muốn định nghĩa một đường line với 2 điểm và hướng để đếm người vào/ra
2. **US-2**: Là hệ thống, tôi cần phát hiện khi người đi qua line theo hướng đã định nghĩa và ghi nhận event "enter" hoặc "exit"
3. **US-3**: Là developer, tôi muốn cấu hình line với các hướng như "top_to_bottom", "bottom_to_top", "left_to_right", "right_to_left"

### Acceptance Criteria
- [ ] Hỗ trợ config line với `start_point`, `end_point` và `direction`
- [ ] Phát hiện chính xác khi người đi qua line từ A→B (in) và B→A (out)
- [ ] Tương thích với config hiện tại (polygon vẫn hoạt động)
- [ ] Hỗ trợ cả absolute và percentage coordinates
- [ ] Có flickering protection (threshold)
- [ ] Ghi nhận events vào database như polygon zone

## Technical Approach

### Architecture Changes

#### 1. Config Schema Extension
```json
{
  "zone_id": "line_1",
  "name": "Entrance Line",
  "type": "line",
  "coordinate_type": "percentage",
  "start_point": [30, 50],
  "end_point": [70, 50],
  "direction": "left_to_right",  // "left_to_right" = in, "right_to_left" = out
  "enter_threshold": 1,
  "exit_threshold": 1
}
```

#### 2. Direction Mapping
- `left_to_right`: Từ trái sang phải = ENTER
- `right_to_left`: Từ phải sang trái = EXIT
- `top_to_bottom`: Từ trên xuống = ENTER
- `bottom_to_top`: Từ dưới lên = EXIT

#### 3. Code Changes

**File: `src/modules/counter/zone_counter.py`**
- Modify `_check_zone_line()` to detect direction
- Add `_detect_line_direction()` method
- Update `update()` method to handle direction-based events
- Ensure backward compatibility with existing line detection

**File: `src/modules/counter/zone_counter.py` - `_check_zone_line()`**
- Current: Returns boolean (crossed or not)
- New: Returns tuple `(crossed: bool, direction: Optional[str])`
- Direction: "A_to_B" or "B_to_A" based on crossing side

**File: `input/cameras_config/kidsplaza_thanhxuan.json`**
- Add example line zone configuration

### Implementation Plan

1. **Phase 1: Core Logic**
   - [ ] Add direction detection in `_check_zone_line()`
   - [ ] Map direction to enter/exit events
   - [ ] Update zone state tracking for line zones

2. **Phase 2: Config & Validation**
   - [ ] Add `direction` field validation
   - [ ] Support all 4 directions
   - [ ] Update zone validation logic

3. **Phase 3: Testing**
   - [ ] Unit tests for direction detection
   - [ ] Integration test with video
   - [ ] Verify database events

4. **Phase 4: Documentation**
   - [ ] Update config examples
   - [ ] Add usage guide

## Technical Details

### Direction Detection Algorithm

1. **Line Vector**: `line_vec = end_point - start_point`
2. **Previous Position Vector**: `prev_vec = prev_centroid - start_point`
3. **Current Position Vector**: `curr_vec = curr_centroid - start_point`
4. **Cross Products**: 
   - `prev_cross = cross(line_vec, prev_vec)`
   - `curr_cross = cross(line_vec, curr_vec)`
5. **Crossing Detection**: Sign change (`prev_cross * curr_cross < 0`)
6. **Direction**:
   - If `prev_cross < 0` and `curr_cross > 0`: Crossing from left side → right side
   - If `prev_cross > 0` and `curr_cross < 0`: Crossing from right side → left side

### Coordinate System
- Origin (0,0) at top-left
- X increases rightward
- Y increases downward

### Direction Mapping Examples

**Horizontal Line (left to right):**
- `start_point = [30, 50]`, `end_point = [70, 50]`
- `direction = "left_to_right"`
- Crossing from left (x < 30) to right (x > 70) = ENTER
- Crossing from right (x > 70) to left (x < 30) = EXIT

**Vertical Line (top to bottom):**
- `start_point = [50, 30]`, `end_point = [50, 70]`
- `direction = "top_to_bottom"`
- Crossing from top (y < 30) to bottom (y > 70) = ENTER
- Crossing from bottom (y > 70) to top (y < 30) = EXIT

## Testing Strategy

### Unit Tests
- Test direction detection for all 4 directions
- Test edge cases (parallel movement, no crossing)
- Test with percentage coordinates

### Integration Tests
- Test with real video containing people crossing line
- Verify events are generated correctly
- Verify database storage

### Manual Testing
- Configure line zone in config file
- Run with test video
- Verify enter/exit events match expected direction

## Backward Compatibility

- Existing polygon zones: No changes required
- Existing line zones without `direction`: Use default behavior (maintain current logic)
- Config validation: `direction` is optional for line zones

## Files to Modify

1. `src/modules/counter/zone_counter.py` - Core logic
2. `input/cameras_config/kidsplaza_thanhxuan.json` - Example config
3. `tests/unit/test_zone_counter.py` - Unit tests (if exists)
4. `docs/` - Documentation updates

## Dependencies

- No new dependencies required
- Uses existing numpy for vector calculations
- Uses existing cv2 for drawing (if needed)

## Risk Assessment

- **Low Risk**: Feature is additive, doesn't break existing functionality
- **Testing Required**: Direction detection logic needs thorough testing
- **Config Migration**: Existing configs remain valid

## Timeline

- Planning: ✅ Complete
- Implementation: ~2-3 hours
- Testing: ~1-2 hours
- Documentation: ~30 minutes

