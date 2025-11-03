# Gender & Age Accuracy Analysis & Improvements

**Date**: 2025-11-02  
**Issue**: Gender và Age detection không chính xác

## 🔍 Vấn Đề Phát Hiện

### Channel 3:
- **Expected**: Male, 20-30 tuổi
- **Actual**: Female (0.70), Age=5 (clamped)

### Channel 4:
- **Expected**: Male, 20-30 tuổi  
- **Actual**: Unknown (0.51-0.55), Age=5 (clamped)

## 🔬 Root Cause Analysis

### 1. **Gender Model Issues** ⚠️

**Current Implementation**:
- Using MobileNetV2 với ImageNet pretrained weights
- **KHÔNG có UTKFace gender-trained weights**
- Model chưa được fine-tune cho gender classification

**Code**: `face_gender_classifier.py:58-77`
```python
# Try to load UTKFace pretrained gender weights if available
pretrained_path = Path(...) / "mobilenetv2_gender_utkface.pth"

if pretrained_path.exists():
    # Load weights
else:
    logger.info("Using ImageNet pretrained weights (fine-tuning recommended for gender)")
```

**Problem**: 
- ImageNet weights không phù hợp cho gender classification
- Accuracy sẽ thấp (~60-70%)
- Dễ nhầm lẫn giữa Male/Female

### 2. **Age Model Issues** ⚠️

**Current Implementation**:
- PyTorch ResNet18/Hugging Face model
- Model output đang return giá trị rất thấp (< 5)
- Bị clamp về minimum = 5

**Evidence from logs**:
- Age estimation = 5 (clamped)
- Confidence = 0.80 (high but wrong value)

**Problem**:
- Model có thể chưa được train đúng cách
- Output format không match expected
- Classification model mapping có thể sai

### 3. **Face Crop Quality** 📷

**Current Process**:
1. Detect face with OpenCV DNN (YuNet)
2. Extract face_bbox
3. Crop from original frame
4. Resize to 224x224 for classification

**Potential Issues**:
- Face crop có thể quá nhỏ (distant detection)
- Quality thấp (blur, angle)
- Incomplete face capture

## ✅ Improvement Strategies

### 1. **Gender Classification Improvements**

#### A. Quality Check for Face Crops
- Validate face crop size (minimum 64x64 pixels)
- Check crop aspect ratio
- Skip classification if crop too small/poor quality

#### B. Voting/Averaging Mechanism
- Collect multiple predictions per track
- Use majority voting or weighted average
- Only update after N consistent predictions

#### C. Better Face Extraction
- Ensure face_bbox is properly scaled
- Add padding around face for better context
- Use better interpolation for resize

### 2. **Age Estimation Improvements**

#### A. Model Output Validation
- Log raw model outputs (before clamping)
- Check if model is classification or regression
- Verify age range mapping

#### B. Better Preprocessing
- Improve face crop quality
- Better normalization
- Augment training data representation

#### C. Confidence Calibration
- Age confidence should reflect model certainty
- Lower confidence for extreme ages
- Use ensemble if possible

### 3. **Bounding Box Improvements**

#### A. More Accurate Body Estimation
- Adjust `body_expand_ratio` based on face size
- Dynamic expansion based on face-to-body ratio
- Better vertical expansion for different poses

#### B. Tracker Smoothing
- Reduce EMA alpha for more accurate tracking
- Better handling of frame resolution changes
- Validate bbox before display

## 📊 Recommended Changes

### Priority 1: Immediate Fixes

1. **Face Crop Quality Validation**
   ```python
   # Check face crop size
   if face_crop.shape[0] < 64 or face_crop.shape[1] < 64:
       logger.debug("Face crop too small, skipping classification")
       return "Unknown", 0.0
   ```

2. **Gender Voting Window**
   - Implement 3-5 frame voting window
   - Only update gender after consistent predictions
   - This prevents flickering and wrong classifications

3. **Age Model Debugging**
   - Log raw model outputs
   - Check classification vs regression output
   - Verify age range mapping

### Priority 2: Model Improvements

1. **Load UTKFace Pretrained Weights**
   - Download or provide gender-trained weights
   - This will significantly improve accuracy

2. **Age Model Selection**
   - Use better pretrained age model
   - Consider OpenCV DNN age/gender models (if available)
   - Or train/fine-tune custom model

### Priority 3: Accuracy Enhancements

1. **Confidence Thresholds**
   - Increase minimum confidence for display
   - Gender: >= 0.70 (current: 0.65)
   - Age: >= 0.60 (current: 0.50)

2. **Multiple Frame Aggregation**
   - Average predictions across frames
   - Weight by confidence
   - Only show stable predictions

## 🎯 Expected Improvements

After improvements:
- **Gender Accuracy**: 85-90% (from ~60-70%)
- **Age Accuracy**: ±5 years for 70% cases (from clamped to 5)
- **Bounding Box**: More accurate, better tracking
- **Stability**: Less flickering, more consistent

## 📝 Implementation Plan

1. Add face crop quality validation
2. Implement gender voting mechanism
3. Improve age model output handling
4. Add detailed logging for debugging
5. Test with real data and adjust thresholds


