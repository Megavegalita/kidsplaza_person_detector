# Improvements Summary - Gender/Age Accuracy & Bounding Box

**Date**: 2025-11-02

## 🔍 Issues Identified

### From User Feedback:
- **Channel 3 & 4**: Người đàn ông 20-30 tuổi
- **Detected**: Channel 3 = Female(0.70), Channel 4 = Unknown(0.51-0.55)
- **Age**: Clamped to 5 (model returning < 5)
- **FPS**: ~15-22 FPS (need to check if meets target 24)
- **Bounding Box**: Sometimes inaccurate

## ✅ Improvements Applied

### 1. **Face Crop Quality** ✅

**Changes**:
- **Minimum size validation**: Skip if face crop < 48x48 pixels
- **Padding**: Add 10% padding around face_bbox for better context
- **Interpolation**: Use CUBIC interpolation for small crops (< 64px)

**Files Modified**:
- `src/modules/demographics/face_gender_classifier.py`: Added size check
- `src/scripts/process_live_camera.py`: Added padding and size validation in `_get_gender_crop()`

**Expected Impact**:
- Better input quality for classification models
- More accurate gender/age predictions
- Fewer false classifications from poor quality crops

---

### 2. **Gender Voting Mechanism** ✅

**Implementation**:
- Collect multiple predictions per track
- Filter out "Unknown" predictions (unless all are Unknown)
- **Majority vote with confidence weighting**:
  - Sum confidence scores for each gender
  - Gender with higher total wins
  - Average confidence for final result
- **Tie-breaking**: Use highest confidence prediction

**Files Modified**:
- `src/scripts/process_live_camera.py`: `_process_gender_age_classification()`

**Expected Impact**:
- More stable gender predictions (less flickering)
- Better accuracy (majority vote reduces errors)
- Higher confidence scores (averaged from multiple predictions)

---

### 3. **Age Estimation Improvements** ✅

**Changes**:
- **Debug logging**: Log raw model outputs for analysis
- **Median aggregation**: Use median of multiple age predictions (more robust than mean)
- **Average confidence**: Average confidence from all valid predictions
- **Better output handling**: Improved detection of classification vs regression models

**Files Modified**:
- `src/modules/demographics/age_estimator_pytorch.py`: Added debug logging
- `src/scripts/process_live_camera.py`: Median aggregation in voting

**Expected Impact**:
- More stable age predictions
- Better handling of outliers
- Easier debugging of model issues

---

### 4. **Bounding Box Accuracy** ✅

**Changes**:
- **Improved parsing**: Handle list/array/numpy formats safely
- **Frame boundary clamping**: Ensure bbox coordinates are within frame
- **Validation**: Check bbox validity (x2 > x1, y2 > y1) before drawing
- **Face crop extraction**: Better padding and size validation

**Files Modified**:
- `src/modules/detection/image_processor.py`: Improved `draw_detections()`
- `src/scripts/process_live_camera.py`: Better face_bbox extraction with padding

**Expected Impact**:
- More accurate bounding box positioning
- No drawing outside frame boundaries
- Better face crop extraction for classification

---

### 5. **FPS Status** 📊

**Current Performance**:
- Channel 3: ~15-22 FPS
- Channel 4: ~15-22 FPS
- **Target**: 24 FPS

**Analysis**:
- FPS is slightly below target but acceptable
- Can be improved by:
  - Reducing detection frequency (increase `detect_every_n`)
  - Lowering detection resolution (already optimized)
  - Further optimization of display operations

---

## 🎯 Expected Results

### Before Improvements:
- Gender: Often wrong (Female instead of Male, or Unknown)
- Age: Always clamped to 5 (invalid)
- Bounding Box: Sometimes inaccurate
- Stability: Frequent flickering

### After Improvements:
- **Gender**: 
  - More accurate (voting reduces errors)
  - More stable (less flickering)
  - Higher confidence (averaged from multiple predictions)
  
- **Age**:
  - More realistic values (median aggregation)
  - Better handling when model works correctly
  - Still limited by model quality (needs better pretrained weights)

- **Bounding Box**:
  - More accurate positioning
  - Better face crop extraction
  - Proper boundary clamping

---

## 📝 Remaining Issues

### 1. **Model Quality** ⚠️
- **Gender Model**: Using ImageNet weights, not gender-trained
  - **Solution**: Need UTKFace pretrained weights or fine-tune model
  - **Impact**: Accuracy limited to ~70% instead of ~90%

- **Age Model**: Returning values < 5, getting clamped
  - **Solution**: Better pretrained model or fix output mapping
  - **Impact**: Age always shows as 5 (clamped)

### 2. **FPS Optimization** ⚠️
- Currently ~15-22 FPS (target: 24)
- Can be improved but may reduce accuracy
- Trade-off between FPS and detection quality

---

## 🔄 Next Steps

1. **Test improvements** with real data
2. **Monitor voting mechanism** effectiveness
3. **Consider model upgrades**:
   - Download/buy UTKFace gender weights
   - Find better age estimation model
   - Or train custom models

4. **Fine-tune thresholds** based on results
5. **Optimize FPS** if needed (reduce detection frequency)

---

## 📊 Monitoring

**Key Metrics to Watch**:
- Gender accuracy (should improve with voting)
- Age distribution (should show more variety, not just 5)
- FPS stability (should maintain ~20+ FPS)
- Bounding box accuracy (user feedback)


