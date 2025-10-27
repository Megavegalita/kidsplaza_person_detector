# Cursor Commands for Python Development

Các custom commands được cấu hình cho project Python.

## 📋 Available Commands

### Code Quality
- **`run-linting`** - Run Flake8 và Pylint linting checks
- **`run-type-checking`** - Run MyPy type checking
- **`format-code`** - Format code với Black và isort
- **`code-quality-check`** - Run tất cả code quality checks

### Testing
- **`run-tests`** - Run all tests với pytest
- **`run-tests-with-coverage`** - Run tests và generate coverage report

### Pre-commit & Security
- **`pre-commit-check`** - Run pre-commit hooks
- **`security-check`** - Security scanning với bandit

### Health Checks
- **`health-check-database`** - Verify database connections
- **`health-check-camera`** - Verify camera connections

### Utilities
- **`clean-cache`** - Clean Python cache files
- **`install-dev-deps`** - Install development dependencies
- **`update-requirements`** - Update requirements.txt
- **`check-dependencies`** - Check for vulnerable packages

## 🚀 Usage

### In Cursor IDE
1. Open Command Palette: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type command name
3. Select command
4. Execute

### Sử dụng trong Chat với AI Agent
Đề cập command name trong chat:
```
Run code quality check
Check tests with coverage
Verify database health
```

## 📝 Custom Commands Format

Mỗi command trong `.cursor/commands.json` có cấu trúc:
```json
{
  "name": "command-name",
  "command": "actual-shell-command",
  "description": "What this command does"
}
```

## 🔧 Adding New Commands

Để thêm custom command mới:
1. Edit `.cursor/commands.json`
2. Add new command object
3. Use same format as existing commands

## 📚 Example Custom Commands

```bash
# Run specific test file
pytest tests/unit/test_database.py -c .config/pytest.ini -v

# Check code before commit
black src/ && isort src/ && pre-commit run --all-files

# Generate documentation
sphinx-build docs/ docs/_build/html
```

## 🎯 Best Practices

1. **Always run before commit:**
   - `code-quality-check`
   - `run-tests`
   - `pre-commit-check`

2. **Before deploying:**
   - `code-quality-check`
   - `run-tests-with-coverage`
   - `security-check`

3. **Weekly maintenance:**
   - `clean-cache`
   - `update-requirements`
   - `check-dependencies`

## 📖 References

- [Cursor Commands Documentation](https://cursor.com/docs/agent/chat/commands)
- See `docs/QUICK_START.md` for basic usage
- See `docs/DEVELOPER_CHECKLIST.md` for development workflow

