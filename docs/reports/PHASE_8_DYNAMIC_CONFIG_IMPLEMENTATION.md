# Phase 8: Dynamic Configuration Implementation

**Date**: 2025-11-03  
**Status**: ✅ Completed

---

## 🎯 Mục Tiêu

Chuyển đổi tất cả cấu hình hardcoded sang dynamic configuration được load từ camera config file, cho phép per-channel customization.

---

## ✅ Changes Made

### 1. Configuration Schema Enhancement

**Added to `default_features`**:
```json
{
  "body_detection": {
    "conf_threshold": 0.5,
    "detect_every_n": 4,
    "detect_resize": [480, 360],
    "model_path": "yolov8n.pt"
  },
  "tracking": {
    "max_age": 30,
    "min_hits": 2,
    "iou_threshold": 0.3,
    "ema_alpha": 0.5
  }
}
```

**Per-Channel Overrides**:
Mỗi channel có thể override bất kỳ config nào:
```json
{
  "channel_id": 1,
  "features": {
    "body_detection": {
      "conf_threshold": 0.5,
      "detect_every_n": 4
    },
    "tracking": {
      "max_age": 30,
      "iou_threshold": 0.4
    }
  }
}
```

### 2. Code Changes

**File**: `src/scripts/process_live_camera.py`

**Added**:
- Load `body_detection` config (conf_threshold, detect_every_n)
- Load `tracking` config (max_age, min_hits, iou_threshold, ema_alpha)
- Load `gender_classification` full config (all parameters)
- Per-channel config merging logic

**Removed Hardcoded Values**:
- ❌ `detect_every_n` hardcoded based on channel_id
- ✅ Now loaded from config with per-channel override support

**Priority Order**:
1. Command line arguments (highest priority)
2. Channel-specific config
3. Default features config
4. System defaults (lowest priority)

---

## 📊 Configuration Loading Priority

```
Command Line Args → Channel Config → Default Features → System Defaults
     (highest)                              (lowest)
```

### Example: `conf_threshold`
1. If `--conf-threshold` is set → use command line value
2. Else if channel config has `body_detection.conf_threshold` → use channel value
3. Else if default_features has `body_detection.conf_threshold` → use default value
4. Else → use system default (0.5)

---

## 🔧 Supported Configurations

### Body Detection
- `conf_threshold` - Detection confidence threshold
- `detect_every_n` - Detect every N frames
- `detect_resize` - Resize dimensions for detection
- `model_path` - Model file path

### Tracking
- `max_age` - Maximum age of tracks
- `min_hits` - Minimum hits for track confirmation
- `iou_threshold` - IoU threshold for matching
- `ema_alpha` - EMA smoothing alpha

### Re-ID
- `enabled` - Enable/disable Re-ID
- `every_k_frames` - Process every K frames
- `ttl_seconds` - Cache TTL
- `similarity_threshold` - Similarity threshold
- `aggregation_method` - Aggregation method
- `append_mode` - Append mode
- `max_embeddings` - Maximum embeddings

### Gender Classification
- `enabled` - Enable/disable gender classification
- `every_k_frames` - Process every K frames
- `model_type` - Model type (timm_mobile, etc.)
- `min_confidence` - Minimum confidence
- `female_min_confidence` - Female min confidence
- `male_min_confidence` - Male min confidence
- `voting_window` - Voting window size
- `max_per_frame` - Max per frame
- `adaptive_enabled` - Adaptive processing

### Counter
- `enabled` - Enable/disable counter
- `zones` - Zone configurations

---

## 📝 Current Channel Configurations

### Channel 1
- `detect_every_n`: 4
- `reid`: disabled (override)
- `counter`: enabled with 1 polygon zone

### Channel 2
- `detect_every_n`: 4 (default)
- `reid`: enabled (default)
- `counter`: enabled with 1 polygon zone

### Channel 3
- `detect_every_n`: 4 (default)
- `reid`: enabled (default)
- `counter`: enabled with 1 polygon zone

### Channel 4
- `detect_every_n`: 2 (override - more frequent detection)
- `reid`: enabled (default)
- `counter`: enabled with 2 zones (1 polygon + 1 line)

---

## ✅ Benefits

1. **Flexibility**: Mỗi channel có thể có config riêng
2. **Maintainability**: Tất cả configs ở một nơi (JSON file)
3. **No Code Changes**: Thay đổi config không cần rebuild code
4. **Testing**: Dễ test với different configs
5. **Deployment**: Có thể deploy configs khác nhau cho different environments

---

## 🧪 Testing

All configurations are verified:
- ✅ Config loading từ file
- ✅ Per-channel overrides working
- ✅ Defaults fallback working
- ✅ Priority order correct

---

## 📚 Usage Examples

### Override detect_every_n for Channel 4
```json
{
  "channel_id": 4,
  "features": {
    "body_detection": {
      "detect_every_n": 2
    }
  }
}
```

### Disable Re-ID for specific channel
```json
{
  "channel_id": 1,
  "features": {
    "reid": {
      "enabled": false
    }
  }
}
```

### Custom tracking parameters
```json
{
  "channel_id": 2,
  "features": {
    "tracking": {
      "iou_threshold": 0.4,
      "max_age": 50
    }
  }
}
```

---

## ✅ Status

**All hardcoded configurations have been moved to dynamic config loading.**

System now fully supports:
- ✅ Per-channel configuration overrides
- ✅ Default features with fallback
- ✅ Command line argument priority
- ✅ All features configurable

**Status**: ✅ **READY FOR PRODUCTION**

