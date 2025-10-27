# Address GitHub PR Comments

## Overview
Systematically review and address all comments on an open pull request, ensuring thorough responses and necessary code changes.

## Steps

### 1. **Review all comments**
   - Read through all reviewer comments
   - Understand the context and intent
   - Check for any conflicting or overlapping feedback
   - Note any blocking vs. non-blocking comments

### 2. **Categorize feedback**
   - **Must fix**: Critical issues affecting functionality, security, or architecture
   - **Should fix**: Best practices, code quality improvements, or minor bugs
   - **Nice to have**: Suggestions for improvements or clarifications
   - **Questions**: Reviewer questions requiring explanation

### 3. **Address issues systematically**
   - Start with must-fix items
   - Fix related issues together to minimize commits
   - Add tests for new fixes when applicable
   - Run validation commands:
     ```bash
     # Run code quality checks
     format-code
     code-quality-check
     
     # Run tests
     run-tests
     ```

### 4. **Respond to all comments**
   - Acknowledge every comment
   - Explain reasoning for changes
   - Link commits/responses to specific comments
   - Request re-review when appropriate

### 5. **Update PR description if needed**
   - Update with changes made
   - Add any new context or considerations
   - Note any deferred issues for follow-up

## Response Template

```markdown
Thank you for the feedback! I've addressed the comment below:

[Summary of change]

✅ Addressed in commit: [commit hash]

Please let me know if this looks good or if you have any additional feedback.
```

## Checklist
- [ ] All must-fix comments resolved
- [ ] All should-fix comments addressed or acknowledged
- [ ] Tests updated/added where needed
- [ ] Code quality checks passed
- [ ] Responses posted to all comments
- [ ] PR ready for re-review

