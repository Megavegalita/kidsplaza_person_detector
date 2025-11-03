# Age Display Issue Analysis & Fixes

**Date**: 2025-11-02  
**Status**: 🔧 Issues identified and fixes applied

## 🔍 Vấn Đề Phát Hiện

### 1. **Age Estimate = 0 không hiển thị** ❌
- **Symptom**: Age model estimate trả về `age=0` với `confidence=0.80`
- **Root Cause**: 
  - Model PyTorch (ResNet18/Hugging Face) có thể chưa được pretrain đúng cách
  - Output có thể là classification model mà chưa map đúng age ranges
  - Code check `if age > 0` nên không hiển thị age=0

### 2. **Channel 4 có nhiều tracks** ⚠️
- **Symptom**: Channel 4 có 9-10 tracks trong khi Channel 3 chỉ có 1 track
- **Possible Causes**:
  - NMS không hoạt động đúng ở channel 4
  - Face detection trả về nhiều duplicate faces
  - Tracker tạo nhiều tracks cho cùng một person

### 3. **Gender/Age logging chưa đủ chi tiết** 📝
- **Issue**: Không biết tại sao age=0 được estimate
- **Fix**: Thêm detailed logging

---

## ✅ Fixes Applied

### 1. **Age Display Logic** ✅
```python
# Updated: Allow age >= 0 but only display if > 0 and confidence > 0.3
if age >= 0 and age_conf > 0.3:
    self._track_id_to_age[t_id_int] = int(age)
    self._track_id_to_age_conf[t_id_int] = float(age_conf)
    if age > 0:
        logger.info("Gender/Age result stored: ...")
    else:
        logger.warning("Age=0 may indicate model issue: ...")
```

**Display Logic**:
```python
# Only display if age > 0 AND confidence > 0.3
if age is not None and age > 0 and age_conf is not None and age_conf > 0.3:
    display_det["age"] = age
    display_det["age_confidence"] = age_conf
```

### 2. **Enhanced Logging** ✅
- Added detailed logging for:
  - Gender/Age enqueuing: crop size, use_face flag
  - Age/Gender estimation results (OpenCV DNN or PyTorch)
  - Result storage with warnings for age=0

### 3. **Debug Information** ✅
- Log crop size và use_face classifier flag
- Log model type (OpenCV DNN vs PyTorch)
- Log confidence scores

---

## 🔍 Root Cause Analysis: Age = 0

### Possible Reasons:

1. **Model Not Pretrained Properly**:
   - Hugging Face model có thể không được load weights đúng cách
   - ResNet18 fallback có random weights (chưa pretrain)

2. **Classification Model Output**:
   - Nếu model là classification (age ranges), mapping có thể sai
   - Class 0 có thể map to age=0 thay vì actual age range

3. **Input Processing Issue**:
   - Face crop có thể quá nhỏ hoặc không đúng format
   - Preprocessing (resize, normalization) có thể sai

---

## 🎯 Recommendations

### 1. **Verify Age Model** 🔧
```python
# Test age model với known face image
age, conf = age_estimator.estimate(test_face_crop)
print(f"Age: {age}, Confidence: {conf}")
```

### 2. **Check Model Output** 🔍
- Add logging để xem raw model output
- Verify model architecture matches expected output

### 3. **Fix Model Loading** 📦
- Ensure Hugging Face models load pretrained weights correctly
- Check model config và output format

### 4. **Channel 4 Detection Issue** 📹
- Compare face detection results between channels
- Check NMS logic for overlapping faces
- Verify tracker matching logic

---

## 📊 Status After Fixes

✅ **Enhanced Logging**: Added detailed logs for debugging  
✅ **Age Display Logic**: Only show valid ages (> 0, conf > 0.3)  
⚠️ **Age Model**: Needs verification - currently returning age=0  
⚠️ **Channel 4**: Needs investigation - too many tracks

---

## 🚀 Next Steps

1. **Verify Age Model Output**:
   - Check raw model outputs
   - Test with known-age faces
   - Fix model loading if needed

2. **Investigate Channel 4**:
   - Compare detection results
   - Check NMS effectiveness
   - Review tracker matching

3. **Test with Real Data**:
   - Monitor logs after restart
   - Verify age display when valid ages are estimated
   - Check channel 4 track count

---

## 📝 Notes

- Age model có thể cần retrain hoặc load pretrained weights tốt hơn
- OpenCV DNN age/gender models (Caffe) đã failed to download (404)
- PyTorch models đang dùng Hugging Face pretrained nhưng có thể không hoạt động đúng
- Cần integrate pretrained model tốt hơn hoặc train custom model


