# Landmark Validation Fix - Reduce Motorcycle False Positives

**Date**: 2025-11-03  
**Status**: ✅ Applied

---

## 🔍 VẤN ĐỀ

### **Channel 1: False Positive Vẫn Xảy Ra**
- Threshold 0.55 vẫn không đủ (confidence 0.75 pass qua)
- Motorcycle patterns được detect thành face với confidence cao
- YuNet model thực sự detect "face" từ motorcycle patterns

**Evidence**:
- Display: "person: 0.75 | Female(1.00)" trên motorcycle
- Logs: "Found 1 raw faces from YuNet detector" liên tục
- Confidence 0.75 > threshold 0.55 → pass qua

---

## ✅ GIẢI PHÁP: LANDMARK VALIDATION

### **YuNet Cung Cấp Face Landmarks**
YuNet detect faces và cung cấp landmarks:
- Right eye (x_re, y_re)
- Left eye (x_le, y_le)
- Nose tip (x_nt, y_nt)
- Mouth corners (x_rcm, y_rcm, x_lcm, y_lcm)

**Key Insight**: Motorcycles và objects không có face landmarks hợp lý!

---

## 🔧 IMPLEMENTATION

### **1. Landmark Validation Function**

```python
def _validate_face_landmarks(
    self, right_eye_x, right_eye_y,
    left_eye_x, left_eye_y,
    nose_tip_x, nose_tip_y,
    mouth_right_x, mouth_right_y,
    mouth_left_x, mouth_left_y,
    face_x, face_y, face_w, face_h
) -> bool:
    """Validate landmark geometry to reject false positives."""
    
    # 1. Check landmarks within face bbox
    # 2. Eyes at same height (difference < 20% face height)
    # 3. Nose below eyes, above mouth
    # 4. Mouth below nose
    # 5. Vertical ordering: eyes > nose > mouth
    # 6. Eyes symmetric (similar distance from center)
```

**Validation Rules**:
1. ✅ **Landmarks within bbox**: All landmarks must be within face bounding box (with 20% tolerance)
2. ✅ **Eyes aligned**: Right and left eye at similar height (difference < 20% of face height)
3. ✅ **Nose position**: Nose between eyes horizontally, below them vertically
4. ✅ **Mouth position**: Mouth below nose
5. ✅ **Vertical order**: eyes > nose > mouth (strict ordering)
6. ✅ **Symmetry**: Eyes roughly symmetric (offset difference < 25% of face width)

### **2. Integration**

```python
# After confidence check
confidence = float(face[14])
if confidence < self.min_detection_confidence:
    continue

# NEW: Landmark validation
landmark_valid = self._validate_face_landmarks(...)
if not landmark_valid:
    logger.info("Rejected face: invalid landmark geometry")
    continue
```

### **3. Threshold Tuning**

```python
# Channel 1: Increased threshold + landmark validation
if channel_id == 1:
    face_confidence_threshold = max(0.60, conf_threshold * 1.2)  # 0.60
```

---

## 📊 EXPECTED IMPACT

### **Before**:
- ❌ Confidence 0.75 pass qua threshold 0.55
- ❌ Motorcycle detected as person
- ❌ No landmark validation

### **After**:
- ✅ Confidence 0.60 threshold (higher)
- ✅ Landmark validation rejects motorcycles (no valid eyes/nose/mouth)
- ✅ Only real faces with valid landmarks pass

---

## 🎯 WHY THIS WORKS

### **Motorcycle Patterns vs Real Faces**:

**Motorcycle**:
- Patterns giống face (headlight = eyes?) nhưng:
  - ❌ Không có landmarks hợp lý
  - ❌ "Eyes" không aligned
  - ❌ Không có nose/mouth thật
  - ❌ Landmark geometry không hợp lý

**Real Face**:
- ✅ Eyes aligned horizontally
- ✅ Nose below eyes, centered
- ✅ Mouth below nose
- ✅ Valid geometric relationships
- ✅ Landmarks within face bbox

**Landmark validation sẽ reject motorcycles vì chúng không có valid landmark structure!**

---

## 📝 FILES MODIFIED

1. **`src/modules/detection/face_detector_opencv.py`**:
   - Added `_validate_face_landmarks()` method
   - Integrated landmark validation after confidence check
   - Validates geometric relationships of landmarks

2. **`src/scripts/process_live_camera.py`**:
   - Increased Channel 1 threshold: 0.55 → 0.60
   - Added logging for landmark validation

---

## ✅ VERIFICATION

### **Expected Behavior**:
- ✅ Channel 1: Motorcycle false positives rejected by landmark validation
- ✅ Logs show: "Rejected face: invalid landmark geometry"
- ✅ Only real faces with valid landmarks pass

### **Monitoring**:
- Check logs for "Rejected face: invalid landmark geometry"
- Monitor false positive rate (should drop significantly)
- Verify real faces still pass validation

---

**Status**: Applied ✅ | Testing in progress 🔄

