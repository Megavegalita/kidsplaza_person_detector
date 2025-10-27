# Code Review Checklist

## Overview
Comprehensive checklist for reviewing Python backend code, ensuring quality, security, and best practices.

## Pre-Review Checklist

### 1. **Environment Setup**
   - [ ] Latest code pulled from target branch
   - [ ] Dependencies installed (`pip install -r requirements-dev.txt`)
   - [ ] Tests pass on clean branch (`run-tests`)
   - [ ] No linting errors (`run-linting`)

### 2. **Documentation Review**
   - [ ] Read PR description thoroughly
   - [ ] Review related tickets/issues
   - [ ] Check test plan and acceptance criteria

## Code Review Checklist

### Code Quality

#### **Structure & Organization**
- [ ] Code follows project structure standards (`docs/standards/project_structure.md`)
- [ ] Logical organization and clear separation of concerns
- [ ] No unnecessary complexity or over-engineering
- [ ] Proper module and file naming

#### **Style & Formatting**
- [ ] Follows PEP 8 style guide
- [ ] Consistent indentation (4 spaces)
- [ ] Line length within limits (< 100 chars)
- [ ] Proper spacing and formatting (`format-code` check)

#### **Type Hints & Documentation**
- [ ] All function parameters have type hints
- [ ] Return types are annotated
- [ ] Google-style docstrings for public functions
- [ ] Docstrings include Args, Returns, and Raises sections

#### **Code Clarity**
- [ ] Meaningful variable and function names
- [ ] Clear logic flow
- [ ] No magic numbers (use constants)
- [ ] Comments explain 'why', not 'what'

### Best Practices

#### **Error Handling**
- [ ] No bare `except:` clauses
- [ ] Specific exception types caught
- [ ] Proper error messages
- [ ] Logging added where appropriate
- [ ] Graceful degradation for failures

#### **Security**
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] Parameterized queries (no SQL injection risk)
- [ ] Sanitized file paths
- [ ] Security check passed (`security-check`)

#### **Performance**
- [ ] Efficient algorithms and data structures
- [ ] No unnecessary database queries
- [ ] Proper use of async/await for I/O operations
- [ ] Caching implemented where appropriate

### Testing

#### **Test Coverage**
- [ ] Unit tests for new functions
- [ ] Integration tests for new features
- [ ] Edge cases and error conditions tested
- [ ] Test coverage maintained (>80%)

#### **Test Quality**
- [ ] Tests are independent and isolated
- [ ] Proper use of fixtures and mocking
- [ ] Clear test names describing what they test
- [ ] No flaky or slow tests

### Database & External Services

#### **Database Operations**
- [ ] Proper use of connection context managers
- [ ] Transactions handled correctly
- [ ] No connection leaks
- [ ] Proper indexing considered
- [ ] Migration strategy for schema changes

#### **OpenCV & Camera**
- [ ] Proper resource cleanup (e.g., camera release)
- [ ] Error handling for camera failures
- [ ] Consider performance implications
- [ ] Memory management for image processing

### Project-Specific Concerns

#### **Person Detector Specific**
- [ ] Detection accuracy maintained or improved
- [ ] Performance impact acceptable
- [ ] Camera health checks updated if needed
- [ ] Database health checks still valid

#### **Configuration**
- [ ] Environment variables used appropriately
- [ ] Config file changes documented
- [ ] Backward compatibility considered

## Reviewer Actions

### 1. **Initial Review**
   ```bash
   # Check out the branch
   git fetch origin
   git checkout feature-branch-name
   
   # Run automated checks
   code-quality-check
   run-tests
   security-check
   ```

### 2. **Provide Feedback**
   - Use inline comments for specific issues
   - Add PR-level comments for broader concerns
   - Mark as Request Changes for blocking issues
   - Approve when satisfied

### 3. **Code-Approved Checklist**
   - [ ] All automated checks pass
   - [ ] Manual review completed
   - [ ] Tests added/updated as needed
   - [ ] Documentation updated
   - [ ] No blocking issues remain
   - [ ] LGTM (Looks Good To Me) from reviewer

## Common Issues to Watch For

### Security Red Flags
- [ ] SQL injection risks
- [ ] Path traversal vulnerabilities
- [ ] Exposed secrets or credentials
- [ ] Inadequate input validation

### Performance Red Flags
- [ ] N+1 query problems
- [ ] Inefficient loops or algorithms
- [ ] Missing indexes
- [ ] Memory leaks in image processing

### Python-Specific Red Flags
- [ ] Mutable default arguments
- [ ] Improper exception handling
- [ ] Missing `__init__.py` files
- [ ] Circular imports
- [ ] Resource leaks (files, connections)

## Post-Review

### **After Approval**
- [ ] Merge conflicts resolved if any
- [ ] Final CI/CD checks pass
- [ ] Ready for merge

### **After Merge**
- [ ] Close related tickets
- [ ] Update documentation if needed
- [ ] Monitor for issues in production

