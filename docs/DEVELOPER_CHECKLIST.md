# Developer Checklist

Checklist bắt buộc khi tạo file mới hoặc sửa đổi code.

## 📝 Trước Khi Code

### Planning
- [ ] Đã xác định rõ requirements
- [ ] Đã review design với team (nếu cần)
- [ ] Đã chọn đúng template cho file type
- [ ] Đã hiểu rõ coding standards

### Setup
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Pre-commit hooks installed

---

## 💻 Khi Code

### Code Quality
- [ ] Tuân thủ PEP 8 style guide
- [ ] Không có magic numbers/strings
- [ ] Đã loại bỏ duplicate code
- [ ] Functions nhỏ gọn, single responsibility
- [ ] Không quá complexity (Cyclomatic complexity < 15)

### Documentation
- [ ] Module docstring added
- [ ] Class docstrings added
- [ ] Public methods có docstrings
- [ ] Complex logic có comments
- [ ] TODO comments cho future work

### Type Hints
- [ ] Tất cả functions có type hints
- [ ] Return types specified
- [ ] Parameters có types
- [ ] Using `typing` module

### Error Handling
- [ ] Specific exceptions caught (không bare except)
- [ ] Errors được log properly
- [ ] User-friendly error messages
- [ ] Cleanup resources (context managers)

### Security
- [ ] Không hardcode secrets
- [ ] Input validation implemented
- [ ] SQL injection prevention (parameterized queries)
- [ ] Path traversal prevention
- [ ] File size limits

---

## ✅ Testing

### Unit Tests
- [ ] Unit tests written cho mọi function
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Mock external dependencies
- [ ] Test coverage > 80%

### Integration Tests
- [ ] Integration tests written (if applicable)
- [ ] Database operations tested
- [ ] API endpoints tested (if applicable)
- [ ] External services mocked

### Test Quality
- [ ] Tests are independent
- [ ] Tests are fast
- [ ] Tests are maintainable
- [ ] Clear test names
- [ ] Arrange-Act-Assert pattern

---

## 🔍 Code Review

### Before Commit
- [ ] Code formatted với Black
- [ ] Imports sorted với isort
- [ ] No linter errors:
  - [ ] Flake8 passes
  - [ ] Pylint passes
  - [ ] MyPy passes
- [ ] All tests pass
- [ ] Coverage meets requirements

### Pre-commit Hooks
```bash
pre-commit run --all-files
```
- [ ] All hooks pass
- [ ] No auto-fix issues

### Manual Checks
- [ ] Code reviewed by yourself
- [ ] No commented-out code left
- [ ] No debug prints left
- [ ] No credentials in code
- [ ] Config files updated (if needed)

---

## 📦 Commit & Push

### Commit Message
```bash
# Format: <type>: <subject>
# Types: feat, fix, docs, style, refactor, test, chore
# Examples:
feat: Add database health check script
fix: Resolve camera connection timeout
docs: Update README with usage examples
```

### Commit Checklist
- [ ] Commit message is clear và descriptive
- [ ] Related files committed together
- [ ] No unnecessary files included
- [ ] .gitignore updated (if needed)

### Before Push
- [ ] Pull latest changes first
- [ ] Resolve conflicts (if any)
- [ ] Run tests again
- [ ] Review diff

---

## 🚀 After Push

### CI/CD
- [ ] CI pipeline passes
- [ ] Tests pass on CI
- [ ] Code quality checks pass
- [ ] Deployment successful (if applicable)

### Documentation
- [ ] README updated (if needed)
- [ ] API docs updated (if applicable)
- [ ] Configuration docs updated (if needed)
- [ ] CHANGELOG updated (if applicable)

---

## 🔧 Development Tools

### Daily Workflow
```bash
# 1. Start working
git pull origin main
source venv/bin/activate

# 2. Create/modify code
# Make changes...

# 3. Quality checks
black src/
isort src/
flake8 src/
pylint src/
mypy src/

# 4. Run tests
pytest tests/

# 5. Commit
git add .
git commit -m "feat: Description"
git push origin main
```

### Weekly Tasks
- [ ] Review dependencies for updates
- [ ] Update requirements.txt if needed
- [ ] Review and fix TODOs
- [ ] Code cleanup
- [ ] Documentation review

---

## 🐛 Debugging Checklist

### When Debugging
- [ ] Added logging statements
- [ ] Used debugger (if needed)
- [ ] Reproduced issue locally
- [ ] Identified root cause
- [ ] Fixed issue properly
- [ ] Added test to prevent regression
- [ ] Removed debug code before commit

### Common Issues
- [ ] Import errors → Check PYTHONPATH
- [ ] Type errors → Check type hints
- [ ] Connection errors → Check config
- [ ] Test failures → Run specific test

---

## 📚 Reference Documents

- **Best Practices**: `docs/standards/python_production_best_practices.md`
- **File Requirements**: `docs/standards/FILE_CREATION_REQUIREMENTS.md`
- **Project Structure**: `docs/standards/project_structure.md`
- **Quick Start**: `docs/QUICK_START.md`
- **Templates**: `templates/` directory

---

## ⚠️ Red Flags (Avoid!)

### Code Quality
- ❌ Bare `except:` clauses
- ❌ Magic numbers without constants
- ❌ Functions > 100 lines
- ❌ Deeply nested code (> 3 levels)
- ❌ Copy-paste code (DRY violation)

### Security
- ❌ Hardcoded secrets
- ❌ SQL with string concatenation
- ❌ File operations without validation
- ❌ Unvalidated user input

### Testing
- ❌ Tests without assertions
- ❌ Tests that depend on each other
- ❌ Tests that access real resources
- ❌ Missing edge case tests

### Documentation
- ❌ Functions without docstrings
- ❌ Missing type hints
- ❌ Outdated comments
- ❌ Missing error handling docs

---

## 🎯 Quick Commands Reference

```bash
# Format code
black src/
isort src/

# Linting
flake8 src/
pylint src/
mypy src/

# Testing
pytest                           # Run all tests
pytest tests/unit/              # Run unit tests only
pytest -v                        # Verbose output
pytest --cov=src                # With coverage
pytest tests/test_file.py -k test_name  # Specific test

# Pre-commit
pre-commit run --all-files      # Run all files
pre-commit run black            # Run specific hook

# Git
git status                       # Check status
git diff                         # Review changes
git add .                        # Stage changes
git commit -m "message"          # Commit
git push origin main             # Push

# Database health check
python src/scripts/verify_database_health.py

# Camera health check
python src/scripts/verify_camera_health.py
```

---

## 📞 Need Help?

- Check documentation in `docs/standards/`
- Review templates in `templates/`
- See examples in existing code
- Ask team members
- Check online resources

---

**Remember**: Code quality is everyone's responsibility! 🚀

