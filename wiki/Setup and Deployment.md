# Setup and Deployment

This page documents how the project is run in each environment and how to self-host the production stack.

Unless stated otherwise, commands should be run from the repository root. Commands that need to be run from `backend/` or `frontend/` explicitly say so.

## Environment Overview

| Environment | Compose file                                | What runs                                                     | Main use                                                                |
| ----------- | ------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Dev         | `infrastructure/docker-compose.dev.yml`     | PostgreSQL only                                               | Local development with Django and Vite running directly on your machine |
| Staging     | `infrastructure/docker-compose.staging.yml` | PostgreSQL, backend, frontend build container, nginx          | Full local stack on `http://localhost` without HTTPS/certbot            |
| Production  | `infrastructure/docker-compose.prod.yml`    | PostgreSQL, backend, frontend build container, nginx, certbot | Self-hosted deployment on a public server                               |

## Local Development

Use the dev setup when you want fast iteration and hot reload.

### 1. Backend environment file

Create `backend/.env` by copying `backend/.env.example`.

This file is used by Django when you run the backend directly on your machine.

### 2. Start only the database with Docker

Create `infrastructure/.env.dev` by copying `infrastructure/.env.dev.example`.

Start PostgreSQL:

```bash
docker compose -f infrastructure/docker-compose.dev.yml up -d
```

This exposes PostgreSQL on `localhost:5432`.

### 3. Run the backend locally

From `backend/`:

```bash
pip install -r requirements/development.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

### 4. Run the frontend locally

From `frontend/`:

```bash
npm ci
npm run dev
```

By default, Vite runs on `http://localhost:5173`.

### 5. Stop the dev database

When you are done, stop the database again so it does not keep running and cause conflicts later.

```bash
docker compose -f infrastructure/docker-compose.dev.yml down
```

## Local Staging

Use the staging stack when you want to run the full application locally behind nginx, close to production, but without HTTPS and certbot.

### 1. Create the staging env file

Create `infrastructure/.env.staging` by copying `infrastructure/.env.staging.example`.

### 2. Start the full stack

```bash
docker compose -f infrastructure/docker-compose.staging.yml up --build
```

What this starts:

- `database`: PostgreSQL
- `backend`: Django with `config.settings.staging`
- `frontend`: builds the React app into a shared volume
- `nginx`: serves the frontend and reverse proxies `/api/` and `/admin/`

### 3. Open the application

- Frontend: `http://localhost/`
- API: `http://localhost/api/`
- Admin: `http://localhost/admin/`
- Health: `http://localhost/health`

### 4. Stop the stack

When you are done, stop the staging stack again so it does not keep running and cause conflicts later.

```bash
docker compose -f infrastructure/docker-compose.staging.yml down
```

If you also want to remove volumes:

Warning: `down -v` permanently deletes the PostgreSQL volume and all database data in it.

```bash
docker compose -f infrastructure/docker-compose.staging.yml down -v
```

## Production Self-Hosting

The production deployment is intended for a Linux server that runs a self-hosted GitHub Actions runner and Docker.

### What the production stack contains

`infrastructure/docker-compose.prod.yml` starts:

- `database`: PostgreSQL with persistent storage
- `backend`: Django with `config.settings.prod`
- `frontend`: builds the static frontend bundle
- `nginx`: serves the frontend, `/api/`, `/admin/`, `/static/`, and `/media/`
- `certbot`: renews Let's Encrypt certificates automatically

### Prerequisites

Before the first deployment, make sure you have:

- A Linux server
- A public domain name pointing to the server
- Ports `80` and `443` open to the internet
- A GitHub repository admin who can add Actions runners and repository secrets

### Recommended setup order

The safest order is:

1. Install Docker on the server.
2. Install and register the GitHub Actions self-hosted runner.
3. Add the production variables as GitHub Secrets.
4. Trigger the deployment workflow once so `infrastructure/.env.prod` is generated on the server.
5. Run `infrastructure/certbot/setup-certbot.sh` once to request the real certificate.

### 1. Install Docker

Install Docker and the Docker Compose plugin on the server.

Follow the official Docker instructions for your Linux distribution:

- [Install Docker Engine](https://docs.docker.com/engine/install/)
- [Install Docker Compose plugin](https://docs.docker.com/compose/install/linux/)

Verify the installation:

```bash
docker --version
docker compose version
```

### 2. Install the GitHub Actions runner

Install it from the repository settings in GitHub:

1. Open `Settings -> Actions -> Runners`.
2. Click `New self-hosted runner`.
3. Select the correct OS and architecture for your server.
4. Run the commands GitHub shows on the server.
5. Install the runner as a service so it survives reboots.

Official reference:

- [Adding a self-hosted runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)

### 3. Add GitHub Secrets

The deploy workflow creates `infrastructure/.env.prod` from `infrastructure/.env.prod.example`, so every variable in that example file should be added as a GitHub repository secret.

To add them:

1. Open the repository on GitHub.
2. Go to `Settings -> Secrets and variables -> Actions`.
3. Click `New repository secret`.
4. Open `infrastructure/.env.prod.example`.
5. For each variable name in that file, create a secret in GitHub with the same name and the correct production value.

### 4. First deployment

The production workflow is defined in `.github/workflows/deploy.yml`.

It:

1. Checks out the repository on the self-hosted runner.
2. Creates `infrastructure/.env.prod` from GitHub Secrets using `envsubst`.
3. Builds the production containers.
4. Starts the stack with Docker Compose.
5. Runs a simple post-deploy container status check.

To trigger it:

- push to `main`, or
- run the workflow manually from the GitHub Actions UI

### 5. Run the certbot bootstrap script

After the first deployment, SSH into the server and run:

```bash
cd ~/actions-runner/_work/<repo-name>/<repo-name>/
bash infrastructure/certbot/setup-certbot.sh <domain> <email>
```

Example:

```bash
bash infrastructure/certbot/setup-certbot.sh your-domain.example admin@example.com
```

### 6. Verify the deployment

Useful checks on the server:

```bash
docker compose -f infrastructure/docker-compose.prod.yml ps
```

Then verify:

- `http://<domain>/health` returns `ok`
- `https://<domain>/` serves the frontend
- `https://<domain>/api/docs/` serves the OpenAPI docs
