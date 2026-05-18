<div align="center">

<img src="https://sel2-2.ugent.be/favicon.ico" width="80" alt="VIERNULVIER logo" />

# VIERNULVIER Archive

**The digital archive of arts centre VIERNULVIER - search decades of culture in Ghent.**

[**Live website**](https://sel2-2.ugent.be/nl) · [**API Docs**](https://sel2-2.ugent.be/api/docs/) · [**Wiki**](https://github.com/SELab-2/viernulvier-2/wiki) · [**CMS**](https://sel2-2.ugent.be/admin/) · [**User Manual**](User%20Manual.pdf)

</div>

---

## Contents

- [About the project](#about-the-project)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
  - [Requirements](#requirements)
  - [Backend (native)](#backend-native)
  - [Frontend (native)](#frontend-native)
  - [Full stack with Docker Compose](#full-stack-with-docker-compose)
- [Environments](#environments)
- [Running tests](#running-tests)
- [Linting & formatting](#linting--formatting)
- [Data synchronisation](#data-synchronisation)
- [Deployment](#deployment)
- [Wiki](#wiki)

---

## About the project

VIERNULVIER is an arts centre in Ghent with a rich history of performances. That archive data was until now not publicly available via the main website - this application solves that.

**VIERNULVIER Archive** provides a searchable archive website where visitors can discover decades of cultural history: performances, series, locations, media and more - synchronised directly from the [VIERNULVIER/Peppered API](https://www.viernulvier.gent/api/docs#/).

```
viernulvier-2/
├── backend/        # Django REST API - domain apps, serializers, views, tests
├── frontend/       # React + TypeScript app built with Vite
├── infrastructure/ # Docker Compose, nginx, certbot configuration
└── wiki/           # Architecture notes and developer guides
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
└───────────────────────────┬─────────────────────────────────┘
                            │  HTTPS
┌───────────────────────────▼─────────────────────────────────┐
│                         nginx                               │
│         (reverse proxy + static frontend files)             │
└──────────┬────────────────────────────────┬─────────────────┘
           │ /api/*  /admin/*               │ /*
┌──────────▼──────────────┐     ┌───────────▼───────────────┐
│   Django REST Backend   │     │   React Frontend (Vite)   │
│   (Gunicorn + Python)   │     │   (static build)          │
└──────────┬──────────────┘     └───────────────────────────┘
           │
┌──────────▼──────────────┐     ┌───────────────────────────┐
│      PostgreSQL         │     │  VIERNULVIER/Peppered API │
│      (database)         │     │  (external data source)   │
└─────────────────────────┘     └───────────────────────────┘
```

Full architecture documentation is available on the [Architecture wiki page](https://github.com/SELab-2/viernulvier-2/wiki/Architecture).

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Django, Django REST Framework, pytest |
| Frontend | TypeScript, React 19, Vite, Material UI, i18next |
| Database | PostgreSQL |
| Reverse proxy | nginx |
| TLS | Let's Encrypt / certbot |
| Lint / format | ruff (Python), ESLint + Prettier (TypeScript) |
| CI/CD | GitHub Actions + self-hosted runner |
| Containers | Docker & Docker Compose |

---

## Getting started

### Requirements

| Tool | Version |
|---|---|
| Python | 3.10+ |
| Node.js / npm | v24+ |
| Docker & Docker Compose | recent version |
| Git | recent version |

> **Tip:** Docker is optional for native development, but required for staging and production.

---

### Backend (native)

```bash
# 1. Copy the environment file
cp infrastructure/.env.example infrastructure/.env

# 2. Start the database (PostgreSQL via Docker)
docker compose -f infrastructure/docker-compose.dev.yml up -d

# 3. Create a virtual environment and activate it
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 4. Install dependencies
pip install -r backend/requirements/development.txt

# 5. Run migrations
cd backend
python manage.py makemigrations
python manage.py migrate

# 6. (Optional) Create a superuser for /admin/
python manage.py createsuperuser

# 7. Start the dev server -> http://localhost:8000
python manage.py runserver
```

Stop the database when you're done:

```bash
docker compose -f infrastructure/docker-compose.dev.yml down
```

---

### Frontend (native)

```bash
cd frontend

# Install dependencies
npm ci

# Start the dev server -> http://localhost:5173
npm run dev

# Build for production
npm run build
```

---

### Full stack with Docker Compose

Start backend, frontend and database simultaneously:

```bash
docker compose -f infrastructure/docker-compose.staging.yml up --build
```

The full stack is then accessible at:

| Service | URL |
|---|---|
| Frontend | http://localhost/ |
| API | http://localhost/api/ |
| Admin | http://localhost/admin/ |
| API Docs | http://localhost/api/docs/ |

---

## Environments

| Environment | Compose file | What runs | Purpose |
|---|---|---|---|
| **Dev** | `docker-compose.dev.yml` | PostgreSQL only | Fast iteration - Django + Vite run natively |
| **Staging** | `docker-compose.staging.yml` | PostgreSQL, backend, frontend, nginx | Full local stack at `http://localhost` |
| **Production** | `docker-compose.prod.yml` | PostgreSQL, backend, frontend, nginx, certbot | Self-hosted deployment on a public server |

---

## Running tests

### Backend

```bash
cd backend

# Full test suite
pytest

# Single app
pytest tests/events

# With coverage
coverage run -m pytest
coverage report -m
```

Full CI check (required before a PR):

```bash
ruff check .                                       # lint
ruff format --check .                              # formatting
python manage.py check                             # Django system check
python manage.py makemigrations --check --dry-run  # no pending migrations
pytest                                             # test suite
```

### Frontend

```bash
cd frontend
npm ci
npm test
```

See the [Testing wiki page](https://github.com/SELab-2/viernulvier-2/wiki/Testing,-Linting-and-Formatting) for a full overview of the test structure and guidelines.

---

## Linting & formatting

### Backend (Python - ruff)

```bash
cd backend

ruff check .           # lint
ruff format --check .  # check formatting
ruff format .          # automatically fix formatting
```

### Frontend (TypeScript - ESLint + Prettier)

```bash
cd frontend

npm run lint           # lint
npm run lint:fix       # automatically fix
npm run format:check   # check formatting
npm run format:fix     # automatically fix formatting
```

> **CI behaviour:** On a push to `main`, lint errors are automatically fixed and committed back. On a pull request, CI fails if there are errors - resolve them locally before pushing.

---

## Data synchronisation

The `sync_viernulvier` management command fetches data from the Viernulvier/Peppered API:

```bash
# Synchronise everything
python manage.py sync_viernulvier

# Only one model type
python manage.py sync_viernulvier --only events

# Incremental - only records updated after a given date
python manage.py sync_viernulvier --updated-after 2024-06-01T00:00:00Z
```

Import historical pre-API data from bundled CSV files:

```bash
python manage.py import_legacy_csv
python manage.py import_legacy_csv --dry-run   # preview without writing
```

**Available sync steps** (in dependency order):

`uitdatabank_types` -> `genres` -> `tags` -> `locations` -> `spaces` -> `halls` -> `media_galleries` -> `media_items` -> `prices` -> `price_ranks` -> `productions` -> `events` -> `event_prices`

Full documentation: [Scraper wiki page](https://github.com/SELab-2/viernulvier-2/wiki/Scraper).

---

## Deployment

Production runs on a self-hosted GitHub Actions runner with Docker. A push to `main` triggers the deploy workflow automatically.

### One-time setup on a new server

```bash
# 1. Install Docker (https://docs.docker.com/engine/install/)
# 2. Register a GitHub Actions self-hosted runner (Settings -> Actions -> Runners)
# 3. Add all variables from infrastructure/.env.example as GitHub repository secrets
# 4. Push to main (or trigger the workflow manually) for the first deployment
# 5. Request the TLS certificate
bash infrastructure/certbot/setup-certbot.sh your-domain.example admin@example.com
```

### Verification

```bash
docker compose -f infrastructure/docker-compose.prod.yml ps
curl https://your-domain.example/health   # expected: ok
```

Full instructions: [Setup and Deployment wiki](https://github.com/SELab-2/viernulvier-2/wiki/Setup-and-Deployment).


---

## Wiki

| Page | Description |
|---|---|
| [Architecture](https://github.com/SELab-2/viernulvier-2/wiki/Architecture) | System and deployment architecture |
| [API Overview](https://github.com/SELab-2/viernulvier-2/wiki/API-Overview) | Authentication, permissions, throttling, endpoints |
| [Backend Folder Structure](https://github.com/SELab-2/viernulvier-2/wiki/Backend-Folder-Structure) | Django app structure and naming conventions |
| [Backend Requirements Structure](https://github.com/SELab-2/viernulvier-2/wiki/Backend-Requirements-Structure) | Dependency management per environment |
| [Frontend](https://github.com/SELab-2/viernulvier-2/wiki/Frontend) | React app overview, routing, theming, scripts |
| [Frontend Components](https://github.com/SELab-2/viernulvier-2/wiki/Frontend-Components) | Component library and reusable patterns |
| [Frontend folder structure](https://github.com/SELab-2/viernulvier-2/wiki/Frontend-folder-structure) | Frontend directory structure |
| [Scraper](https://github.com/SELab-2/viernulvier-2/wiki/Scraper) | Sync command, filters, scraper architecture |
| [Setup and Deployment](https://github.com/SELab-2/viernulvier-2/wiki/Setup-and-Deployment) | Installation and deployment guide |
| [Testing, Linting and Formatting](https://github.com/SELab-2/viernulvier-2/wiki/Testing,-Linting-and-Formatting) | Test strategy, linting and CI behaviour |
| [EER diagram](https://github.com/SELab-2/viernulvier-2/wiki/Eer%E2%80%90diagram) | Entity-relationship diagram of the domain model |

---

<div align="center">

Made by students of [Ghent University](https://www.ugent.be/) as part of the Software Engineering Lab 2 course · [SELab-2](https://github.com/SELab-2)

Distributed under the terms of the LICENSE file in the root of this project.

</div>