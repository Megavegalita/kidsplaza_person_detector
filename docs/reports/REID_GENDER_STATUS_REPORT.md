# Re-ID và Gender Detection Status Report

**Date**: 2025-11-02  
**Preset Used**: `gender_main_v1`

## Tổng Quan

### ✅ RE-ID (Re-Identification): **ĐÃ BẬT**

#### Configuration
- **Preset Setting**: `reid_enable: True`
- **Code Status**: Được kích hoạt qua preset
- **Components Initialized**:
  - ✅ ReIDCache: Connected to Redis
  - ✅ ReIDEmbedder: Initialized (target_size=(64, 128))

#### Activation Logic
```python
# Trong process_live_camera.py:585-608
if (
    len(detections) > 0  # Chỉ chạy khi có detections
    and should_detect      # Chỉ trên detection frames
    and self.reid_enable   # ✅ Đã bật qua preset
    and self.reid_embedder is not None
    and self.reid_cache is not None
):
    integrate_reid_for_tracks(...)
```

#### Settings (từ preset `gender_main_v1`)
- `reid_enable`: True
- `reid_every_k`: 20 frames
- `reid_ttl_seconds`: 60 seconds
- `reid_similarity_threshold`: 0.65
- `reid_aggregation_method`: "avg_sim"
- `reid_append_mode`: True
- `reid_max_embeddings`: 3

#### Current Status
- ✅ Re-ID đang hoạt động
- ✅ Chỉ chạy khi có face detections (optimization)
- ✅ Redis cache đang được sử dụng

---

### ❌ GENDER DETECTION: **ĐÃ TẮT** (Force Disabled)

#### Configuration
- **Preset Setting**: `gender_enable: True` (trong preset)
- **Code Status**: `self.gender_enable = False` ❌ (Force disabled)
- **Reason**: "TEMPORARILY DISABLED for testing face detection"

#### Disabled Location
```python
# Trong process_live_camera.py:223-233
# Initialize Gender components (TEMPORARILY DISABLED for testing face detection)
# Gender classification requires TensorFlow which has dependency conflicts
self.gender_enable = False  # Force disable for now
self.gender_classifier = None  # Disabled
logger.info("Gender classification disabled - testing face detection only")
```

#### Processing Logic
```python
# Trong process_live_camera.py:616-631
# Gender classification (TEMPORARILY DISABLED)
# if (
#     self.gender_enable
#     and self.gender_classifier is not None
#     and self.gender_worker is not None
# ):
#     self._process_gender_classification(...)
```

#### Log Confirmation
```
2025-11-02 12:42:13,629 - __main__ - INFO - Gender classification disabled - testing face detection only
```

#### Settings (từ preset, nhưng không được sử dụng)
- `gender_enable`: True (trong preset, nhưng bị override thành False)
- `gender_every_k`: 15 frames
- `gender_max_per_frame`: 4
- `gender_model_type`: "timm_mobile"
- `gender_min_confidence`: 0.50
- `gender_voting_window`: 35

#### Current Status
- ❌ Gender detection KHÔNG hoạt động
- ❌ Code bị comment và force disable
- ❌ Lý do: Dependency conflicts với TensorFlow (đã chuyển sang OpenCV DNN)

---

## Kết Luận

| Component | Preset Config | Code Status | Đang Hoạt Động |
|-----------|---------------|-------------|----------------|
| **Re-ID** | ✅ True | ✅ Enabled | ✅ **CÓ** |
| **Gender** | ✅ True | ❌ False (Force disabled) | ❌ **KHÔNG** |

### Recommendations

1. **Re-ID**: Đang hoạt động tốt, không cần thay đổi

2. **Gender Detection**: 
   - Hiện tại bị force disable để test face detection
   - Cần enable lại nếu muốn sử dụng gender classification
   - Yêu cầu: Resolve TensorFlow dependencies hoặc sử dụng model không cần TensorFlow

### Để Bật Lại Gender Detection

1. Sửa code trong `process_live_camera.py:225`:
   ```python
   # Từ:
   self.gender_enable = False  # Force disable for now
   
   # Thành:
   self.gender_enable = gender_enable  # Use parameter value
   ```

2. Uncomment code xử lý gender ở dòng 616-631

3. Đảm bảo dependencies (TensorFlow hoặc alternative) đã được cài đặt

4. Khởi động lại các channels


