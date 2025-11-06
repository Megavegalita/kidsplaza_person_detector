# Comprehensive Model Analysis Report

**Date**: 2025-11-02  
**Channels Analyzed**: 1, 2, 3, 4  
**Analysis Duration**: ~2 minutes runtime

---

## 🔍 EXECUTIVE SUMMARY

### Critical Issues Identified:

1. **❌ Age Model**: All Hugging Face models FAILED to load
   - Fallback to torchvision ResNet18 (ImageNet weights only)
   - Age always = 3 (clamped minimum)
   - **Root Cause**: Model architecture mismatch or transformers version issue

2. **⚠️ Gender Model**: Working but low confidence
   - Most predictions = "Unknown" (conf 0.55-0.66, below 0.65 threshold)
   - Some Male predictions (conf 0.65-0.66, barely above threshold)
   - **Issue**: Model accuracy or face crop quality

3. **✅ Detection**: Working well
   - Face detection active
   - Tracks being created
   - FPS acceptable (16-22 FPS)

4. **✅ Bounding Box**: No major errors in logs
   - Validation working
   - Scaling logic present

---

## 📊 DETAILED ANALYSIS

### 1. Age Model Loading ❌ FAILED

**Expected Models** (Priority Order):
1. prithivMLmods/facial-age-detection (8-class, 82.25% accuracy) ⭐
2. LisanneH/AgeEstimation (regression, MAE 5.2)
3. fanclan/age-gender-model (combined)
4. Sharris/age_detection_regression
5. torchvision_resnet18 (fallback) ← **Currently Using**

**Actual Status**:
```
All Hugging Face models failed to load, using torchvision fallback
No pretrained age weights found
Model uses ImageNet weights only
Age predictions will be approximate
```

**Error Analysis**:
- Model: `prithivMLmods/facial-age-detection`
- Error: `ValueError: Could not find SiglipForImageClassification`
- **Root Cause**: 
  - Model uses SigLIP architecture
  - Transformers version may not support SigLIP
  - Or model needs `trust_remote_code=True` and specific transformers version

**Impact**:
- Age always clamped to 3 (minimum)
- No valid age predictions
- Model using random/ImageNet weights (not age-trained)

**Age Predictions**:
- All predictions: `age=3(0.80)`
- This is the clamped minimum, not real prediction
- Confidence = 0.80 is default/estimated, not real

---

### 2. Gender Model Status ⚠️ PARTIALLY WORKING

**Model**: FaceGenderClassifier (MobileNetV2, PyTorch)
**Device**: MPS (Apple Silicon)
**Status**: ✅ Initialized successfully

**Predictions Analysis** (Channel 3 & 4):

**Distribution**:
- Unknown: ~70% (conf 0.55-0.66, mostly below 0.65 threshold)
- Male: ~25% (conf 0.65-0.78, at/barely above threshold)
- Female: ~5% (conf 0.70, above threshold)

**Issues**:
1. **Low Confidence**: Most predictions < 0.65 threshold
   - Many "Unknown" results
   - Threshold was 0.65, now 0.60 (should help)

2. **Model Accuracy**: MobileNetV2 with ImageNet weights (not gender-trained)
   - May need UTKFace pretrained weights
   - Or better face crop quality

3. **Voting**: Only 1 prediction per track in most cases
   - Voting mechanism not collecting enough predictions
   - Need more predictions for stable results

**Sample Predictions**:
```
track_id=1: Unknown(0.60-0.66) - Most common
track_id=1: M(0.65-0.78) - Sometimes
```

---

### 3. Detection Performance ✅ GOOD

**Face Detection**:
- Method: OpenCV DNN YuNet
- Status: ✅ Working
- Channels 3 & 4: Detecting faces
- Channel 3: 0 persons (no one present or too far)
- Channel 4: 1-3 persons detected consistently

**Tracking**:
- Channel 3: 1 track
- Channel 4: 3 tracks (initially had 11, now stable at 3)
- **Issue**: Channel 4 had too many tracks initially (11) → Now stable (3)

**FPS**:
- Channel 1: ~16.4 FPS (below target 24)
- Channel 3: ~22.6 FPS (near target 24) ✅
- Channel 4: ~22.6 FPS (near target 24) ✅
- **Note**: Running 4 channels simultaneously, so lower FPS is expected

---

### 4. Bounding Box Status ✅ NO MAJOR ERRORS

**Validation**:
- No "Invalid bbox" errors in recent logs
- No "Suspiciously large bbox" warnings
- Clamping logic working

**Scaling**:
- Scale factors calculated: `scale_w`, `scale_h`
- Bboxes scaled back in `_detect_frame_async`
- Validation after clamping

**Possible Issues** (from user feedback):
- May be visual positioning (not accuracy)
- May need adjustment of `body_expand_ratio`
- May be frame resolution mismatch

---

### 5. Display Logic Status ⚠️ UNCLEAR

**Gender Display**:
- Threshold: >= 0.60 (updated from 0.65)
- Should display: M(0.65-0.78), F(0.70)
- May not display: Unknown(0.55-0.64)

**Age Display**:
- Threshold: >= 3, conf > 0.4
- Stored: age=3(0.80)
- Should display: Age:1-8 (from age=3)
- **Issue**: age=3 may not be displayed if user expects realistic ages

**Voting Results**:
- Most stored as: "voted from 1 predictions"
- Voting not effective (need multiple predictions)

---

## 🎯 ROOT CAUSES

### Primary Issue: Age Model ❌

**Problem**: All Hugging Face age models fail to load
- Error: SigLIP architecture not found
- Fallback: torchvision ResNet18 (ImageNet weights)
- Result: Age always = 3 (clamped)

**Solution Needed**:
1. Fix transformers/SigLIP compatibility
2. Or find alternative age models
3. Or manually download model weights

### Secondary Issue: Gender Accuracy ⚠️

**Problem**: Low confidence predictions
- Model: MobileNetV2 (ImageNet weights, not gender-trained)
- Result: Many "Unknown" predictions
- Threshold adjustment helps but doesn't fix accuracy

**Solution Needed**:
1. Use UTKFace pretrained gender weights
2. Improve face crop quality
3. Collect more predictions for voting

---

## 🔧 RECOMMENDATIONS

### Priority 1: Fix Age Model ⚠️ CRITICAL

1. **Check Transformers Version**:
   - May need newer version for SigLIP support
   - Or downgrade if compatibility issue

2. **Alternative Models**:
   - Try LisanneH/AgeEstimation (regression, may work)
   - Or use OpenCV DNN age models (manual download)
   - Or train custom model on AFAD dataset

3. **Manual Download**:
   - Download prithivMLmods model manually
   - Place in local directory
   - Load from file instead of Hugging Face

### Priority 2: Improve Gender Accuracy

1. **Face Crop Quality**:
   - Ensure minimum size (48x48) - ✅ Already implemented
   - Add padding - ✅ Already implemented
   - Check if crops are clear enough

2. **Model Weights**:
   - Find/download UTKFace pretrained MobileNetV2 gender weights
   - Or fine-tune on gender dataset

3. **Voting Mechanism**:
   - Collect more predictions per track
   - Increase collection window
   - Use weighted average

### Priority 3: Bounding Box Accuracy

1. **Verify Scaling**:
   - Add detailed logging for scale factors
   - Check if bbox coordinates match display resolution

2. **Body Estimation**:
   - Adjust `body_expand_ratio` if needed
   - Test different expansion values

3. **Visual Verification**:
   - Compare displayed bbox with actual person position
   - Adjust if consistently off

---

## 📈 CURRENT METRICS

### Channel 3:
- FPS: 22.6 ✅
- Tracks: 1
- Gender: Mostly Unknown (0.55-0.66)
- Age: 3 (invalid, clamped)

### Channel 4:
- FPS: 22.6 ✅
- Tracks: 3 (was 11, now stable)
- Gender: Mix of Unknown/Male
- Age: 3 (invalid, clamped)
- Detections: 1-3 persons

---

## 🚀 NEXT STEPS

1. **Fix Age Model Loading** (Critical)
   - Debug SigLIP architecture issue
   - Try alternative models
   - Or manual model download

2. **Improve Gender Accuracy**
   - Get UTKFace pretrained weights
   - Or improve face crop quality
   - Better voting mechanism

3. **Verify Display**
   - Test with actual persons
   - Check if gender/age show on overlay
   - Verify bounding box positioning

4. **Optimize Performance**
   - FPS is acceptable but can improve
   - Further optimization if needed

---

## 📝 CONCLUSION

**Working Well**:
- ✅ Face detection
- ✅ Tracking (mostly)
- ✅ FPS (near target)
- ✅ Multi-threading

**Needs Fix**:
- ❌ Age model (all Hugging Face models failed)
- ⚠️ Gender accuracy (low confidence)
- ⚠️ Display verification (need to check visually)

**Critical Action**: Fix age model loading first - this is blocking all age predictions.


