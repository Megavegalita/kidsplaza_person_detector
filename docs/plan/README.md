# Plan Documentation

Tài liệu kế hoạch phát triển cho Kidsplaza Person Detector.

## 📋 Documents

### [Development Plan](development_plan.md)
Kế hoạch phát triển chi tiết cho hệ thống phát hiện người.

**Nội dung:**
- Requirements và user stories
- Kiến trúc hệ thống
- Implementation plan theo phase
- Testing strategy
- Configuration management
- Risk assessment
- Success criteria

### [Testing Workflow](testing_workflow.md) ⭐
Quy trình testing với video file trước khi tích hợp live camera.

**Nội dung:**
- Testing workflow overview
- Phase 3.5: Offline video file testing
- Test cases và metrics
- Pre-live camera checklist
- Success criteria

### [Tech Stack](tech_stack.md)
Ngăn xếp công nghệ chính cho nền tảng Mac M4 Pro.

**Nội dung:**
- Môi trường & ngôn ngữ
- Framework học sâu (PyTorch with MPS)
- Thư viện thị giác máy tính (OpenCV)
- Công cụ tối ưu hóa (Core ML)
- Các mô hình (YOLO, ByteTrack, Age/Gender)

### [Changelog](CHANGELOG.md)
Tổng hợp các thay đổi và cập nhật của development plan.

**Nội dung:**
- Summary of changes
- Key improvements
- New features added

## 🚀 Quick Start

### Phase 1: Environment Setup
```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 2. Install PyTorch with MPS support
pip install torch torchvision --index-url https://download.pytorch.org/whl/nightly/cpu

# 3. Install other dependencies
pip install opencv-python ultralytics bytetracker
pip install coremltools psycopg2 redis

# 4. Verify MPS is available
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Phase 2: Begin Implementation
Xem chi tiết trong [development_plan.md](development_plan.md)

## 📁 Structure

```
docs/plan/
├── README.md              # This file
├── development_plan.md    # Detailed development plan
├── testing_workflow.md    # Video file testing workflow
├── tech_stack.md         # Technology stack
└── CHANGELOG.md          # Changes and updates
```

## 🎯 Current Status

**Branch**: `main_func`  
**Phase**: Planning → Phase 1 (Environment Setup)  
**Status**: Ready to begin implementation  
**Testing Strategy**: **OFFLINE VIDEO FILE TESTING FIRST**, then live camera

## 🔑 Key Principle

**CRITICAL: Test on Video Files Before Live Integration**

Testing workflow:
1. ✅ Setup & Development (Phases 1-3)
2. ✅ **Video File Testing** (Phase 3.5) - OFFLINE
3. ✅ Continue Development on Video Files (Phases 4-6)
4. ✅ Validation Complete
5. ✅ Only Then → Live Camera Integration (Phase 7)

## 📖 Related Documentation

- [Developer Checklist](../DEVELOPER_CHECKLIST.md)
- [Quick Start Guide](../QUICK_START.md)
- [Project Structure](../standards/project_structure.md)
- [Best Practices](../standards/python_production_best_practices.md)

## ✅ Next Steps

1. Review [development_plan.md](development_plan.md)
2. Setup development environment (Phase 1)
3. Begin camera module implementation (Phase 2)
4. Follow the phase-by-phase plan

---

**Last Updated**: 2024  
**Version**: 1.0

