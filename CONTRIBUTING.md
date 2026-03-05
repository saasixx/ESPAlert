# Contributing to ESPAlert

> 🇬🇧 **English** | [🇪🇸 Español](docs/es/CONTRIBUTING.md)

Thank you for your interest in contributing to **ESPAlert**! This document
explains the workflow, project conventions, and how to submit your changes efficiently.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Git Workflow](#git-workflow)
- [Code Conventions](#code-conventions)
- [Tests](#tests)
- [Pull Requests](#pull-requests)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

---

## Code of Conduct

This project is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you commit to respecting its standards.

## Getting Started

1. **Fork** the repository.
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/ESPAlert.git
   cd ESPAlert
   ```
3. Create a descriptive branch:
   ```bash
   git checkout -b feat/my-new-feature
   ```

## Development Environment

### Option A — Docker (recommended)

```bash
cp .env.example .env          # Adjust values if needed
docker compose up --build      # Start the entire stack
```

- **Frontend**: http://localhost:3000
- **API + Docs**: http://localhost:8000/docs

### Option B — Local (without Docker for frontend)

```bash
# Start only infrastructure + backend services
docker compose up db redis api worker beat -d

# Install frontend dependencies
npm install
npm run dev
```

### Requirements

| Tool   | Minimum Version |
|--------|-----------------|
| Node.js | 20 LTS          |
| Python | 3.12            |
| Docker | 24+             |
| npm    | 10+             |

## Git Workflow

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <brief description>

[optional body]

[optional footer]
```

### Allowed Types

| Type       | When to use                         |
|------------|-------------------------------------|
| `feat`     | New feature                         |
| `fix`      | Bug fix                             |
| `docs`     | Documentation only                  |
| `style`    | Formatting (no logic changes)       |
| `refactor` | Refactoring without functional change |
| `test`     | Add or fix tests                    |
| `chore`    | Maintenance tasks (CI, deps, etc.)  |
| `perf`     | Performance improvement             |

### Examples

```
feat(map): add wildfire layer
fix(api): correct GPS radius filter
docs(readme): update installation instructions
```

## Code Conventions

### Python (Backend — `apps/api/`)

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) with default rules.
- **Format**: Ruff format (Black-compatible).
- **Docstrings**: In English, Google style.
- **Types**: Use type hints for all public functions.

```bash
# Run linter
pip install ruff
ruff check apps/api/
ruff format apps/api/
```

### TypeScript/React (Frontend — `apps/web/`)

- **Linter**: ESLint with Next.js config.
- **Format**: Prettier (via ESLint).
- **Components**: Functional components with hooks.
- **Naming**: PascalCase for components, camelCase for hooks and utilities.

```bash
npm run lint
```

### Code Language

- **User Interface**: Spanish (primary), English available via i18n.
- **Source Code** (variables, functions, classes): In **English**.
- **Comments and Docstrings**: In **English**.
- **Commits and PRs**: English preferred, Spanish accepted.

## Tests

### Backend

```bash
cd apps/api
pip install -r requirements.txt pytest httpx
pytest -v
```

### Frontend

```bash
npm run turbo lint --filter=web
npm run turbo build --filter=web
```

## Pull Requests

1. Ensure your branch is up to date with `main`.
2. Verify that tests pass locally.
3. Write a clear change description.
4. Reference the related issue (if applicable): `Closes #123`.
5. Request review from at least one maintainer.

### PR Checklist

- [ ] My code follows project conventions.
- [ ] I've added tests for the changes (if applicable).
- [ ] Documentation is updated.
- [ ] Commits follow Conventional Commits format.
- [ ] I've tested the changes locally with Docker.

## Reporting Bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template and provide:

1. **Clear description** of the problem.
2. **Steps to reproduce** the error.
3. **Expected behavior** vs. **actual behavior**.
4. **Environment**: browser, OS, Docker version.
5. **Screenshots or logs** if relevant.

## Requesting Features

Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template and include:

1. **Problem** that the feature solves.
2. **Proposed solution** with as much detail as possible.
3. **Alternatives** you've considered.
4. **Mockups or diagrams** if applicable.

---

> **Questions?** Open a [Discussion](../../discussions) on GitHub or contact the maintainers.

Thank you for making ESPAlert a better project! 🛡️
