# Model Download Checklist ✅

## 📋 CHECKLIST NHANH

### ✅ Priority 1: OpenCV DNN Models (BẮT BUỘC)

- [ ] `models/age_gender_opencv/age_deploy.prototxt`
- [ ] `models/age_gender_opencv/age_net.caffemodel` (~43 MB)
- [ ] `models/age_gender_opencv/gender_deploy.prototxt`
- [ ] `models/age_gender_opencv/gender_net.caffemodel` (~3.4 MB)

---

## 📥 CÁCH TẢI NHANH NHẤT

### Option 1: Chạy Script (Tự động)
```bash
cd /Users/autoeyes/Project/kidsplaza/person_detector
./download_models.sh
```

### Option 2: Command Line (Thủ công)
```bash
cd models/age_gender_opencv

# Download từng file
curl -L -o age_deploy.prototxt https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt
curl -L -o age_net.caffemodel https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel
curl -L -o gender_deploy.prototxt https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt
curl -L -o gender_net.caffemodel https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel
```

### Option 3: Tải từ GitHub Web Interface

1. **Age Prototxt**: 
   - URL: https://github.com/opencv/opencv/blob/4.x/samples/dnn/age_deploy.prototxt
   - Click "Raw" → Save As → `models/age_gender_opencv/age_deploy.prototxt`

2. **Age Model**:
   - URL: https://github.com/opencv/opencv_extra/blob/4.x/testdata/dnn/age_net.caffemodel
   - Click "Download" → Save to `models/age_gender_opencv/age_net.caffemodel`

3. **Gender Prototxt**:
   - URL: https://github.com/opencv/opencv/blob/4.x/samples/dnn/gender_deploy.prototxt
   - Click "Raw" → Save As → `models/age_gender_opencv/gender_deploy.prototxt`

4. **Gender Model**:
   - URL: https://github.com/opencv/opencv_extra/blob/4.x/testdata/dnn/gender_net.caffemodel
   - Click "Download" → Save to `models/age_gender_opencv/gender_net.caffemodel`

---

## 🔗 DIRECT LINKS (Copy vào trình duyệt)

### Age Model
1. **Prototxt**: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt
2. **Caffemodel**: https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel

### Gender Model
1. **Prototxt**: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt
2. **Caffemodel**: https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel

---

## ✅ KIỂM TRA SAU KHI TẢI

```bash
cd /Users/autoeyes/Project/kidsplaza/person_detector
ls -lh models/age_gender_opencv/
```

Kết quả mong đợi:
```
total 46M
-rw-r--r--  1 user  staff   2.1K  age_deploy.prototxt
-rw-r--r--  1 user  staff  43.0M  age_net.caffemodel
-rw-r--r--  1 user  staff   1.9K  gender_deploy.prototxt
-rw-r--r--  1 user  staff   3.4M  gender_net.caffemodel
```

---

## 🎯 VỊ TRÍ CUỐI CÙNG

Tất cả files phải ở đây:
```
/Users/autoeyes/Project/kidsplaza/person_detector/models/age_gender_opencv/
├── age_deploy.prototxt         ✅ (2.1 KB)
├── age_net.caffemodel          ✅ (43 MB)
├── gender_deploy.prototxt       ✅ (1.9 KB)
└── gender_net.caffemodel       ✅ (3.4 MB)
```

---

## 📝 GHI CHÚ

- **Tổng kích thước**: ~47 MB
- **Thời gian tải**: ~1-5 phút tùy kết nối
- **Sau khi tải**: Restart application để system load models
- **Verify**: Check logs để confirm models đã load thành công


