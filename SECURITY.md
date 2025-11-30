# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### Email

Send an email to: **AnthemFlynn@users.noreply.github.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### GitHub Private Security Advisory

Use [GitHub's private vulnerability reporting](https://github.com/AnthemFlynn/toolable/security/advisories/new):

1. Go to the Security tab
2. Click "Report a vulnerability"
3. Fill out the form with details

## Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next release cycle

## Security Considerations for Tool Developers

If you're building tools with Toolable, please review the security guidelines in [README.md](README.md#security-considerations):

### High-Risk Areas

1. **Code Execution**
   - Never use `eval()` or `exec()` on user input
   - Use `ast.literal_eval()` for safe literal evaluation
   - Validate file paths to prevent directory traversal

2. **Resource Limits**
   - Timeout values are capped at 600 seconds
   - Working directories are validated before use
   - Use `dry_run` for testing without side effects

3. **Input Validation**
   - Always validate user input via Pydantic models
   - Implement `pre_validate()` for I/O-dependent checks
   - Use `to_log_safe()` to redact sensitive data from logs

4. **External Tools (ToolRegistry)**
   - Only load tools from trusted sources
   - Subprocess calls have 5-second timeouts
   - Malformed tool responses are handled gracefully

## Known Security Considerations

### Resource URI Pattern Matching

Resource URI patterns use regex matching with proper escaping and anchoring:
- All literal characters are escaped (`.`, `*`, `[`, etc.)
- Patterns use `fullmatch` to prevent partial matches
- Path traversal attempts are blocked

### Subprocess Execution

The `ToolRegistry` executes external tools via subprocess:
- 5-second timeout on discovery calls
- Invalid responses handled gracefully with warnings
- No shell=True (prevents shell injection)

### Timeout Handling

Tools can set execution timeouts:
- Maximum timeout: 600 seconds (10 minutes)
- Cross-platform implementation (signal.alarm on Unix, threading.Timer on Windows)
- Proper cleanup in all code paths

## Disclosure Policy

We follow coordinated disclosure:
1. Reporter notifies maintainers privately
2. Maintainers confirm and develop fix
3. Fix is released
4. Public disclosure after users have time to update (typically 7-14 days)
5. Reporter credited (unless they prefer anonymity)

## Security Updates

Security updates will be:
- Announced in GitHub Security Advisories
- Tagged with severity level (Critical/High/Medium/Low)
- Documented in CHANGELOG.md
- Released as patch versions ASAP

## Hall of Fame

We appreciate security researchers who help keep Toolable secure. Researchers who responsibly disclose vulnerabilities will be credited here (with permission):

- None yet - be the first!

## Contact

For security concerns that don't rise to the level of a vulnerability report:
- Open a GitHub Discussion
- Mention security concerns in issues (for non-sensitive topics)

Thank you for helping keep Toolable and its users safe!
