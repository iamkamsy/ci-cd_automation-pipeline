# Azure DevOps CI/CD Automation Project - Technical Documentation

## Overview

This repository is being shaped into a cost-conscious Azure DevOps portfolio project for a full-stack task manager application.

The application currently contains:

| Layer | Current Technology | Purpose |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS | Browser UI for authentication and task management |
| Backend | Python, Flask, Flask-CORS, Gunicorn | API service for auth, sessions, and task routes |
| Database | MongoDB Atlas | Persistent user and task data |
| Source Control | Git + GitHub | Repository hosting and CI/CD trigger source |

The DevOps goal is to deploy the app on Azure with Terraform and GitHub Actions while avoiding paid Azure resources wherever possible.

## Target Architecture

```text
Developer
   |
   v
GitHub Repository
   |
   +--> GitHub Actions: Terraform validation and apply
   |
   +--> GitHub Actions: Backend tests, Docker CI validation, App Service deploy
   |
   +--> GitHub Actions: Frontend build and Static Web Apps deploy

React Frontend
   |
   v
Azure Static Web Apps Free
   |
   v
Flask API
   |
   v
Azure App Service Free F1
   |
   v
MongoDB Atlas M0 Free
```

## Cost Policy

This project is intentionally designed around free-tier-safe services.

Allowed Azure resources:

| Resource | Cost Position | Reason |
|---|---|---|
| Azure Resource Group | Free | Logical container for project resources |
| Azure App Service Plan F1 | Free tier | Hosts the Flask API without paid compute |
| Azure Linux Web App | Free-tier plan backed | Runs the Flask backend through App Service |
| Azure Static Web Apps Free | Free tier | Hosts the React frontend |
| Azure Budget Alert | Cost-control guardrail | Helps detect unexpected spending |

Resources intentionally avoided:

| Avoided Resource | Reason |
|---|---|
| AKS | Paid and operationally heavy for this personal project |
| Azure Container Registry | Paid storage/registry dependency; Docker is CI-only here |
| Azure Container Instances | Paid runtime |
| Azure Container Apps | Can incur charges and is unnecessary for this scope |
| Azure VMs | Paid compute and extra maintenance |
| Azure SQL / Cosmos DB | Paid database alternatives not needed because MongoDB Atlas M0 is used |
| Load Balancers / Application Gateway | Paid network resources not needed for a simple portfolio app |
| Deployment slots | Not available on the App Service Free F1 tier |
| Always On | Not supported by Free F1 and must remain disabled |

## Repository Structure

Current important paths:

```text
backend/
  app.py
  db.py
  Dockerfile
  routes/
  models/
  requirements.txt
  tests/

frontend/
  package.json
  src/
  public/

infra/terraform/
  providers.tf
  main.tf
  variables.tf
  outputs.tf
  terraform.tfvars.example
  README.md

.github/workflows/
  terraform-plan.yml
  terraform-apply.yml
  backend-ci-cd.yml
  frontend-ci-cd.yml
  docker-ci.yml

ansible/
  inventory.ini
  playbook.yml

README.md
documentation.md
```

## Implementation Phases

### Step 1: Backend Deployment Foundation

Status: Implemented.

Purpose:

- Add a `/health` endpoint for CI and deployment smoke checks.
- Add pytest coverage for the health endpoint.
- Add `pytest` to backend dependencies.
- Add a backend Dockerfile for CI validation only.
- Add a backend `.env.example` with safe placeholders.

Important design notes:

- Docker is used to prove that the backend can build and run in a clean Linux environment.
- Docker images will not be pushed to Azure Container Registry.
- The Azure backend deployment remains source-based App Service deployment, not container deployment.

### Step 2: Terraform Infrastructure

Status: Implemented.

Purpose:

- Provision the Azure Resource Group.
- Provision an App Service Plan locked to Free F1.
- Provision a Linux Web App for the Flask backend.
- Add app settings for `MONGO_URI`, `FLASK_ENV`, and build behavior.
- Provision Azure Static Web Apps Free if supported cleanly by Terraform.
- Add tags for cost tracking.
- Add outputs for deployed URLs and resource names.
- Add an optional resource-group budget alert guarded by `enable_budget_alert`.

Terraform safety requirements:

- App Service SKU must validate to `F1`.
- Static Web App SKU must validate to `Free`.
- `always_on` must be `false`.
- No paid SKUs should be present.
- No remote state backend by default.
- Budget alerts must use a stable `budget_start_date`, not a dynamic timestamp.

Remote state note:

This personal project uses local Terraform state by default to avoid provisioning an Azure Storage Account just for state. A production project should use remote state with locking, access controls, and secure state storage.

Current Terraform files live in `infra/terraform/`. The local variables file is intentionally excluded from Git:

```text
infra/terraform/terraform.tfvars
infra/terraform/*.tfstate
```

Use `infra/terraform/terraform.tfvars.example` as the template for local values.

### Step 3: GitHub Actions

Status: Implemented.

Current workflows:

| Workflow | Trigger | Purpose |
|---|---|---|
| `terraform-plan.yml` | Pull requests touching `infra/terraform/**` | Format, init, validate, and plan Terraform |
| `terraform-apply.yml` | Pushes to `main` touching `infra/terraform/**` | Apply infrastructure changes |
| `backend-ci-cd.yml` | PRs and pushes touching `backend/**` | Install dependencies, run pytest, deploy backend on `main` |
| `docker-ci.yml` | PRs and pushes touching backend Docker files | Build backend image, run container, curl `/health`, stop container |
| `frontend-ci-cd.yml` | PRs and pushes touching `frontend/**` | Install, build, and deploy frontend on `main` |

Deployment gates:

- Pull requests run validation only.
- Backend deploy runs only on `push` to `main` when `AZURE_WEBAPP_NAME` and `AZURE_WEBAPP_PUBLISH_PROFILE` are configured.
- Frontend deploy runs only on `push` to `main` when `AZURE_STATIC_WEB_APPS_API_TOKEN` is configured.
- Docker CI never pushes images and never deploys to Azure.

Required GitHub secrets:

```text
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
MONGO_URI
FLASK_SECRET_KEY
AZURE_WEBAPP_PUBLISH_PROFILE
AZURE_STATIC_WEB_APPS_API_TOKEN
```

Required GitHub repository variables:

```text
AZURE_WEBAPP_NAME
```

`AZURE_WEBAPP_NAME` must match the Terraform `app_service_name` value.

### Step 4: Ansible Local Setup

Status: Implemented.

Purpose:

- Automate local development setup only.
- Create example environment files when missing.
- Optionally install local backend dependencies.
- Print setup instructions for the developer.

Ansible will not create Azure VMs, configure remote servers, or deploy cloud infrastructure.

Current Ansible files:

```text
ansible/inventory.ini
ansible/playbook.yml
```

The inventory targets only `localhost` with a local connection. The playbook creates missing `.env.example` files without overwriting existing files, can optionally install backend dependencies into the active Python environment, and prints local setup instructions.

Typical usage:

```text
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml -e install_backend_deps=true
```

### Step 5: README and Interview Narrative

Purpose:

- Explain the architecture clearly.
- Show how Terraform, GitHub Actions, Azure, Docker, Ansible, and MongoDB Atlas fit together.
- Document free-tier design decisions.
- Provide setup and secret instructions.
- Include resume-ready bullet examples.

## DevOps Workflow

Recommended branch flow:

```text
feature/* or for-review/*
   |
   v
Pull Request
   |
   +--> Terraform plan if infrastructure changed
   +--> Backend tests if backend changed
   +--> Docker validation if backend Docker context changed
   +--> Frontend build if frontend changed
   |
   v
main
   |
   +--> Terraform apply for infrastructure changes
   +--> Backend deploy to Azure App Service
   +--> Frontend deploy to Azure Static Web Apps
```

The working review process for this repo is:

1. Generate one small implementation step on a `for-review/...` branch.
2. Stage the changes without committing.
3. Review the staged diff.
4. Fix issues before moving to the next step.

## Azure Authentication Model

Terraform workflows will use a GitHub Actions service principal with these secrets:

```text
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
```

The service principal should have the minimum permissions needed for the resource group scope. For a personal learning project, Contributor on the dedicated resource group is usually simpler to operate than subscription-wide permissions.

Backend source deployment will use:

```text
AZURE_WEBAPP_PUBLISH_PROFILE
AZURE_WEBAPP_NAME
```

Frontend Static Web Apps deployment will use:

```text
AZURE_STATIC_WEB_APPS_API_TOKEN
```

Application secrets such as `MONGO_URI` and `FLASK_SECRET_KEY` must remain in GitHub Secrets and Azure App Service app settings. They should never be committed.

## Backend Runtime Notes

The Flask backend is expected to run behind Gunicorn on Azure App Service.

Expected production command:

```text
gunicorn app:app
```

Important environment variables:

```text
MONGO_URI
SECRET_KEY
DB_NAME
FLASK_ENV
CORS_ORIGINS
SESSION_COOKIE_SECURE
```

The `/health` endpoint is intended for lightweight CI and smoke-test checks. It should not require a database round trip.

The backend Dockerfile is for CI validation only. Azure deployment remains source-based App Service deployment, not container deployment.

## Frontend Runtime Notes

The frontend is a Vite React application. Static Web Apps will build it from `frontend/` and publish the generated static assets.

Typical local commands:

```text
cd frontend
npm install
npm run build
```

The frontend should use environment variables for backend API URLs rather than hardcoded production endpoints.

## Production Differences

For a real production system, this design would likely change:

| Area | Personal Project Choice | Production Upgrade |
|---|---|---|
| Terraform state | Local state | Remote state with locking |
| App Service plan | Free F1 | Basic, Standard, or Premium tier |
| Deployment slots | Avoided | Staging slot with swap |
| Monitoring | Minimal | Application Insights and alerts |
| Secrets | GitHub Secrets and app settings | Key Vault with managed identity |
| Auth to Azure | Service principal secret | GitHub OIDC federation |
| Database | MongoDB Atlas M0 | Paid cluster with backups and monitoring |
| Containers | CI validation only | Registry and container hosting only if justified |

## Resume Narrative

Strong project bullets:

- Provisioned Azure infrastructure using Terraform, including a Resource Group, App Service Plan F1, Linux Web App, app settings, tags, outputs, and free-tier guardrails.
- Automated infrastructure validation and deployment using GitHub Actions with Terraform plan on pull requests and Terraform apply on main branch merges.
- Built CI/CD workflows for a React and Flask full-stack application using GitHub Actions, Azure Static Web Apps, Azure App Service, Docker validation, and MongoDB Atlas.
- Enforced cost-conscious cloud usage through Terraform variable validation, SKU restrictions, disabled Always On, and explicit avoidance of paid Azure services.
- Used Docker for backend CI validation without introducing paid container registry or Azure container runtime dependencies.
