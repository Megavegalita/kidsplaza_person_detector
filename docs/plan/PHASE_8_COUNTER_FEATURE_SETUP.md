# Phase 8: Counter Feature & Channel Configuration

## 🎯 Mục Tiêu

Triển khai tính năng đếm người (counter) với khả năng cấu hình:
- Đếm người vào/vào vùng được định nghĩa (counting zones)
- Đếm người ra khỏi vùng
- Cấu hình bật/tắt các tính năng theo channel:
  - Body detection: always enabled (bắt buộc)
  - ByteTrack tracking: always enabled (bắt buộc)
  - Re-ID: configurable per channel (default: true)
  - Gender classification: configurable per channel (default: true)
  - Counter: configurable per channel (default: true)

## 📋 Scope

### Phase 8.1: Channel Configuration System
- Thêm cấu hình features per channel trong camera config JSON
- Load và validate config
- Apply config settings per channel during initialization

### Phase 8.2: Counter Module
- Implement counting zone detection
- Track people entering/exiting zones
- Zone definition (polygon hoặc line-based)
- Count persistence và reporting

### Phase 8.3: Integration
- Integrate counter vào live camera processing pipeline
- Display counts trên overlay
- Store counts vào database

## 🔧 Configuration Structure

### Camera Config Enhancement

**Location**: `input/cameras_config/kidsplaza_thanhxuan.json`

**New Structure**:
```json
{
  "company": "Kidsplaza",
  "address": "Bich Xa, Thach That, Thanh Xuan, Ha Noi",
  "server": {...},
  "credentials": {...},
  "channels": [
    {
      "channel_id": 1,
      "name": "channel_1",
      "rtsp_url": "...",
      "description": "...",
      "location": "ben_ngoai_cam_phai",
      "features": {
        "body_detection": {
          "enabled": true,
          "always": true,
          "comment": "Always enabled, cannot be disabled"
        },
        "tracking": {
          "enabled": true,
          "always": true,
          "comment": "ByteTrack always enabled"
        },
        "reid": {
          "enabled": true,
          "always": false,
          "every_k_frames": 20,
          "ttl_seconds": 60,
          "similarity_threshold": 0.65
        },
        "gender_classification": {
          "enabled": true,
          "always": false,
          "every_k_frames": 20,
          "model_type": "timm_mobile",
          "min_confidence": 0.5
        },
        "counter": {
          "enabled": true,
          "always": false,
          "zones": [
            {
              "zone_id": "zone_1",
              "name": "Main Entrance",
              "type": "polygon",
              "points": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
              "direction": "bidirectional",
              "enter_threshold": 0.5,
              "exit_threshold": 0.5
            },
            {
              "zone_id": "zone_2",
              "name": "Exit Line",
              "type": "line",
              "start_point": [x1, y1],
              "end_point": [x2, y2],
              "direction": "one_way",
              "side": "above"
            }
          ]
        }
      }
    }
  ],
  "default_features": {
    "body_detection": {"enabled": true, "always": true},
    "tracking": {"enabled": true, "always": true},
    "reid": {"enabled": true, "always": false},
    "gender_classification": {"enabled": true, "always": false},
    "counter": {"enabled": true, "always": false}
  }
}
```

## 📦 Deliverables

### 1. Configuration Module Enhancement
**File**: `src/modules/camera/camera_config.py`

**New Methods**:
- `get_channel_features(channel_id: int) -> Dict`
- `get_feature_config(channel_id: int, feature_name: str) -> Optional[Dict]`
- `is_feature_enabled(channel_id: int, feature_name: str) -> bool`
- `validate_features_config(config: Dict) -> bool`

### 2. Counter Module
**File**: `src/modules/counter/zone_counter.py`

**Class**: `ZoneCounter`

**Responsibilities**:
- Define counting zones (polygon hoặc line-based)
- Track track_id positions across frames
- Detect entering/exiting events
- Maintain counts per zone
- Reset counts on demand

**Key Methods**:
```python
class ZoneCounter:
    def __init__(self, zones: List[Dict]) -> None
    def update(self, detections: List[Dict], frame: np.ndarray) -> Dict[str, Any]
    def get_counts(self) -> Dict[str, Dict[str, int]]
    def reset(self, zone_id: Optional[str] = None) -> None
    def draw_zones(self, frame: np.ndarray) -> np.ndarray
```

### 3. Zone Types

#### 3.1 Polygon Zone (Bidirectional)
- Define bằng list of points tạo thành polygon
- Detect khi track_id centroid vào/ra polygon
- Support bidirectional (count both directions)

#### 3.2 Line Zone (One-way)
- Define bằng start_point và end_point
- Detect khi track_id crosses line từ một phía (above/below/left/right)
- Support one-way counting

### 4. Integration Points

#### 4.1 Live Camera Processor
**File**: `src/scripts/process_live_camera.py`

**Changes**:
- Load feature config từ camera config
- Initialize counter nếu `counter.enabled = true`
- Update counter trong processing loop
- Display counts trên overlay

#### 4.2 Video Processor (Optional)
**File**: `src/scripts/process_video_file.py`

**Changes**:
- Support counter config từ CLI hoặc JSON
- Integrate counter vào video processing pipeline

## 🎯 Implementation Steps

### Step 1: Configuration System (P8.1)

#### 1.1 Enhance CameraConfig
- [ ] Add `get_channel_features()` method
- [ ] Add `get_feature_config()` method
- [ ] Add `is_feature_enabled()` method
- [ ] Add `validate_features_config()` method
- [ ] Support default_features fallback
- [ ] Add validation logic cho feature config

#### 1.2 Update Config Schema
- [ ] Update `kidsplaza_thanhxuan.json` với feature config
- [ ] Add default_features section
- [ ] Validate JSON schema
- [ ] Document config structure

#### 1.3 Testing
- [ ] Unit tests cho config loading
- [ ] Test feature enable/disable logic
- [ ] Test default fallback
- [ ] Test validation

### Step 2: Counter Module (P8.2)

#### 2.1 Create Counter Module
- [ ] Create `src/modules/counter/__init__.py`
- [ ] Create `src/modules/counter/zone_counter.py`
- [ ] Implement `ZoneCounter` class
- [ ] Support polygon zones
- [ ] Support line zones
- [ ] Implement entering/exiting detection

#### 2.2 Zone Detection Logic
- [ ] Point-in-polygon algorithm
- [ ] Line crossing detection
- [ ] Track position history
- [ ] Direction detection
- [ ] Threshold-based counting (avoid double-counting)

#### 2.3 State Management
- [ ] Track last known position per track_id
- [ ] Maintain zone occupancy state
- [ ] Count increments/decrements
- [ ] Reset functionality

#### 2.4 Visualization
- [ ] Draw zones trên frame
- [ ] Draw zone labels
- [ ] Draw counts overlay
- [ ] Color coding (entering/exiting)

#### 2.5 Testing
- [ ] Unit tests cho zone detection
- [ ] Test polygon point-in-polygon
- [ ] Test line crossing
- [ ] Test count accuracy
- [ ] Test reset functionality

### Step 3: Integration (P8.3)

#### 3.1 Live Camera Integration
- [ ] Load counter config trong `LiveCameraProcessor.__init__()`
- [ ] Initialize `ZoneCounter` nếu enabled
- [ ] Update counter trong processing loop
- [ ] Display counts trên overlay
- [ ] Store counts vào database (nếu DB enabled)

#### 3.2 Overlay Enhancement
- [ ] Add counter display to overlay
- [ ] Show counts per zone
- [ ] Show total counts
- [ ] Format: `Zone: In: X | Out: Y | Total: Z`

#### 3.3 Database Integration (Optional)
- [ ] Add counter table schema
- [ ] Store zone counts per frame
- [ ] Aggregate counts per session
- [ ] Query counts by time range

#### 3.4 Testing
- [ ] Integration test với live camera
- [ ] Test counter accuracy
- [ ] Test display overlay
- [ ] Test database persistence (if enabled)

## 🔍 Key Design Decisions

### 1. Zone Definition

**Option A: Polygon Zones** (Recommended for bidirectional)
- Pros: Flexible, supports any shape
- Cons: More complex detection

**Option B: Line Zones** (Recommended for one-way)
- Pros: Simple, fast detection
- Cons: Limited to single direction

**Decision**: Support both types for flexibility.

### 2. Counting Algorithm

**Option A: Centroid-based**
- Use track centroid để detect zone entry/exit
- Simple, fast
- May miss partial entries

**Option B: BBox overlap**
- Use bounding box overlap với zone
- More accurate
- More complex computation

**Decision**: Start with centroid-based, add bbox overlap as option.

### 3. Double-counting Prevention

**Strategy**:
- Track last zone state per track_id
- Only increment khi state changes (inside → outside hoặc outside → inside)
- Use threshold để avoid flickering (e.g., must be inside for N frames)

### 4. Configuration Priority

**Priority Order**:
1. Channel-specific config (if exists)
2. Default features config (if exists)
3. System defaults (hardcoded)

## 📊 Acceptance Criteria

### Phase 8.1 (Configuration System)
- [ ] Config file có thể define features per channel
- [ ] System có thể load và validate config
- [ ] Features có thể enabled/disabled per channel
- [ ] Default features được apply khi channel config missing
- [ ] Validation errors được report clearly

### Phase 8.2 (Counter Module)
- [ ] ZoneCounter có thể detect polygon zones
- [ ] ZoneCounter có thể detect line zones
- [ ] Counts được track accurately (≥95% accuracy on test video)
- [ ] Reset functionality works
- [ ] Visualization renders zones correctly

### Phase 8.3 (Integration)
- [ ] Counter integrates với live camera pipeline
- [ ] Counts displayed trên overlay
- [ ] Counter chỉ chạy khi enabled trong config
- [ ] Performance impact ≤5% FPS reduction
- [ ] Database persistence works (if enabled)

## 🧪 Testing Strategy

### Unit Tests
- Config loading và validation
- Zone detection algorithms
- Counting logic
- State management
- Reset functionality

### Integration Tests
- Full pipeline với counter enabled
- Config per-channel application
- Count accuracy trên test video
- Performance impact measurement

### E2E Tests
- Test với real camera stream
- Test count accuracy với known scenarios
- Test config enable/disable
- Test multiple zones simultaneously

## 🚨 Risks & Mitigations

### Risk 1: Count Accuracy
**Mitigation**: 
- Use threshold-based detection to avoid flickering
- Track position history
- Validate với known test scenarios

### Risk 2: Performance Impact
**Mitigation**:
- Optimize zone detection algorithms
- Cache zone calculations
- Process only when counter enabled

### Risk 3: Configuration Complexity
**Mitigation**:
- Clear documentation
- Validation với helpful error messages
- Default values cho tất cả settings

### Risk 4: Zone Definition Difficulty
**Mitigation**:
- Provide helper tools để define zones
- Support visual zone definition
- Clear documentation với examples

## 📈 Success Metrics

- **Accuracy**: ≥95% count accuracy trên test video
- **Performance**: ≤5% FPS reduction khi counter enabled
- **Flexibility**: Support ≥5 zones per channel
- **Usability**: Config có thể setup trong <5 minutes

## 📝 Implementation Notes

### Default Feature Values

**System Defaults** (nếu không có config):
```python
DEFAULT_FEATURES = {
    "body_detection": {"enabled": True, "always": True},
    "tracking": {"enabled": True, "always": True},
    "reid": {"enabled": True, "always": False},
    "gender_classification": {"enabled": True, "always": False},
    "counter": {"enabled": True, "always": False}
}
```

### Zone Definition Format

**Polygon Zone (Absolute Coordinates)**:
```json
{
  "zone_id": "zone_1",
  "name": "Main Entrance",
  "type": "polygon",
  "coordinate_type": "absolute",
  "points": [[100, 100], [200, 100], [200, 200], [100, 200]],
  "direction": "bidirectional",
  "enter_threshold": 0.5,
  "exit_threshold": 0.5
}
```

**Polygon Zone (Percentage Coordinates)**:
```json
{
  "zone_id": "zone_1",
  "name": "Left Half",
  "type": "polygon",
  "coordinate_type": "percentage",
  "points": [[0, 0], [50, 0], [50, 100], [0, 100]],
  "direction": "bidirectional",
  "comment": "Adapts to any resolution - left half of screen"
}
```

**Line Zone (Absolute Coordinates)**:
```json
{
  "zone_id": "zone_2",
  "name": "Exit Line",
  "type": "line",
  "coordinate_type": "absolute",
  "start_point": [100, 300],
  "end_point": [500, 300],
  "direction": "one_way",
  "side": "above",
  "threshold": 0.5
}
```

**Line Zone (Percentage Coordinates)**:
```json
{
  "zone_id": "zone_2",
  "name": "Middle Line",
  "type": "line",
  "coordinate_type": "percentage",
  "start_point": [0, 50],
  "end_point": [100, 50],
  "direction": "one_way",
  "side": "above",
  "comment": "Horizontal line at 50% height - adapts to any resolution"
}
```

**Note**: 
- Use `coordinate_type: "percentage"` for zones that need to adapt to different camera resolutions
- Percentage values range from 0-100 (e.g., 50 = 50% of frame width/height)
- If `coordinate_type` is omitted, defaults to "absolute"

### Count Persistence

**In-Memory** (default):
- Counts reset khi restart process
- Suitable for real-time display

**Database** (optional):
- Store counts per zone per frame
- Aggregate per session
- Query historical counts

## 🔗 Related Files

- `src/modules/camera/camera_config.py` - Config loading
- `src/scripts/process_live_camera.py` - Main processing pipeline
- `input/cameras_config/kidsplaza_thanhxuan.json` - Camera configuration
- `docs/plan/PHASE_7_LIVE_CAMERA_PLAN.md` - Previous phase reference

## ✅ Exit Criteria

1. Configuration system allows per-channel feature enable/disable
2. Counter module detects zones và counts accurately
3. Integration với live camera pipeline complete
4. Counts displayed trên overlay
5. Tests passing với ≥95% accuracy
6. Performance impact ≤5% FPS reduction
7. Documentation complete
8. Code review passed

## 🎯 Next Steps After Phase 8

### Phase 9: Advanced Counter Features (Future)
- Multi-direction counting
- Zone analytics (dwell time, peak hours)
- Alert system (threshold-based)
- Historical reporting và dashboards

## 📚 References

- Point-in-polygon algorithms: [Ray casting algorithm](https://en.wikipedia.org/wiki/Point_in_polygon)
- Line crossing detection: [Cross product method](https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect)
- Previous phases: `docs/plan/PHASE_7_LIVE_CAMERA_PLAN.md`

