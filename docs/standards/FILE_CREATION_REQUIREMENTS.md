# File Creation Requirements

Tài liệu này mô tả các yêu cầu bắt buộc khi tạo file mới trong project.

## 📋 Tổng Quan

Mỗi file Python mới phải tuân thủ các yêu cầu sau để đảm bảo consistency và quality.

---

## 1. Python Files (.py)

### Bắt Buộc

#### 1.1 Shebang Line
```python
#!/usr/bin/env python3
```
- **Luôn có** cho các script executable
- Dùng `python3` không dùng `python`

#### 1.2 Module Docstring
```python
"""
Module description.

This module provides functionality for...
"""
```
- **Bắt buộc** cho mọi Python file
- Nêu rõ mục đích và chức năng của module
- Tối thiểu 2-3 dòng

#### 1.3 Type Hints
```python
from typing import Dict, List, Optional, Tuple

def process_data(
    data: Dict[str, any],
    validate: bool = True
) -> Optional[str]:
    """Process data with optional validation."""
    pass
```
- **Bắt buộc** cho tất cả function signatures
- Bao gồm: parameters, return type
- Sử dụng `typing` module

#### 1.4 Function Docstrings
```python
def connect_to_database(
    host: str,
    port: int
) -> bool:
    """
    Connect to database.
    
    Args:
        host: Database host address
        port: Database port number
        
    Returns:
        True if connection successful, False otherwise
        
    Raises:
        ConnectionError: If connection fails
    """
```
- **Bắt buộc** cho public functions
- Google style docstring
- Include: Args, Returns, Raises

#### 1.5 Error Handling
```python
def load_config(config_path: str) -> Dict:
    """Load configuration with proper error handling."""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise ValueError(f"Invalid config: {e}") from e
```
- **Luôn xử lý exceptions** cụ thể
- Không dùng bare `except:`
- Log errors

---

## 2. Scripts (.py trong src/scripts/)

### Yêu Cầu Đặc Biệt

#### 2.1 main() Function
```python
def main():
    """Main entry point for the script."""
    try:
        # Script logic here
        result = process_data()
        sys.exit(0)  # Success
    except Exception as e:
        logger.exception(f"Script failed: {e}")
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
```
- **Bắt buộc** cho mọi script
- Exit codes: 0 (success), 1 (failure)
- Handle exceptions

#### 2.2 Argument Parsing
```python
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Process camera data'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to input file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output.txt',
        help='Path to output file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    # Use args.input_file, args.output, args.verbose
```

#### 2.3 Logging Setup
```python
import logging

# Setup module-level logger
logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Script started")
```

---

## 3. Module Files (.py trong src/modules/)

### Yêu Cầu Đặc Biệt

#### 3.1 Class Structure
```python
class DatabaseManager:
    """Manages database connections."""
    
    def __init__(self, config: Dict[str, any]) -> None:
        """
        Initialize database manager.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self._connection = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connection is not None
    
    def connect(self) -> None:
        """Connect to database."""
        pass
```
- Docstrings cho classes
- Docstrings cho public methods
- Type hints cho tất cả methods
- Properties cho computed values

---

## 4. Test Files (test_*.py)

### Yêu Cầu Đặc Biệt

#### 4.1 Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestDatabaseManager:
    """Test suite for DatabaseManager."""
    
    def test_connection_success(self):
        """Test successful database connection."""
        # Arrange
        config = {'host': 'localhost', 'port': 5432}
        manager = DatabaseManager(config)
        
        # Act
        result = manager.connect()
        
        # Assert
        assert result is True
    
    def test_connection_failure(self):
        """Test database connection failure."""
        pass
```
- Class name: `Test<ClassName>`
- Method name: `test_<functionality>`
- Docstring cho mỗi test
- Arrange-Act-Assert pattern

---

## 5. Configuration Files (.json, .yaml)

### Yêu Cầu

```json
{
  "version": "1.0.0",
  "settings": {
    "key": "value"
  }
}
```
- Valid JSON/YAML syntax
- No trailing commas
- Indent 2 spaces
- Include version field

---

## 6. Documentation Files (.md)

### Yêu Cầu

```markdown
# Title

## Section

### Subsection

- List items
- Proper formatting

```python
# Code blocks
```

### Tables
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
```
- Clear headings hierarchy
- Code blocks with syntax highlighting
- Tables for structured data

---

## 7. Import Order

### Standard
```python
# 1. Standard library
import json
import sys
from pathlib import Path

# 2. Third-party
import cv2
import psycopg2

# 3. Local imports
from src.modules.database import DatabaseManager
```
- Alphabetical order trong mỗi group
- Blank line giữa groups
- Absolute imports preferred

---

## 8. File Naming Conventions

### Files
- Python files: `snake_case.py`
- Tests: `test_<module_name>.py`
- Configs: `<name>.json`, `<name>.yaml`
- Docs: `<name>.md`

### Directories
- `snake_case` cho directories
- Use lowercase
- No spaces, special characters

---

## 9. Checklist Trước Khi Commit

### Code Quality
- [ ] Code formatted với Black
- [ ] Imports sorted với isort
- [ ] No linter errors (Flake8, Pylint)
- [ ] Type checking pass (MyPy)
- [ ] All tests pass
- [ ] Coverage > 80%

### Documentation
- [ ] Module docstring added
- [ ] Functions có docstrings
- [ ] Type hints added
- [ ] Error handling documented

### Testing
- [ ] Unit tests written
- [ ] Integration tests written (if applicable)
- [ ] Edge cases covered
- [ ] Mock external dependencies

### Security
- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] Path traversal prevention

---

## 10. Templates

Xem các file template trong `templates/`:
- `template_script.py` - Template cho scripts
- `template_module.py` - Template cho modules
- `template_test.py` - Template cho tests

---

## 11. Ví Dụ File Hoàn Chỉnh

```python
#!/usr/bin/env python3
"""
Database health verification module.

This module provides functionality to verify database connections
and health status for PostgreSQL and Redis.
"""

import logging
from typing import Dict, Optional, Tuple

import psycopg2
import redis

logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """Check database health status."""
    
    def __init__(self, config: Dict[str, any]) -> None:
        """
        Initialize database health checker.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        logger.info("Database health checker initialized")
    
    def check_postgresql(
        self,
        timeout: int = 5
    ) -> Tuple[bool, Optional[str]]:
        """
        Check PostgreSQL connection health.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple of (is_healthy, error_message)
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Implementation here
            return True, None
        except Exception as e:
            logger.error(f"PostgreSQL check failed: {e}")
            return False, str(e)

def main() -> None:
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Main logic here
        logger.info("Script completed successfully")
        exit(0)
    except Exception as e:
        logger.exception(f"Script failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
```

---

## 12. Quy Trình Tạo File Mới

1. **Planning**: Xác định purpose và requirements
2. **Template**: Copy từ template phù hợp
3. **Implementation**: Implement functionality
4. **Documentation**: Add docstrings và comments
5. **Testing**: Write tests
6. **Quality Check**: Run linters và formatters
7. **Review**: Code review nếu cần
8. **Commit**: Commit với descriptive message

---

## 13. Công Cụ Hỗ Trợ

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

### Code Formatting
```bash
black src/
isort src/
```

### Linting
```bash
flake8 src/
pylint src/
```

### Type Checking
```bash
mypy src/
```

---

## 14. References

- See: `docs/standards/python_production_best_practices.md`
- See: `docs/standards/project_structure.md`
- See: `docs/QUICK_START.md`

