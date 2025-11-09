# Security Policy

## Reporting Vulnerabilities

Report vulnerabilities to: **afridiibrahim41@gmail.com**

This public-demo intentionally redacts signing and packaging internals. If you discover a secret accidentally committed, **STOP**. Do not add further commits. Contact the maintainer for remediation steps including history rewrite advice or rotating keys.

## Scope

This public demo repository contains:
- ✅ Safe demonstration code
- ✅ Documentation and examples
- ✅ Public API interfaces

This repository does NOT contain:
- ❌ Private keys or credentials
- ❌ Signing internals
- ❌ Production secrets
- ❌ Enterprise features

## What to Report

Please report:
- Accidentally committed secrets or credentials
- Security vulnerabilities in demo code
- Documentation that exposes sensitive implementation details
- Any PEM markers or key material in git history

## Response Timeline

- **Critical** (leaked credentials): Response within 24 hours
- **High** (security vulnerability): Response within 72 hours
- **Medium** (documentation issue): Response within 1 week
- **Low** (general security questions): Response within 2 weeks

## Full Security Contact

For enterprise security inquiries or NDA-covered source access:

**Email:** afridiibrahim41@gmail.com

## Security Best Practices

When using this demo:
1. Never commit actual API keys or credentials
2. Use environment variables for sensitive data
3. Review git history before making repositories public
4. Use `.gitignore` to exclude sensitive files
5. Rotate any keys that may have been accidentally exposed

## Disclosure Policy

We follow responsible disclosure:
1. Report the issue privately
2. We investigate and develop a fix
3. We release the fix
4. Public disclosure after fix is deployed

Thank you for helping keep this project secure!
