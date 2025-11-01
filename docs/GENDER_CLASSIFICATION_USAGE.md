# Gender Classification - Hướng Dẫn Sử Dụng

## Tổng Quan

Module gender classification đã được tích hợp vào pipeline, hỗ trợ 3 loại model:
1. `simple` - Simple CNN (random weights, không chính xác)
2. `timm_mobile` - MobileNetV3-Small (recommended, nhanh ~5-10ms)
3. `timm_efficient` - EfficientNet-B0 (cân bằng tốc độ/chính xác ~10-15ms)

## Sử Dụng

### Command Line

```bash
python src/scripts/process_video_file.py \
  "input/video/video.mp4" \
  --model yolov8n.pt \
  --output output/videos \
  --tracker-iou-threshold 0.4 \
  --tracker-ema-alpha 0.4 \
  --tracker-max-age 30 \
  --tracker-min-hits 3 \
  --reid-enable \
  --reid-every-k 20 \
  --gender-enable \
  --gender-every-k 30 \
  --gender-model-type timm_mobile
```

### Các Tham Số

- `--gender-enable`: Bật gender classification
- `--gender-every-k`: Phân loại mỗi K frame (default: 20)
- `--gender-model-type`: Loại model (`simple`, `timm_mobile`, `timm_efficient`)

## Kết Quả

### Overlay
Hiển thị gender counts: `Gender M/F/U: 10/15/5`

### JSON Report
```json
{
  "summary": {
    "unique_tracks_total": 30,
    "gender_counts_total": {
      "M": 10,
      "F": 15,
      "Unknown": 5
    }
  },
  "frame_results": [
    {
      "frame_number": 1,
      "gender_counts": {"M": 0, "F": 0, "Unknown": 0},
      "detections": [
        {
          "track_id": 1,
          "gender": "M",
          "gender_confidence": 0.85
        }
      ]
    }
  ]
}
```

## Lưu Ý

⚠️ **Current models chưa fine-tuned** cho gender classification
- `simple`: Random weights (không chính xác)
- `timm_mobile`: ImageNet-pretrained (chưa phù hợp cho gender)
- `timm_efficient`: ImageNet-pretrained (chưa phù hợp cho gender)

✅ **Đề xuất**: Fine-tune MobileNetV3 trên gender dataset trước khi production

## Fine-tuning Plan

### Step 1: Prepare Dataset
- Download UTKFace hoặc Adience dataset
- Crop upper-body person regions
- Labels: M/F

### Step 2: Train Model
```python
import timm
import torch

# Load pretrained
model = timm.create_model('mobilenetv3_small_100', pretrained=True, num_classes=2)

# Fine-tune on gender dataset
# ...

# Save model
torch.save(model.state_dict(), 'models/gender_mobilenetv3.pth')
```

### Step 3: Update GenderClassifier
```python
# Load fine-tuned model
model.load_state_dict(torch.load('models/gender_mobilenetv3.pth'))
```

## Monitoring

Log hiển thị gender counts mỗi 100 frames:
```
INFO - Gender counts (cumulative) at frame 300: M=5, F=8, U=2
INFO - Gender counts (cumulative) at frame 600: M=12, F=15, U=3
```

