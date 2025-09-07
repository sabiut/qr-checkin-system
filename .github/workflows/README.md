# Claude Code Review GitHub Actions

This directory contains GitHub Actions workflows that enable Claude AI to automatically review your pull requests.

## 🤖 Available Workflows

### 1. `claude-pr-review.yml` (Recommended)
**Simple, reliable PR review workflow**
- Triggers on PR creation, updates, and reopens
- Reviews changed files (Python, JS, TS, etc.)
- Posts comprehensive review as PR comment
- Focuses on security, code quality, and best practices

### 2. `claude-code-review.yml`
**Official Claude Code Review action** (if available)
- Uses the official Anthropic action
- Configurable focus areas
- Multiple review styles

### 3. `claude-comprehensive-review.yml`
**Multi-stage review process**
- Separate jobs for security, architecture, Django, frontend, and performance
- More detailed but requires more API calls

## 🔧 Setup Instructions

### 1. Get Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and get your API key
3. Copy the API key

### 2. Add GitHub Secrets
1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** Your Anthropic API key from step 1

### 3. Enable GitHub Actions
1. Make sure GitHub Actions are enabled in your repository
2. The workflows will automatically trigger on new PRs

## 📋 What Claude Reviews

### Security Focus
- SQL injection vulnerabilities
- XSS prevention
- Authentication and authorization issues
- Input validation and sanitization
- Data exposure risks

### Code Quality
- Django/Python best practices
- Model design and ORM usage
- API design patterns
- Error handling
- Code organization and maintainability

### Performance
- Database query optimization
- Caching opportunities
- Algorithmic efficiency
- Memory usage patterns

### Architecture
- Design pattern usage
- Separation of concerns
- Modularity and reusability
- Integration patterns

## 🎯 Usage

1. **Create a PR** targeting the `main` branch
2. **Wait for the workflow** to run (usually 1-2 minutes)
3. **Check the PR comments** for Claude's review
4. **Address any issues** Claude identifies
5. **Push updates** to trigger a new review

## ⚙️ Customization

You can customize the workflows by editing the YAML files:

- **Focus areas:** Modify the review prompts
- **File patterns:** Change which files get reviewed
- **Review depth:** Adjust the token limits and detail level
- **Multiple reviews:** Enable/disable different workflow jobs

## 🔍 Example Review Output

Claude will post comments like:

```markdown
## 🤖 Claude Code Review

### ✅ Security
No major security vulnerabilities found. Good use of Django's built-in protections.

### ⚠️ Code Quality Issues
1. **Line 45:** Consider using `select_related()` to optimize this database query
2. **Line 128:** This view method is quite long - consider breaking it into smaller functions

### 🎯 Suggestions
- Add input validation for the email field
- Consider caching the user profile lookup
- Document the gamification point calculation logic

### 💡 Overall Assessment
Well-structured code following Django conventions. The feedback system integration is clean and maintainable.
```

## 🚨 Important Notes

- **API Costs:** Each review uses Anthropic API calls (typically $0.01-$0.10 per review)
- **Rate Limits:** Be aware of API rate limits for high-frequency PRs
- **File Size:** Very large diffs may be truncated to stay within token limits
- **Privacy:** Code diffs are sent to Anthropic's servers for review

## 🛠️ Troubleshooting

### Workflow not running?
- Check that GitHub Actions are enabled
- Verify the workflow file syntax
- Ensure secrets are properly configured

### API errors?
- Verify your Anthropic API key is correct
- Check your API usage limits and billing
- Review the workflow logs for specific error messages

### No review comments?
- Check if the workflow completed successfully
- Verify GitHub token permissions
- Look for errors in the Actions logs

## 🔄 Updates

To update the workflows:
1. Modify the YAML files in this directory
2. Commit and push the changes
3. The updated workflows will be used for subsequent PRs