# Documentation Index

Tài liệu tổng hợp cho project Kidsplaza Person Detector.

## 📚 Documents

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - Bắt đầu nhanh với project
  - Environment setup
  - Installation
  - Basic usage
  - Common commands

### Standards & Best Practices
- **[Python Production Best Practices](standards/python_production_best_practices.md)**
  - Code style & conventions
  - Type hints & documentation
  - Error handling
  - Database best practices
  - Security practices
  - Performance optimization
  - Testing strategies

- **[File Creation Requirements](standards/FILE_CREATION_REQUIREMENTS.md)**
  - Yêu cầu khi tạo file mới
  - Code structure requirements
  - Documentation requirements
  - Import order
  - Naming conventions

- **[Project Structure](standards/project_structure.md)**
  - Directory organization
  - Module structure
  - Testing structure
  - Configuration management

### Developer Resources
- **[Developer Checklist](DEVELOPER_CHECKLIST.md)** - Checklist bắt buộc cho developers
  - Before coding
  - During coding
  - Testing
  - Code review
  - Before commit

## 📁 Structure

```
docs/
├── README.md                              # This file
├── QUICK_START.md                         # Quick start guide
├── DEVELOPER_CHECKLIST.md                 # Developer checklist
├── reports/                           # Consolidated reports and results
└── standards/
    ├── python_production_best_practices.md # Best practices
    ├── FILE_CREATION_REQUIREMENTS.md      # File requirements
    └── project_structure.md               # Project structure
```

## 🔧 Templates

Xem trong `templates/` directory:
- `template_script.py` - Template cho scripts
- `template_module.py` - Template cho modules  
- `template_test.py` - Template cho tests

## 🚀 Quick Links

### Development
- **Setup**: [Quick Start Guide](QUICK_START.md#1-setup-environment)
- **Code Quality**: [Best Practices](standards/python_production_best_practices.md)
- **File Creation**: [Requirements](standards/FILE_CREATION_REQUIREMENTS.md)
- **Checklist**: [Developer Checklist](DEVELOPER_CHECKLIST.md)

### Tools
- **Linting**: Flake8, Pylint
- **Formatting**: Black, isort
- **Type Checking**: MyPy
- **Testing**: Pytest
- **Pre-commit**: Pre-commit hooks

### Reports
- Re-ID: `debug_plan/REID_OPTIMIZATION_FINAL_REPORT.md`, `REID_FACE_OPTIMIZATION_REPORT.md`
- ArcFace: `ARCFACE_INTEGRATION_STATUS.md`, `ARCFACE_BENCHMARK_INTERIM.md`
- Gender: `GENDER_CLASSIFICATION_FINAL_CONFIG.md`, `GENDER_CLASSIFICATION_USAGE.md`

## 📖 Usage

### For New Developers
1. Read [Quick Start Guide](QUICK_START.md)
2. Review [Best Practices](standards/python_production_best_practices.md)
3. Check [Developer Checklist](DEVELOPER_CHECKLIST.md)
4. Look at [Templates](../templates/)

### For Daily Work
1. Check [Developer Checklist](DEVELOPER_CHECKLIST.md)
2. Follow [File Requirements](standards/FILE_CREATION_REQUIREMENTS.md)
3. Use templates from `templates/`
4. Run quality checks before commit

### For Code Review
1. Review against [Best Practices](standards/python_production_best_practices.md)
2. Check [Developer Checklist](DEVELOPER_CHECKLIST.md)
3. Verify tests and coverage
4. Check documentation

## 🔍 Code Quality Standards

### Required Tools
- Black (code formatter)
- isort (import sorter)
- Flake8 (linter)
- Pylint (advanced linter)
- MyPy (type checker)
- Pytest (testing)
- Pre-commit (hooks)

### Quality Gates
- [ ] Code formatted with Black
- [ ] Imports sorted with isort
- [ ] No Flake8 errors
- [ ] No Pylint errors (>9.0 score)
- [ ] MyPy type checking passes
- [ ] All tests pass
- [ ] Coverage > 80%

## 📊 Project Structure

```
project/
├── src/
│   ├── modules/          # Reusable modules
│   └── scripts/          # Executable scripts
├── tests/                # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/               # Configuration
├── docs/                 # Documentation (this folder)
├── templates/            # Code templates
└── requirements.txt      # Dependencies
```

## 🛠️ Common Commands

```bash
# Setup
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install

# Code quality
black src/
isort src/
flake8 src/
pylint src/
mypy src/

# Testing
pytest
pytest --cov=src

# Pre-commit
pre-commit run --all-files

# Scripts
python src/scripts/verify_database_health.py
python src/scripts/verify_camera_health.py
python src/scripts/display_camera.py 1
```

## 📞 Support

- **Documentation Issues**: Check relevant doc file
- **Code Issues**: Review standards and best practices
- **Setup Issues**: See Quick Start Guide
- **Questions**: Ask team members

## 🔄 Document Updates

Khi cập nhật code, hãy cập nhật documentation tương ứng:
- API changes → Update API docs
- New features → Update README
- Process changes → Update best practices
- Structure changes → Update project structure doc

---

**Happy Coding!** 🚀

