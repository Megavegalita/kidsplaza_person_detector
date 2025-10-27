# Light Review Existing Diffs

## Overview
Quick review of existing code changes (diffs) to understand context and recent modifications before making new changes.

## Purpose
- Understand what has changed recently
- Avoid conflicts with ongoing work
- Get context for related changes
- Identify patterns or issues in recent commits

## Steps

### 1. **View Recent Changes**
   ```bash
   # View recent commits
   git log --oneline -20
   
   # View diffs in branch
   git diff main...your-branch
   
   # View diff for specific commit
   git show <commit-hash>
   ```

### 2. **Review by File Type**
   ```bash
   # Python files only
   git diff main...your-branch -- '*.py'
   
   # Config files
   git diff main...your-branch -- 'config/*.json'
   
   # Test files
   git diff main...your-branch -- 'tests/**/*.py'
   ```

### 3. **Focus Areas**

#### **Critical Files**
   - [ ] Database connection code
   - [ ] Camera processing code
   - [ ] Detection algorithms
   - [ ] Configuration files
   - [ ] Error handling

#### **Documentation**
   - [ ] README updates
   - [ ] Docstring changes
   - [ ] API documentation
   - [ ] Configuration docs

#### **Tests**
   - [ ] New test files
   - [ ] Test case changes
   - [ ] Fixture updates
   - [ ] Coverage changes

### 4. **Look For Patterns**

#### **Quality Indicators**
   - [ ] Proper type hints added
   - [ ] Docstrings updated
   - [ ] Error handling improved
   - [ ] Tests added for new code

#### **Red Flags**
   - [ ] Hardcoded values/secrets
   - [ ] Missing error handling
   - [ ] Untested new code
   - [ ] Breaking changes not documented
   - [ ] Performance regressions

### 5. **Quick Checklist**

#### **For Modified Files**
   - [ ] Changes follow project standards
   - [ ] No obvious bugs introduced
   - [ ] Related files updated consistently
   - [ ] No duplicate code added

#### **For New Files**
   - [ ] Follows project structure
   - [ ] Has proper docstrings
   - [ ] Includes tests
   - [ ] No licensing issues

## Common Context Understanding

### Understanding Detection Logic Changes
When reviewing detection-related diffs:
- [ ] Accuracy implications clear
- [ ] Performance impact considered
- [ ] Edge cases handled
- [ ] Camera compatibility maintained

### Understanding Database Changes
When reviewing database-related diffs:
- [ ] Migrations included if schema changed
- [ ] Connection pooling handled
- [ ] Error handling for DB failures
- [ ] Indexes added where needed

### Understanding Camera Changes
When reviewing camera-related diffs:
- [ ] Resource cleanup implemented
- [ ] Error handling for camera failures
- [ ] RTSP connection handling robust
- [ ] Memory management proper

## Quick Review Commands

### View Specific Changes
```bash
# Changes to specific function
git log -p --all --full-history -- '**/file.py' | grep -A 10 -B 5 "function_name"

# Changes by author
git log --author="author-name" --oneline

# Changes in date range
git log --since="2 weeks ago" --until="now"

# File change statistics
git diff main...your-branch --stat
```

### Focused Reviews
```bash
# Only additions
git diff main...your-branch --diff-filter=A

# Only deletions
git diff main...your-branch --diff-filter=D

# Only modifications
git diff main...your-branch --diff-filter=M
```

## Review Checklist

### Quick Scan (5 minutes)
- [ ] Look at diff stats (lines changed)
- [ ] Scan commit messages for context
- [ ] Check if tests updated
- [ ] Spot obvious issues

### Medium Review (15 minutes)
- [ ] Read through key changes
- [ ] Understand purpose of changes
- [ ] Check error handling
- [ ] Verify test coverage

### Deep Review (30+ minutes)
- [ ] Understand business logic changes
- [ ] Review edge cases
- [ ] Consider performance implications
- [ ] Check for security issues

## Common Questions to Answer

1. **What is the purpose of these changes?**
   - Check commit messages
   - Look for related issues/PRs
   - Ask original author if unclear

2. **Are there any risks?**
   - Breaking changes?
   - Performance impact?
   - Security concerns?

3. **Is testing adequate?**
   - Tests added?
   - Edge cases covered?
   - Integration tests pass?

4. **Are related files consistent?**
   - Config files updated?
   - Documentation updated?
   - Database migrations included?

## Using Diff Tools

### VS Code / Cursor
```bash
# Open in editor
git diff main...your-branch

# View specific file
code -d main..your-branch src/modules/example.py
```

### Command Line
```bash
# Side-by-side diff
git diff --color-words main...your-branch

# Unified diff with context
git diff -U 3 main...your-branch
```

## Notes Template

```markdown
# Diff Review Notes

## Files Changed
- [File 1]: [Brief summary]
- [File 2]: [Brief summary]

## Key Changes
1. [Change 1]
2. [Change 2]

## Concerns
- [Concern 1]
- [Concern 2]

## Questions
- [Question 1]
- [Question 2]

## Action Items
- [ ] [Item 1]
- [ ] [Item 2]
```

