# Private components (not published in public-demo)

The following components remain private to protect IP, security, and commercial features:

## Cryptographic Components
- Ed25519 key generation and storage
- Signing internals (key handling, signature creation)
- Signature verification logic
- Key management utilities

## Packaging Internals
- ZIP archive construction with signature integration
- Manifest generation with cryptographic hashes
- File content validation and integrity checks
- `.epi` format assembly

## SDK Integration
- OpenAI advanced SDK auto-patching logic
- Thread-local storage for context management
- Automatic request/response interception
- Streaming response capture

## Testing & Quality Assurance
- Full test suite (191 tests, 87% coverage)
- Integration tests with live API mocking
- User workflow simulation tests
- CI/CD pipeline configurations

## Build & Distribution
- PyPI packaging scripts
- Build automation (build.sh, build.ps1)
- Distribution artifacts (wheels in dist/)
- Version management and changelog generation

## Security-Sensitive
- Any credentials, tokens, or secret material
- Private key files (.pem, .key)
- API keys or service tokens
- Production deployment configurations

## To Request Access

Full source and enterprise features available under NDA.

**Contact:** afridiibrahim41@gmail.com

**What we provide under NDA:**
- Complete source code with all private components
- Full test suite and coverage reports
- Build scripts and CI/CD configurations
- Production deployment guides
- Enterprise support and custom integrations
