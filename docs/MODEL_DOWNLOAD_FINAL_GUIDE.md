# Hướng Dẫn Tải Models - Final (Khi URLs Fail)

**Date**: 2025-11-02  
**Status**: GitHub URLs trả về 404 - Files không còn tồn tại ở đó

---

## ⚠️ VẤN ĐỀ

Các URLs GitHub đã trả về 404:
- `https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt` → 404
- `https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel` → 404
- Tất cả paths khác đều 404

**Lý do**: OpenCV đã di chuyển hoặc xóa các files này khỏi GitHub repos.

---

## ✅ GIẢI PHÁP: Tải Thủ Công

### Option 1: OpenCV Model Zoo (KHUYẾN NGHỊ)

1. **Truy cập OpenCV Model Zoo**:
   - URL: https://github.com/opencv/opencv_extra/tree/master/testdata/dnn
   - Hoặc: https://github.com/opencv/opencv/wiki/Models

2. **Tìm Age/Gender Models**:
   - Tìm trong list: `age_net.caffemodel`, `gender_net.caffemodel`
   - Click vào từng file → Download

3. **Tìm Prototxt files**:
   - URL: https://github.com/opencv/opencv/tree/master/samples/dnn
   - Tìm: `age_deploy.prototxt`, `gender_deploy.prototxt`
   - Click "Raw" → Save As

---

### Option 2: Google Drive / Mirror Sites

Các files có thể được host ở:
- Google Drive (shared links)
- Dropbox
- Other mirror sites

**Search**: "opencv age_net.caffemodel download" hoặc "opencv gender_net.caffemodel"

---

### Option 3: Clone OpenCV Repos và Tìm Files

```bash
# Clone full repos (không phải shallow)
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_extra.git

# Tìm files
find opencv -name "age_deploy.prototxt"
find opencv -name "gender_deploy.prototxt"
find opencv_extra -name "age_net.caffemodel"
find opencv_extra -name "gender_net.caffemodel"

# Copy đến thư mục models
cp <found_path> models/age_gender_opencv/
```

---

### Option 4: Sử dụng Alternative Models

Thay vì OpenCV DNN, có thể sử dụng:
1. **PyTorch models** (đã có trong code)
2. **Other pretrained models** từ:
   - Hugging Face (nếu load được)
   - Model Zoo khác
   - Custom trained models

---

## 📋 CHECKLIST SAU KHI TẢI

Sau khi tải manual, kiểm tra:

```bash
cd models/age_gender_opencv
ls -lh

# Kết quả mong đợi:
# - age_deploy.prototxt        ~2KB
# - age_net.caffemodel         ~25-43MB
# - gender_deploy.prototxt      ~2KB  
# - gender_net.caffemodel       ~3.4MB
```

Kiểm tra nội dung prototxt (không phải "404: Not Found"):
```bash
head age_deploy.prototxt
# Nên thấy: "name: "age_net"" hoặc các dòng protobuf khác
```

---

## 🔧 VERIFY SAU KHI TẢI

```bash
python -c "
from src.modules.demographics.age_gender_opencv import AgeGenderOpenCV
import logging
logging.basicConfig(level=logging.WARNING)
estimator = AgeGenderOpenCV()
if estimator.age_net and estimator.gender_net:
    print('✅ Models loaded successfully!')
else:
    print('❌ Models failed to load')
"
```

---

## 📝 GHI CHÚ

- **Tổng kích thước**: ~28-46 MB
- **Thời gian tải**: Phụ thuộc vào nguồn và tốc độ mạng
- **Sau khi tải**: System sẽ tự động detect và load khi restart application

---

## 🆘 NẾU VẪN KHÔNG TẢI ĐƯỢC

Có thể:
1. **Sử dụng PyTorch models thay thế** (đã có trong code)
2. **Train/fine-tune custom models** từ datasets như:
   - UTKFace
   - Adience
   - AFAD
3. **Contact OpenCV community** để hỏi về models mới nhất

