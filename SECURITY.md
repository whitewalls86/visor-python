# Security Policy

## Supported Versions

Security fixes are provided for the latest released version of `visor-python`.

Because this project is pre-1.0, users should pin to a specific minor version and
review the changelog before upgrading.

## Reporting A Vulnerability

Please do not open a public GitHub issue for security vulnerabilities.

Use GitHub's private vulnerability reporting for this repository:

https://github.com/whitewalls86/visor-python/security/advisories/new

If private reporting is unavailable, contact the maintainer listed in
`pyproject.toml`.

Do not include API keys, secrets, or sensitive live API response data in reports.

## API Keys

`visor-python` reads `VISOR_API_KEY` from the environment by default. The SDK does
not require API keys to be stored in source code.

Recommended practices:

- Store API keys in environment variables or a secret manager.
- Do not commit `.env` files.
- Do not print API keys in logs.
- Rotate any key that may have been exposed.
