# Onboard New Developer

## Overview
Complete onboarding process for new developers joining the Person Detector project, ensuring they can contribute effectively from day one.

## Phase 1: Environment Setup (Day 1)

### 1. **Access & Permissions**
   - [ ] Repository access granted (GitHub/GitLab)
   - [ ] CI/CD access configured
   - [ ] Database credentials provided (securely)
   - [ ] Camera access credentials (if needed)
   - [ ] VPN/Network access (if applicable)

### 2. **Local Development Setup**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd person_detector
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   install-dev-deps
   
   # Verify installation
   python --version
   pip list
   ```

### 3. **IDE Setup**
   - [ ] Open project in Cursor (or preferred IDE)
   - [ ] Install Python extension
   - [ ] Configure interpreter (select venv)
   - [ ] Install recommended extensions:
     - Python
     - Pylance
     - Python Docstring Generator
     - autoDocstring

### 4. **Configuration**
   ```bash
   # Setup pre-commit hooks
   pre-commit install
   
   # Verify configuration
   ls .config/
   
   # Test setup
   python --version
   ```

### 5. **Initial Verification**
   ```bash
   # Run health checks
   health-check-database
   health-check-camera
   
   # Verify code quality tools
   format-code
   run-linting
   ```

## Phase 2: Understanding the Project (Days 2-3)

### 1. **Read Documentation**
   - [ ] README.md (project overview)
   - [ ] docs/QUICK_START.md (getting started)
   - [ ] docs/DEVELOPER_CHECKLIST.md (development guidelines)
   - [ ] docs/standards/project_structure.md (project organization)
   - [ ] docs/standards/FILE_CREATION_REQUIREMENTS.md (file templates)

### 2. **Understand Architecture**
   - [ ] Review project structure (`src/`, `tests/`, `config/`)
   - [ ] Understand database schema (PostgreSQL)
   - [ ] Understand caching layer (Redis)
   - [ ] Review camera processing flow (OpenCV)
   - [ ] Check existing scripts and their purposes

### 3. **Key Technologies**
   - [ ] Python 3.11+ fundamentals
   - [ ] FastAPI basics (if using API)
   - [ ] PostgreSQL and psycopg2
   - [ ] Redis for caching
   - [ ] OpenCV for image processing
   - [ ] RTSP camera protocols

### 4. **Run Existing Code**
   ```bash
   # Run test scripts
   python src/scripts/verify_database_health.py
   python src/scripts/verify_camera_health.py
   python src/scripts/display_camera.py
   
   # Run tests
   run-tests
   ```

## Phase 3: Development Workflow (Days 4-5)

### 1. **Git Workflow**
   ```bash
   # Branch naming convention
   feature/feature-name
   bugfix/description
   hotfix/description
   
   # Create feature branch
   git checkout -b feature/first-contribution
   
   # Make small changes
   git add .
   git commit -m "feat: your first contribution"
   git push origin feature/first-contribution
   ```

### 2. **Code Quality Workflow**
   ```bash
   # Before committing
   format-code
   run-linting
   run-type-checking
   run-tests
   
   # If using pre-commit
   pre-commit-check
   ```

### 3. **Using Cursor Commands**
   Learn to use these commands:
   - `format-code` - Format your code
   - `run-linting` - Check code style
   - `run-tests` - Run test suite
   - `code-quality-check` - Full quality check
   - `clean-cache` - Clean Python cache

### 4. **Create First Contribution**
   - [ ] Pick an issue or create a small feature
   - [ ] Use `setup-new-feature` command
   - [ ] Follow project structure
   - [ ] Write tests
   - [ ] Submit PR using `create-pr` command

## Phase 4: Deep Dive (Week 2)

### 1. **Codebase Exploration**
   ```bash
   # Find specific functionality
   grep -r "function_name" src/
   
   # Understand data flow
   # Trace from camera input to database output
   
   # Review existing modules
   ls -R src/
   ```

### 2. **Testing Deep Dive**
   - [ ] Review existing test structure
   - [ ] Understand pytest fixtures
   - [ ] Learn mocking patterns used
   - [ ] Run coverage report (`run-tests-with-coverage`)

### 3. **Common Tasks Practice**
   ```bash
   # Debug a test failure
   run-all-test-and-fix
   
   # Review code
   code-review-checklist
   
   # Submit changes
   create-pr
   ```

## Phase 5: Become Productive (Week 3+)

### 1. **Start Contributing**
   - [ ] Pick issues labeled "good first issue"
   - [ ] Follow development workflow
   - [ ] Request code reviews
   - [ ] Apply feedback

### 2. **Team Integration**
   - [ ] Attend standups/daily meetings
   - [ ] Ask questions regularly
   - [ ] Share knowledge and learnings
   - [ ] Contribute to documentation

### 3. **Master the Tools**
   - [ ] Efficiently use Cursor commands
   - [ ] Debug effectively
   - [ ] Write comprehensive tests
   - [ ] Perform thorough code reviews

## Essential Commands Reference

### Daily Development
```bash
# Format code
format-code

# Run tests
run-tests

# Check code quality
code-quality-check

# Health checks
health-check-database
health-check-camera
```

### Before Submission
```bash
# Full quality check
code-quality-check

# Security check
security-check

# Run all tests
run-tests-with-coverage

# Clean cache
clean-cache
```

## Common Issues and Solutions

### Issue: Import Errors
```bash
# Solution: Make sure you're in venv
source venv/bin/activate

# Reinstall dependencies
install-dev-deps
```

### Issue: Database Connection Failed
```bash
# Check database config
cat config/database.json

# Verify database is running
health-check-database
```

### Issue: Camera Not Working
```bash
# Check camera config
cat input/cameras_config/*.json

# Verify camera health
health-check-camera
```

### Issue: Tests Failing
```bash
# Clean cache and retry
clean-cache
run-tests

# Run specific test for debugging
pytest tests/unit/test_specific.py -v
```

## Resources

### Documentation
- Project README: `README.md`
- Quick Start: `docs/QUICK_START.md`
- Standards: `docs/standards/`
- Templates: `templates/`

### External Resources
- Python 3.11 Docs: https://docs.python.org/3/
- FastAPI Docs: https://fastapi.tiangolo.com/
- OpenCV Docs: https://opencv.org/
- PostgreSQL Docs: https://www.postgresql.org/docs/

## Onboarding Checklist

### Week 1
- [ ] Environment setup complete
- [ ] Documentation read
- [ ] First contribution made
- [ ] Tests passing locally
- [ ] Code review received

### Week 2
- [ ] Multiple contributions made
- [ ] Understand project architecture
- [ ] Comfortable with development workflow
- [ ] Code reviews given

### Week 3
- [ ] Productive contributor
- [ ] Mentoring others
- [ ] Suggesting improvements

## Support

### Getting Help
- Slack/Teams channel for questions
- Pair programming sessions
- Office hours with senior developers
- Documentation and comments in code

### Questions to Ask
- How does the detection algorithm work?
- What's the expected performance?
- How are database connections managed?
- What's the camera processing pipeline?

## Success Metrics
- [ ] Environment setup working
- [ ] Can run all tests successfully
- [ ] First PR submitted and approved
- [ ] Comfortable with development workflow
- [ ] Contributing meaningful code
- [ ] Code reviews accepted

