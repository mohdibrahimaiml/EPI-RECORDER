# Public Demo PR Checklist

## Security Verification
- [ ] I confirm this PR creates a `public-demo` branch with demo artifacts only.
- [ ] No private keys, secrets, PEM markers, or credentials are included.
- [ ] Sensitive components are listed in `PRIVATE_COMPONENTS.md`.
- [ ] I have searched git history for sensitive data using: `git log --all -p | grep -E "PRIVATE KEY|BEGIN.*KEY|SECRET|TOKEN"`

## Functionality Verification
- [ ] `demo/api_demo.py` runs locally without external tokens.
- [ ] `README_DEMO.md` explains redactions and how to request full access.
- [ ] All documentation references are public or clearly marked as private/redacted.
- [ ] Demo code is standalone and doesn't depend on private modules.

## PR Description

### Summary of changes
<!-- Describe what this PR adds or changes -->

### Files added
<!-- List new files with brief description of each -->

### Files removed/redacted
<!-- List any files removed or content redacted for security -->

### How to run demo locally
```bash
# Provide step-by-step instructions
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python demo/api_demo.py
```

### How to request full repo under NDA
Contact afridiibrahim41@gmail.com with:
- Your organization name
- Use case description
- NDA acceptance

## Additional Notes
<!-- Any other context, screenshots, or relevant information -->
