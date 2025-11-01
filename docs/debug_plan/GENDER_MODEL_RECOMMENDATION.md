# Đề Xuất Model cho Gender Classification

## Phân Tích Yêu Cầu

### Requirements
1. **Input**: Person crops (upper-body) từ video stream
2. **Output**: Gender (M/F/Unknown) với confidence
3. **Constraints**: 
   - Latency: < 20ms per crop (target 5-10ms)
   - Accuracy: > 85% trên person crops
   - Model size: < 50MB for easy deployment
   - Device: Mac M4 với MPS

### Current Pipeline
- Detection: YOLOv8n (nhanh, 17ms)
- Tracking: IoU-based với EMA
- Re-ID: Lightweight (17ms)
- **Target**: Gender classification < 10ms để không làm bottleneck

## Đề Xuất Models

### Option 1: MobileNetV3-Small (Recommended) ⭐
**Timing**: timm mobile
**Pros**:
- ✅ Very fast (~5-10ms per crop)
- ✅ Small model (~13MB)
- ✅ Pretrained on ImageNet
- ✅ Good accuracy cho face/person classification

**Cons**:
- ⚠️ Chưa fine-tuned cho gender (cần fine-tune)

**Setup**:
```python
model = timm.create_model('mobilenetv3_small_100', pretrained=True, num_classes=2)
```

### Option 2: EfficientNet-B0
**Timing**: timm efficient
**Pros**:
- ✅ Good balance accuracy/speed (~10-15ms)
- ✅ Better accuracy than MobileNetV3

**Cons**:
- ⚠️ Slower than MobileNetV3
- ⚠️ Chưa fine-tuned cho gender

**Setup**:
```python
model = timm.create_model('efficientnet_b0', pretrained=True, num_classes=2)
```

### Option 3: Simple CNN (Current)
**Status**: Đã implemented
**Pros**:
- ✅ Very fast (~2-5ms)
- ✅ No dependencies

**Cons**:
- ❌ **Not pretrained** - random weights
- ❌ Low accuracy (~50% random)

**Conclusion**: Not suitable for production

## Recommendation: Fine-tune MobileNetV3-Small

### Strategy
1. Download **pretrained MobileNetV3-Small** từ timm
2. Replace last layer: 1000 classes → 2 classes (M/F)
3. Fine-tune trên **gender classification dataset**:
   - Datasets: UTKFace, Adience, CelebA
   - Training: 5-10 epochs on upper-body person crops
4. Export final model for production

### Implementation Plan

#### Step 1: Download Pretrained Model
```bash
# Already have timm installed
python -c "import timm; model = timm.create_model('mobilenetv3_small_100', pretrained=True)"
```

#### Step 2: Fine-tune for Gender
```python
# Create fine-tuning script
# datasets/gender_training.py

import torch
import timm
from torch.utils.data import DataLoader
from torchvision import transforms

# Load pretrained model
model = timm.create_model('mobilenetv3_small_100', pretrained=True, num_classes=2)

# Fine-tune last layers
# Train on gender dataset
# ...

# Save model
torch.save(model.state_dict(), 'models/gender_mobilenetv3.pth')
```

#### Step 3: Integrate Fine-tuned Model
```python
# In gender_classifier.py
model.load_state_dict(torch.load('models/gender_mobilenetv3.pth'))
model.eval()
```

## Current Status

### Implemented
- ✅ **Module structure**: `GenderClassifier` class
- ✅ **Timm integration**: Ready for `timm_mobile` và `timm_efficient`
- ✅ **Pipeline integration**: CLI flags, overlay, JSON
- ✅ **Majority voting**: Stability logic

### Missing
- ❌ **Fine-tuned model**: Need to train hoặc download pretrained gender model
- ❌ **Gender dataset**: Need training data

## Alternative: Use Existing Pretrained Gender Models

### Option A: Download from Hugging Face
Search for pretrained gender classification models:
- Keywords: "gender classification", "gender prediction", "face gender"
- Format: PyTorch checkpoint
- Size: Prefer < 50MB

### Option B: Use Simple Rules
If no suitable model available:
```python
# Temporarily use a simple heuristic
def classify_gender(crop):
    h, w = crop.shape[:2]
    aspect_ratio = h / w
    # Heuristic based on aspect ratio (not accurate but fast)
    if aspect_ratio > 1.3:
        return 'F', 0.6
    else:
        return 'M', 0.6
```

## Next Actions

1. **Immediate**: Use ImageNet-pretrained MobileNetV3 với simple random outputs (not accurate)
2. **Short-term**: Fine-tune MobileNetV3 trên gender dataset
3. **Long-term**: Deploy production-ready gender model

## Conclusion

✅ **Best option**: Fine-tune MobileNetV3-Small cho gender classification
✅ **Current status**: Module ready, waiting for trained model
✅ **Integration**: Complete và tested
⚠️ **Production**: Cần pretrained gender model để accuracy tốt

