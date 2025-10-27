# Configuration Files

Thư mục này chứa các file cấu hình cho code quality tools.

## 📁 Contents

- `.pylintrc` - Pylint configuration for advanced linting
- `.flake8` - Flake8 configuration for PEP 8 checking
- `mypy.ini` - MyPy configuration for type checking
- `pytest.ini` - Pytest configuration for testing
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

## 🔧 Usage

### Option 1: Specify Config Path (Recommended)

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

### Option 2: Create Local Symlinks

Nếu muốn tools tự động tìm thấy config, tạo symlinks trong workspace:

```bash
# Create symlinks (one time only)
ln -s .config/.pylintrc .pylintrc
ln -s .config/.flake8 .flake8
ln -s .config/mypy.ini mypy.ini
ln -s .config/pytest.ini pytest.ini
ln -s .config/.pre-commit-config.yaml .pre-commit-config.yaml

# Then use normally
pylint src/
flake8 src/
mypy src/
pytest tests/
```

**Note**: Symlinks không được commit vào git. Mỗi developer cần tự tạo trên local.

## 📝 Customization

Chỉnh sửa config files trong `.config/` directory.

**Lưu ý**: Nếu đã tạo symlinks, chỉ cần edit files trong `.config/` - changes sẽ tự động reflect qua symlinks.

## 🔄 Updating Configs

Để thay đổi config:
1. Edit file trong `.config/` directory (không edit symlink)
2. Changes sẽ tự động có hiệu lực cho lần chạy tiếp theo
3. Không cần restart tools

## 📚 References

- See `.config/.pylintrc` for Pylint options
- See `.config/.flake8` for Flake8 options
- See `.config/mypy.ini` for MyPy options
- See `.config/pytest.ini` for Pytest options
- See `.config/.pre-commit-config.yaml` for pre-commit hooks

