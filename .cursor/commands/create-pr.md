# Create Pull Request

## Overview
Create a well-structured pull request following best practices for the Person Detector project.

## Pre-Submission Checklist

### 1. **Code Quality**
   - [ ] All code changes reviewed
   - [ ] Format code (`format-code`)
   - [ ] Linting passed (`run-linting`)
   - [ ] Type checking passed (`run-type-checking`)
   - [ ] Security check passed (`security-check`)
   - [ ] All tests pass (`run-tests`)

### 2. **Documentation**
   - [ ] Docstrings updated for new/changed functions
   - [ ] README updated if needed
   - [ ] Breaking changes documented
   - [ ] Migration guide added if applicable

### 3. **Testing**
   - [ ] New tests added for new features
   - [ ] Existing tests updated if needed
   - [ ] Coverage maintained (>80%)
   - [ ] Integration tests pass

### 4. **Branch Status**
   - [ ] Up to date with target branch (main/develop)
   - [ ] No merge conflicts
   - [ ] Recent commits properly formatted
   - [ ] Commit messages follow conventions

## Creating the PR

### 1. **Prepare Branch**
   ```bash
   # Ensure up to date
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   
   # Final quality check
   code-quality-check
   run-tests
   ```

### 2. **Push Branch**
   ```bash
   git push origin your-feature-branch
   ```

### 3. **Create PR on GitHub/GitLab**
   - Navigate to repository
   - Click "New Pull Request" or "Create Merge Request"
   - Select base branch (main/develop)
   - Select your feature branch

## PR Description Template

```markdown
## Summary
[Brief description of changes - 1-2 sentences]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Performance improvement
- [ ] Documentation update
- [ ] Refactoring

## Related Tickets
Closes #[issue-number]
Related to #[issue-number]

## Changes Made
- [Change 1]
- [Change 2]
- [Change 3]

## Testing
- [x] Unit tests added/updated
- [x] Integration tests added/updated
- [x] Manual testing completed
- [x] All tests passing

Test cases covered:
- Test case 1 description
- Test case 2 description

## Screenshots/Video (if applicable)
[Add screenshots or demo video here]

## Database Changes
- [ ] No database changes
- [x] Schema changes (migration file included: `migrations/xxx.sql`)
- [ ] Data migration needed

## Configuration Changes
- [ ] No configuration changes
- [x] New environment variables: `VAR_NAME`
- [x] Updated config files: `config/database.json`

## Security Considerations
- [ ] No security impact
- [x] Security review completed
- [x] Input validation added
- [ ] Security audit findings addressed

## Performance Impact
- [ ] No performance impact
- [x] Performance tested and optimized
- [x] Impact: [describe impact]

## Deployment Notes
- [ ] Standard deployment
- [x] Requires deployment steps:
  1. [Step 1]
  2. [Step 2]

## Reviewer Checklist
- [ ] Code follows project standards
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] Security considerations addressed
- [ ] Performance impact acceptable

## Self-Review
- [x] Followed PEP 8 style guide
- [x] Added type hints for all functions
- [x] Added docstrings for public APIs
- [x] No hardcoded secrets
- [x] Error handling implemented
- [x] Logging added where appropriate
```

## Pre-Submit Commands

Run these before creating the PR:

```bash
# 1. Format and style check
format-code
code-quality-check

# 2. Run tests with coverage
run-tests-with-coverage

# 3. Security check
security-check

# 4. Dependency check
check-dependencies

# 5. Clean cache
clean-cache

# 6. Final verification
run-tests
```

## Post-Submission

### 1. **Monitor PR**
   - Wait for CI/CD to pass
   - Respond to automated feedback
   - Address any blocking issues

### 2. **Respond to Review**
   - Use `address-github-pr-comments` command
   - Be responsive and professional
   - Apply feedback systematically

### 3. **After Approval**
   - Rebase if needed
   - Squash commits if requested
   - Ensure CI/CD passes
   - Merge when ready

## Branch Naming Conventions

Follow these patterns:
- **Features**: `feature/description`
- **Bugs**: `bugfix/description`
- **Hotfixes**: `hotfix/description`
- **Documentation**: `docs/description`
- **Refactoring**: `refactor/description`

Example: `feature/person-detector-optimization`

## Commit Message Convention

Format: `<type>: <subject>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example: `feat: add person detection cache layer`

