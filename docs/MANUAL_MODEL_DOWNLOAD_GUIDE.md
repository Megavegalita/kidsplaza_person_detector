# Hướng Dẫn Tải Model Thủ Công (Manual Download Guide)

**Date**: 2025-11-02  
**Purpose**: Tải các model files cần thiết cho age/gender detection

---

## 📁 CẤU TRÚC THƯ MỤC

```
models/
├── age_gender_opencv/          # OpenCV DNN models (Caffe format)
│   ├── age_deploy.prototxt
│   ├── age_net.caffemodel
│   ├── gender_deploy.prototxt
│   └── gender_net.caffemodel
├── age_estimator_hf/           # Hugging Face models (optional, if auto-download fails)
│   ├── prithivMLmods_facial_age_detection/
│   ├── LisanneH_AgeEstimation/
│   ├── fanclan_age_gender_model/
│   └── Sharris_age_detection_regression/
└── age_resnet18_pytorch.pth   # PyTorch pretrained weights (optional)
```

---

## 🎯 PRIORITY 1: OpenCV DNN Models (QUAN TRỌNG NHẤT)

### Vị trí: `models/age_gender_opencv/`

Các file cần tải:

### 1. Age Model Files

**File 1: `age_deploy.prototxt`**
- **URL**: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt
- **Backup URL**: https://github.com/opencv/opencv/blob/4.x/samples/dnn/age_deploy.prototxt
- **Download**: Click "Raw" button on GitHub or use `wget`/`curl`
- **Vị trí**: `models/age_gender_opencv/age_deploy.prototxt`

**File 2: `age_net.caffemodel`**
- **URL**: https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel
- **Backup URL**: 
  - https://drive.google.com/file/d/1_LbF8ssp0cWL3ELl8K6wVoD8vq-_YJ1B/view?usp=sharing
  - https://github.com/opencv/opencv_extra/blob/4.x/testdata/dnn/age_net.caffemodel
- **Download**: Click "Download" on GitHub or use Google Drive link
- **Vị trí**: `models/age_gender_opencv/age_net.caffemodel`
- **Kích thước**: ~43 MB

### 2. Gender Model Files

**File 3: `gender_deploy.prototxt`**
- **URL**: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt
- **Backup URL**: https://github.com/opencv/opencv/blob/4.x/samples/dnn/gender_deploy.prototxt
- **Download**: Click "Raw" button on GitHub
- **Vị trí**: `models/age_gender_opencv/gender_deploy.prototxt`

**File 4: `gender_net.caffemodel`**
- **URL**: https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel
- **Backup URL**:
  - https://drive.google.com/file/d/1Lnt6a4F-xPTXTBrHAuHqKVq_8zWdZKTj/view?usp=sharing
  - https://github.com/opencv/opencv_extra/blob/4.x/testdata/dnn/gender_net.caffemodel
- **Download**: Click "Download" on GitHub or use Google Drive link
- **Vị trí**: `models/age_gender_opencv/gender_net.caffemodel`
- **Kích thước**: ~3.4 MB

---

## 🔧 PRIORITY 2: Hugging Face Models (OPTIONAL)

### Nếu OpenCV models hoạt động tốt, có thể bỏ qua phần này

Các model này sẽ được tự động tải vào cache của Hugging Face nếu có thể. Nếu muốn tải thủ công:

### 1. prithivMLmods/facial-age-detection
- **Hugging Face**: https://huggingface.co/prithivMLmods/facial-age-detection
- **Tải**: Click "Files and versions" → Download repository
- **Vị trí cache**: `~/.cache/huggingface/hub/models--prithivMLmods--facial-age-detection/`
- **Hoặc**: Tạo `models/age_estimator_hf/prithivMLmods_facial_age_detection/`

### 2. LisanneH/AgeEstimation
- **Hugging Face**: https://huggingface.co/LisanneH/AgeEstimation
- **Tải**: Click "Files and versions" → Download repository
- **Vị trí cache**: `~/.cache/huggingface/hub/models--LisanneH--AgeEstimation/`

### 3. fanclan/age-gender-model
- **Hugging Face**: https://huggingface.co/fanclan/age-gender-model
- **Tải**: Click "Files and versions" → Download repository
- **Vị trí cache**: `~/.cache/huggingface/hub/models--fanclan--age-gender-model/`

### 4. Sharris/age_detection_regression
- **Hugging Face**: https://huggingface.co/Sharris/age_detection_regression
- **Tải**: Click "Files and versions" → Download repository
- **Vị trí cache**: `~/.cache/huggingface/hub/models--Sharris--age_detection_regression/`

---

## 📥 PRIORITY 3: PyTorch Pretrained Weights (OPTIONAL)

### File: `age_resnet18_pytorch.pth`
- **Mục đích**: Fine-tuned weights cho ResNet18 age estimation
- **Vị trí**: `models/age_resnet18_pytorch.pth`
- **Lưu ý**: File này cần được train hoặc tìm từ nguồn khác (không có sẵn)
- **Alternatives**: 
  - Sử dụng OpenCV DNN models (đã tải ở Priority 1)
  - Hoặc sử dụng Hugging Face models

---

## 📋 DANH SÁCH TÓM TẮT

### ✅ BẮT BUỘC (Priority 1)

| File | Vị trí | URL |
|------|--------|-----|
| `age_deploy.prototxt` | `models/age_gender_opencv/` | https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt |
| `age_net.caffemodel` | `models/age_gender_opencv/` | https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel |
| `gender_deploy.prototxt` | `models/age_gender_opencv/` | https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt |
| `gender_net.caffemodel` | `models/age_gender_opencv/` | https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel |

### ⚠️ TÙY CHỌN (Priority 2-3)

| Item | Vị trí | Ghi chú |
|------|--------|---------|
| Hugging Face models | Cache hoặc `models/age_estimator_hf/` | Tự động tải nếu có thể |
| `age_resnet18_pytorch.pth` | `models/` | Cần train hoặc tìm nguồn |

---

## 🚀 HƯỚNG DẪN TẢI BẰNG COMMAND LINE

### Tạo thư mục:
```bash
mkdir -p models/age_gender_opencv
```

### Tải các file:

```bash
cd models/age_gender_opencv

# Age prototxt
curl -L -o age_deploy.prototxt https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt

# Age model (lớn ~43MB)
curl -L -o age_net.caffemodel https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel

# Gender prototxt
curl -L -o gender_deploy.prototxt https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt

# Gender model (~3.4MB)
curl -L -o gender_net.caffemodel https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel
```

### Kiểm tra:
```bash
ls -lh models/age_gender_opencv/
```

Kết quả mong đợi:
```
-rw-r--r--  1 user  staff    2.1K  age_deploy.prototxt
-rw-r--r--  1 user  staff   43.0M  age_net.caffemodel
-rw-r--r--  1 user  staff    1.9K  gender_deploy.prototxt
-rw-r--r--  1 user  staff    3.4M  gender_net.caffemodel
```

---

## ⚠️ LƯU Ý

1. **OpenCV GitHub URLs có thể trả về 404**: 
   - Thử backup URLs từ Google Drive
   - Hoặc clone OpenCV repository và copy files manually

2. **Google Drive Links**:
   - Có thể cần phải extract từ zip files
   - Hoặc tải từ mirror sites

3. **Alternative Sources**:
   - OpenCV official repository: https://github.com/opencv/opencv
   - OpenCV extra repository: https://github.com/opencv/opencv_extra
   - Model Zoo: https://github.com/opencv/opencv/wiki/Models

4. **Sau khi tải xong**:
   - Restart application để system tự động detect và load models
   - Kiểm tra logs để confirm models đã load thành công

---

## ✅ VERIFY SAU KHI TẢI

Chạy script kiểm tra:
```bash
python -c "
from src.modules.demographics.age_gender_opencv import AgeGenderOpenCV
import logging
logging.basicConfig(level=logging.INFO)
estimator = AgeGenderOpenCV()
if estimator.age_net is not None and estimator.gender_net is not None:
    print('✅ Models loaded successfully!')
else:
    print('❌ Models not loaded, check paths')
"
```


