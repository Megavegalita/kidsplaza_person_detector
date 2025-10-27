# Quick Start Guide

Hướng dẫn nhanh để bắt đầu với project.

## 1. Setup Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## 2. Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 3. Configuration

Copy và chỉnh sửa file `.env.example`:

```bash
cp .env.example .env
# Edit .env with your settings
```

## 4. Health Checks

### Database Health Check
```bash
python src/scripts/verify_database_health.py
```

### Camera Health Check
```bash
python src/scripts/verify_camera_health.py
```

## 5. Running Scripts

### Display Camera Stream
```bash
python src/scripts/display_camera.py 1  # Channel 1
python src/scripts/display_camera.py 2  # Channel 2
```

## 6. Development Tools

### Code Formatting
```bash
# Format code with Black
black src/

# Sort imports
isort src/
```

### Linting
```bash
# Run Flake8
flake8 src/

# Run Pylint
pylint src/

# Run MyPy type checking
mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_database.py
```

### Security Checks
```bash
# Check for security issues
bandit -r src/

# Check dependency vulnerabilities
safety check
```

## 7. Code Quality Checklist

Trước khi commit code:

- [ ] Code đã được format với Black
- [ ] Imports đã được sắp xếp với isort
- [ ] Không có linter errors (Flake8, Pylint)
- [ ] Type checking pass (MyPy)
- [ ] Tất cả tests pass
- [ ] Code coverage > 80%
- [ ] Pre-commit hooks pass
- [ ] Docstrings đã được thêm cho functions
- [ ] Error handling đã được implement

## 8. Best Practices Reference

Xem chi tiết tại:
- **Best Practices**: `.cursor/command/python_production_best_practices.md`
- **Project Structure**: `.cursor/command/project_structure.md`

## 9. Common Commands

```bash
# Activate venv
source venv/bin/activate

# Check database health
python src/scripts/verify_database_health.py

# Check camera health
python src/scripts/verify_camera_health.py

# Display camera
python src/scripts/display_camera.py 1

# Run tests
pytest

# Format code
black src/

# Check code quality
pre-commit run --all-files
```

## 10. Troubleshooting

### Import errors
```bash
# Make sure you're in the project directory
cd /Users/autoeyes/Project/kidsplaza/person_detector

# Activate venv
source venv/bin/activate
```

### Database connection errors
- Kiểm tra PostgreSQL đang chạy: `brew services list | grep postgres`
- Kiểm tra Redis đang chạy: `brew services list | grep redis`
- Kiểm tra config trong `config/database.json`

### Camera connection errors
- Kiểm tra network connectivity
- Kiểm tra camera credentials trong config
- Kiểm tra RTSP URL format

## Need Help?

- Xem documentation trong `.cursor/command/`
- Check README.md for more details
- Review config files in `config/`

