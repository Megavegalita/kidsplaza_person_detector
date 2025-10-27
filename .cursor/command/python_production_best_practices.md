# Python Production Best Practices

Tài liệu này tổng hợp các best practices và tiêu chuẩn lập trình Python cho sản phẩm production.

## 1. Code Style & Conventions

### PEP 8 Compliance
- Tuân thủ PEP 8 style guide
- Max line length: 79-99 characters (tùy team)
- Use 4 spaces for indentation (không dùng tabs)
- Naming conventions:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: prefix với `_single` hoặc `__double`

### Example
```python
# ✅ Good
class DatabaseConnection:
    MAX_RETRIES = 3
    _internal_state = None
    
    def connect_to_database(self):
        pass

# ❌ Bad
class databaseConnection:
    MaxRetries = 3
    internalState = None
    
    def ConnectToDatabase(self):
        pass
```

---

## 2. Type Hints & Documentation

### Type Hints
- Luôn sử dụng type hints cho functions, methods
- Import từ `typing` module
- Hỗ trợ Python 3.8+ (hoặc 3.9+)

### Docstrings
- Sử dụng Google style hoặc NumPy style docstrings
- Luôn document public APIs
- Include: Args, Returns, Raises

### Example
```python
from typing import Dict, List, Optional, Tuple
from pathlib import Path

def load_config(
    config_path: Path,
    validate: bool = True
) -> Dict[str, any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to the configuration JSON file
        validate: Whether to validate the configuration
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    pass
```

---

## 3. Error Handling

### Principles
- Fail fast - validate inputs early
- Use specific exceptions
- Never catch bare `except:` clause
- Log exceptions with context
- Return meaningful error messages

### Example
```python
def verify_database_connection(
    config: Dict[str, str],
    timeout: int = 5
) -> Tuple[bool, Optional[str]]:
    """Verify database connection with proper error handling."""
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            timeout=timeout
        )
        return True, None
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False, f"Cannot connect to database: {str(e)}"
    except KeyError as e:
        logger.error(f"Missing config key: {e}")
        return False, f"Invalid configuration: missing {e}"
    except Exception as e:
        logger.exception("Unexpected error in database connection")
        return False, f"Unexpected error: {str(e)}"
```

---

## 4. Logging

### Configuration
- Use Python's `logging` module
- Separate log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log to both file and stdout in production
- Include structured logging (JSON) for better parsing

### Example
```python
import logging
from datetime import datetime

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.info("Database connection established")
logger.error(f"Failed to connect: {error}", exc_info=True)
logger.debug(f"Config values: {config_dict}")
```

---

## 5. Configuration Management

### Environment Variables
- Use environment variables for sensitive data
- Never hardcode secrets
- Use `python-dotenv` for `.env` files
- Validate configuration on startup

### Example
```python
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_password = os.getenv('DB_PASSWORD')
        
        # Validate required settings
        if not self.db_password:
            raise ValueError("DB_PASSWORD environment variable is required")

# Usage
config = Config()
```

---

## 6. Database Best Practices

### Connection Management
- Use connection pooling
- Always close connections (context managers)
- Handle transaction rollbacks
- Implement retry logic with exponential backoff

### Example
```python
import psycopg2
from contextlib import contextmanager
from typing import Generator

@contextmanager
def get_db_connection(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager for database connections.
    Ensures proper connection cleanup.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Usage
with get_db_connection(**db_config) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
```

---

## 7. Async Programming (FastAPI)

### Async Best Practices
- Use `async def` for I/O-bound operations
- Use `await` for async operations
- Don't mix sync and async unnecessarily
- Use `asyncio` for concurrent operations

### Example
```python
import asyncio
from typing import List
import aiohttp

async def fetch_data(url: str) -> dict:
    """Fetch data asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def fetch_multiple(urls: List[str]) -> List[dict]:
    """Fetch multiple URLs concurrently."""
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)
```

---

## 8. Testing

### Test Structure
- Use pytest framework
- Organize tests: unit, integration, e2e
- Aim for >80% code coverage
- Test edge cases and error conditions

### Example
```python
import pytest
from unittest.mock import Mock, patch
from src.scripts.verify_database_health import verify_postgresql_connection

def test_verify_postgresql_connection_success():
    """Test successful PostgreSQL connection."""
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db',
        'username': 'test_user',
        'password': 'test_pass'
    }
    
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_conn.cursor.return_value.fetchone.return_value = ('PostgreSQL 15.0',)
        mock_connect.return_value = mock_conn
        
        is_healthy, message, response_time = verify_postgresql_connection(config)
        
        assert is_healthy is True
        assert 'PostgreSQL' in message

def test_verify_postgresql_connection_failure():
    """Test failed PostgreSQL connection."""
    config = {
        'host': 'invalid_host',
        'port': 5432,
        'database': 'test_db',
        'username': 'test_user',
        'password': 'test_pass'
    }
    
    with patch('psycopg2.connect') as mock_connect:
        mock_connect.side_effect = Exception("Connection refused")
        
        is_healthy, message, response_time = verify_postgresql_connection(config)
        
        assert is_healthy is False
        assert 'failed' in message.lower()
```

---

## 9. Security Best Practices

### Input Validation
- Validate and sanitize all inputs
- Use parameterized queries (prevent SQL injection)
- Limit string lengths
- Validate file paths and prevent path traversal

### Example
```python
from pathlib import Path
from typing import Optional

def validate_file_path(file_path: str, base_dir: Path) -> Optional[Path]:
    """
    Validate file path to prevent path traversal attacks.
    
    Args:
        file_path: Path to validate
        base_dir: Base directory to restrict within
        
    Returns:
        Validated Path object or None
    """
    try:
        resolved_path = (base_dir / file_path).resolve()
        if not resolved_path.is_relative_to(base_dir.resolve()):
            return None
        return resolved_path
    except (ValueError, RuntimeError):
        return None

# Usage
safe_path = validate_file_path('config/database.json', Path('/project'))
if safe_path:
    # Safe to use
    pass
```

---

## 10. Performance Optimization

### Profiling & Optimization
- Profile code before optimizing
- Use generators for large datasets
- Cache expensive operations
- Minimize database queries (use joins, avoid N+1)

### Example
```python
# ✅ Good - Use generator for large datasets
def read_large_file(file_path: str) -> Generator[str, None, None]:
    """Read large file line by line using generator."""
    with open(file_path, 'r') as file:
        for line in file:
            yield line.strip()

# Usage
for line in read_large_file('large_file.txt'):
    process(line)

# ❌ Bad - Load entire file into memory
def read_large_file_bad(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        return file.readlines()  # May cause memory issues
```

---

## 11. Code Organization

### Project Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── services.py
│   └── scripts/
│       ├── __init__.py
│       ├── health_check.py
│       └── utilities.py
├── tests/
│   ├── __init__.py
│   ├── test_modules.py
│   └── test_scripts.py
├── config/
│   └── database.json
├── requirements.txt
├── README.md
└── .env.example
```

### Module Organization
- Single Responsibility Principle
- Clear separation of concerns
- Reusable utilities
- Minimal dependencies between modules

---

## 12. Environment Setup

### Virtual Environment
- Always use virtual environment
- Use `venv` or `virtualenv`
- Activate before running scripts
- Requirements management

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Freeze dependencies
pip freeze > requirements.txt
```

---

## 13. CI/CD Best Practices

### Pre-commit Hooks
- Format code (black, autopep8)
- Lint code (pylint, flake8, ruff)
- Run tests
- Type checking (mypy)

### Example .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## 14. Dependencies Management

### Requirements Files
- Separate dev and production requirements
- Pin versions for production
- Use `requirements.txt` and `requirements-dev.txt`

```
# requirements.txt (Production)
psycopg2-binary==2.9.11
redis==5.0.0
opencv-python==4.12.0.88
numpy==2.2.6

# requirements-dev.txt (Development)
pytest==7.4.0
pytest-cov==4.1.0
black==23.3.0
flake8==6.0.0
mypy==1.3.0
```

---

## 15. Documentation Standards

### Code Comments
- Explain WHY, not WHAT
- Comment complex algorithms
- Keep comments up to date

### README Structure
```markdown
# Project Title

## Description
Brief description of the project

## Requirements
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
python src/scripts/verify_database_health.py
```

## Configuration
See `config/database.json` for database settings

## Testing
```bash
pytest tests/
```

## Contributing
Guidelines for contributing
```

---

## 16. Common Anti-patterns to Avoid

### ❌ Don't Do This
```python
# Bare except clause
try:
    process_data()
except:
    pass

# Mutable default arguments
def append_item(item, list=[]):
    list.append(item)
    return list

# Using import *
from module import *

# Not handling exceptions properly
data = json.loads(response)  # May crash

# Catching multiple exceptions incorrectly
try:
    process()
except (Exception, ValueError) as e:
    handle()
```

### ✅ Do This
```python
# Specific exceptions
try:
    process_data()
except ValueError as e:
    logger.error(f"Validation error: {e}")
except KeyError as e:
    logger.error(f"Missing key: {e}")
except Exception as e:
    logger.exception("Unexpected error")
    raise

# Immutable default arguments
def append_item(item, list=None):
    if list is None:
        list = []
    list.append(item)
    return list

# Specific imports
from module import specific_function, SpecificClass

# Proper error handling
try:
    data = json.loads(response)
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
    data = None
```

---

## 17. Production Checklist

- [ ] All code follows PEP 8 style guide
- [ ] Type hints added to all functions
- [ ] Docstrings added to all public APIs
- [ ] Error handling implemented for all edge cases
- [ ] Logging configured and tested
- [ ] Environment variables used for sensitive data
- [ ] Database connections use context managers
- [ ] Async/await properly implemented (if applicable)
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests written and passing
- [ ] Security vulnerabilities checked and fixed
- [ ] Dependencies are pinned and documented
- [ ] Configuration is validated on startup
- [ ] Performance bottlenecks identified and optimized
- [ ] Code reviewed by peers
- [ ] Documentation updated (README, docstrings)
- [ ] CI/CD pipeline configured
- [ ] Monitoring and alerting configured
- [ ] Backward compatibility checked (if API)

---

## 18. Recommended Tools

### Code Quality
- **Black**: Code formatter
- **Flake8**: Linter
- **Ruff**: Fast linter and formatter
- **Pylint**: Advanced linter
- **MyPy**: Static type checker

### Testing
- **Pytest**: Testing framework
- **pytest-cov**: Coverage reports
- **pytest-asyncio**: Async testing

### Documentation
- **Sphinx**: Documentation generator
- **mkdocs**: Markdown documentation

### Security
- **bandit**: Security linter
- **safety**: Check dependencies for vulnerabilities

---

## References

- [PEP 8 Style Guide](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [12 Factor App](https://12factor.net/)

