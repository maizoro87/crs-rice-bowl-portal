# CRS Site

CRS Site is a new project initialized on 2026-01-27.

## Overview

This repository will contain the source code and assets for the CRS Site application.

## Getting Started

More detailed setup and project rules will be added after project initialization.

## Docker & Deployment

This project includes a basic containerization and deployment setup:

- `Dockerfile`: Builds an nginx-based image that serves static content from the `public/` directory.
- `.dockerignore`: Excludes git metadata, environment files, OS/editor cruft, and common build artifacts from the Docker build context.
- `docker-compose.yml`: Runs the CRS Site container locally on port `8080`.
- `.github/workflows/docker-build.yml`: GitHub Actions workflow to build (and optionally push) the Docker image.

### Local Docker usage

Build the image (from the project root):

```bash
docker build -t crs-site:local .
```

Run the container directly:

```bash
docker run --rm -p 8080:80 crs-site:local
```

Or use docker-compose:

```bash
docker compose up --build
```

Then open http://localhost:8080 in your browser.

### CI/CD and registry configuration

The GitHub Actions workflow expects (optionally) the following secrets if you want to push images to a registry:

- `DOCKER_REGISTRY_USERNAME`
- `DOCKER_REGISTRY_PASSWORD`

Set `DOCKER_REGISTRY` in `.github/workflows/docker-build.yml` to your registry host/namespace, for example:

- `docker.io/your-dockerhub-username`
- `ghcr.io/your-org-or-user`

If `DOCKER_REGISTRY` is left empty, CI will still build the image but will not push it, and will tag it locally as `crs-site:ci`.
