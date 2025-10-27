# Project Structure Best Practices

Tài liệu về cấu trúc project cho Python production code.

## Directory Structure

```
project/
├── .cursor/
│   └── commands/              # Best practices documentation
│       ├── python_production_best_practices.md
│       └── project_structure.md
├── .github/
│   └── workflows/            # CI/CD workflows
│       ├── ci.yml
│       └── deploy.yml
├── config/                   # Configuration files
│   └── database.json
├── input/                    # Input data
│   ├── cameras_config/
│   └── video/
├── src/                      # Source code
│   ├── __init__.py
│   ├── modules/              # Reusable modules
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── services.py
│   └── scripts/              # Executable scripts
│       ├── __init__.py
│       ├── verify_database_health.py
│       ├── verify_camera_health.py
│       └── display_camera.py
├── tests/                    # Test files
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_database.py
│   │   └── test_camera.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── fixtures/             # Test fixtures
│       └── sample_data.json
├── docs/                     # Documentation
│   ├── index.md
│   ├── api.md
│   └── deployment.md
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .pylintrc                # Pylint configuration
├── .flake8                  # Flake8 configuration
├── mypy.ini                 # MyPy configuration
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── README.md                # Project documentation
└── LICENSE                  # Project license
```

---

## Module Organization

### Core Modules (`src/modules/`)

**Purpose**: Reusable business logic and utilities

```python
# src/modules/__init__.py
"""Core modules for the application."""

# src/modules/database.py
"""Database connection and operations."""

from typing import Dict, Optional
from contextlib import contextmanager
import psycopg2
import redis

class DatabaseManager:
    """Manages database connections."""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
    
    @contextmanager
    def get_connection(self):
        """Get database connection context."""
        pass

# src/modules/models.py
"""Data models and schemas."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PersonDetection:
    """Person detection result."""
    timestamp: datetime
    confidence: float
    bbox: tuple
    gender: Optional[str] = None
```

### Service Layer (`src/services/`)

**Purpose**: Business logic and orchestration

```python
# src/services/detection_service.py
"""Person detection service."""

from typing import List
from src.modules.models import PersonDetection

class DetectionService:
    """Service for person detection."""
    
    def detect_persons(self, frame) -> List[PersonDetection]:
        """Detect persons in frame."""
        pass
```

---

## Scripts (`src/scripts/`)

**Purpose**: Executable scripts for operations

Each script should:
- Be executable with shebang line: `#!/usr/bin/env python3`
- Have `main()` function
- Use proper argument parsing
- Handle errors gracefully
- Exit with appropriate codes

```python
#!/usr/bin/env python3
"""
Script description.

Usage:
    python src/scripts/script_name.py [arguments]
"""

import sys
from pathlib import Path

def main():
    """Main entry point."""
    try:
        # Script logic
        pass
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Configuration Management

### Environment Variables

Use `.env` for local development, environment variables for production.

```bash
# .env (local development)
DB_HOST=localhost
DB_PORT=5432
DB_USER=autoeyes
DB_PASSWORD=
DB_NAME=gender_analysis

REDIS_HOST=localhost
REDIS_PORT=6379
```

### Configuration Files

Store non-sensitive configuration in JSON/YAML files.

```json
{
  "app_name": "person_detector",
  "version": "1.0.0",
  "settings": {
    "log_level": "INFO",
    "max_retries": 3
  }
}
```

---

## Testing Structure

### Test Organization

```
tests/
├── __init__.py
├── unit/              # Fast, isolated unit tests
│   ├── test_database.py
│   └── test_camera.py
├── integration/       # Integration tests
│   ├── test_api.py
│   └── test_database_integration.py
├── e2e/              # End-to-end tests
│   └── test_full_flow.py
└── fixtures/         # Test data
    ├── sample_data.json
    └── test_images/
```

### Test File Naming

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<function_name>`

```python
# tests/unit/test_database.py
import pytest
from src.modules.database import DatabaseManager

class TestDatabaseManager:
    """Test database manager."""
    
    def test_connection_success(self):
        """Test successful database connection."""
        pass
    
    def test_connection_failure(self):
        """Test database connection failure."""
        pass
```

---

## Documentation Structure

### README.md Template

```markdown
# Project Title

## Description
Brief description of what the project does

## Features
- Feature 1
- Feature 2

## Requirements
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

## Installation

### 1. Clone repository
```bash
git clone <repository_url>
cd project
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Running scripts
```bash
# Health check database
python src/scripts/verify_database_health.py

# Health check cameras
python src/scripts/verify_camera_health.py
```

## Development

### Setup development environment
```bash
pip install -r requirements-dev.txt
pre-commit install
```

### Running tests
```bash
pytest tests/
```

### Code quality checks
```bash
black src/
flake8 src/
pylint src/
mypy src/
```

## Configuration
See `config/database.json` for database settings

## Contributing
Guidelines for contributing

## License
Project license
```

---

## Code Quality Standards

### File Headers

Each Python file should start with module docstring:

```python
#!/usr/bin/env python3
"""
Module description.

This module provides functionality for...
"""

import sys
from typing import Dict, List
```

### Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports
4. Each group separated by blank line

```python
# Standard library
import json
import sys
from pathlib import Path

# Third-party
import cv2
import psycopg2

# Local
from src.modules.database import DatabaseManager
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest
      - name: Code quality
        run: |
          black --check src/
          flake8 src/
          pylint src/
```

---

## Deployment Structure

### Docker Support (Optional)

```dockerfile
# Dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY config/ config/

CMD ["python", "src/scripts/verify_database_health.py"]
```

---

## Version Control Best Practices

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
.venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# MyPy
.mypy_cache/

# Logs
*.log

# Environment
.env
.env.local
```

### Commit Messages

Follow conventional commits:

```
feat: Add database health check script
fix: Resolve camera connection timeout issue
docs: Update README with usage examples
refactor: Improve error handling in database module
test: Add unit tests for database manager
chore: Update dependencies in requirements.txt
```

---

## Monitoring and Logging

### Log Configuration

```python
# src/utils/logging.py
import logging
from pathlib import Path

def setup_logging(log_dir: Path = Path("logs")):
    """Setup application logging."""
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log'),
            logging.StreamHandler()
        ]
    )
```

---

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [Real Python Project Structure](https://realpython.com/python-application-layouts/)
- [12 Factor App](https://12factor.net/)
- [PEP 420 - Implicit Namespace Packages](https://www.python.org/dev/peps/pep-0420/)

