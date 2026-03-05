# Security Policy

## Supported Versions

| Version | Support          |
|---------|------------------|
| main    | ✅ Active        |
| < main  | ❌ No support    |

## Reporting a Vulnerability

**DO NOT open a public issue** to report security vulnerabilities.

Instead:

1. Email the project maintainers with the subject
   `[SECURITY] ESPAlert — <brief description>`.
2. Include:
   - Detailed description of the vulnerability.
   - Steps to reproduce.
   - Potential impact.
   - Possible fix (if you know one).
3. You will receive a response within **72 hours**.

## Project Security Practices

- API keys and secrets are **never** stored in the repository.
- All passwords are hashed with **bcrypt**.
- JWT tokens have configurable expiration.
- The API implements rate limiting with **SlowAPI + Redis**.
- Security headers (HSTS, CSP, X-Frame-Options) are configured in both
  FastAPI middleware and Nginx.
- User data complies with **GDPR/LOPDGDD** (data export and deletion endpoints).
- Docker containers run with **non-root user** (`appuser`).

## Responsible Disclosure

We follow a coordinated disclosure policy. We appreciate giving us reasonable
time to fix the vulnerability before making it public.

All valid security reports will be acknowledged in the CHANGELOG or in the
credits of the corresponding release.
