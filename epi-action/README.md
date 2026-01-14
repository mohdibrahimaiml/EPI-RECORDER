# EPI GitHub Action

The "Invisible" Compliance Hook for AI Engineering.
Automatically record, sign, and verify AI execution in your CI/CD pipeline.

## Usage

Add this to your `.github/workflows/ci.yml`:

```yaml
steps:
  - uses: actions/checkout@v3
  
  # Run your tests with EPI recording
  - name: Run Tests & Record Evidence
    uses: ./epi-action  # Or uses: epilabs/epi-action@v1
    with:
      command: 'pytest tests/'
      output: 'compliance-evidence.epi'
      install-python: 'true'
```

## Inputs

| Input | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `command` | The shell command to run and record. | **Yes** | - |
| `output` | The filename for the generated evidence package. | No | `evidence.epi` |
| `install-python` | Set to 'true' to install Python 3.10 automatically. | No | `false` |
| `upload-artifact` | Upload the .epi file to GitHub Actions Artifacts. | No | `true` |

## How It Works

1.  Installs `epi-recorder`.
2.  Wraps your `command` with `epi record`.
3.  Captures all LLM calls, network requests, and CLI output.
4.  Cryptographically signs the package.
5.  Uploads the `.epi` file as a build artifact for review.
