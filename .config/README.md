# Configuration Files

Thư mục này chứa các file cấu hình cho code quality tools.

## 📁 Contents

- `.pylintrc` - Pylint configuration for advanced linting
- `.flake8` - Flake8 configuration for PEP 8 checking
- `mypy.ini` - MyPy configuration for type checking
- `pytest.ini` - Pytest configuration for testing
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

## 🔗 Symlinks

Các file này được symlink về root directory để tools có thể tự động tìm thấy:
```bash
.pylintrc -> .config/.pylintrc
.flake8 -> .config/.flake8
mypy.ini -> .config/mypy.ini
pytest.ini -> .config/pytest.ini
.pre-commit-config.yaml -> .config/.pre-commit-config.yaml
```

## 🔧 Usage

### Check Configuration

```bash
# Pylint
pylint src/ --rcfile=.config/.pylintrc

# Flake8
flake8 src/ --config=.config/.flake8

# MyPy
mypy src/ --config-file=.config/mypy.ini

# Pytest
pytest tests/ -c .config/pytest.ini
```

### Tự động

Vì có symlinks, các tools sẽ tự động tìm thấy config:
```bash
pylint src/
flake8 src/
mypy src/
pytest tests/
```

## 📝 Customization

Chỉnh sửa config files trong `.config/` directory. Symlinks sẽ tự động reflect changes.

## 🔄 Updating Configs

Nếu thay đổi config:
1. Edit file trong `.config/` directory
2. Changes tự động reflect qua symlinks
3. Không cần restart hoặc reload

## 📚 References

- See `.config/.pylintrc` for Pylint options
- See `.config/.flake8` for Flake8 options
- See `.config/mypy.ini` for MyPy options
- See `.config/pytest.ini` for Pytest options
- See `.config/.pre-commit-config.yaml` for pre-commit hooks

