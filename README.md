# Task Manager -- Azure DevOps CI/CD Portfolio Project

A full-stack task manager application used as a cost-conscious Azure DevOps CI/CD
portfolio project. The application itself is a working personal task manager with
per-user account isolation. The surrounding infrastructure, pipelines, and tooling
demonstrate end-to-end DevOps practices on Azure within free and low-cost tier limits.

This is a personal learning and portfolio project. It is not optimized for production
scale or high availability.

---

## Tech Stack

| Layer          | Technology                                      |
|----------------|-------------------------------------------------|
| Frontend       | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend        | Python 3.11, Flask, Flask-CORS                  |
| Database       | MongoDB Atlas M0 (free tier)                    |
| Infrastructure | Terraform, Azure Resource Manager              |
| CI/CD          | GitHub Actions                                  |
| Container CI   | Docker (build and health-check only, not deployed) |
| Local setup    | Ansible (localhost only)                        |
| Auth           | Signed cookie sessions, bcrypt password hashing |

---

## Architecture

```
React Frontend (TypeScript + Vite)
        |
        v
Azure Static Web Apps -- Free tier
        |
        v
Flask REST API (Python 3.11)
        |
        v
Azure App Service -- Linux, F1 free tier
        |
        v
MongoDB Atlas M0 -- free shared cluster
```

---

## Repository Structure

```
.
|-- frontend/                  React + TypeScript + Vite application
|-- backend/                   Flask API, pytest tests, Dockerfile (CI only)
|-- infra/
|   `-- terraform/             AzureRM Terraform configuration
|       |-- providers.tf
|       |-- main.tf
|       |-- variables.tf
|       |-- outputs.tf
|       |-- terraform.tfvars.example
|       `-- README.md
|-- ansible/
|   |-- inventory.ini          localhost only
|   `-- playbook.yml           local developer setup tasks
|-- .github/
|   `-- workflows/
|       |-- terraform-plan.yml
|       |-- terraform-apply.yml
|       |-- backend-ci-cd.yml
|       |-- docker-ci.yml
|       `-- frontend-ci-cd.yml
|-- documentation.md
|-- changelog.md
`-- README.md
```

---

## DevOps Workflow

### Pull Requests

- Opening a PR that touches `infra/terraform/**` triggers `terraform-plan.yml`:
  fmt check, init, validate, and plan. The plan output is visible in the PR checks.
- Opening a PR that touches `backend/**` triggers `backend-ci-cd.yml` (tests only,
  no deploy) and `docker-ci.yml` (Docker build and /health smoke test).
- Opening a PR that touches `frontend/**` triggers `frontend-ci-cd.yml` (build only,
  no deploy).

### Merges to main

- Merging a change to `infra/terraform/**` triggers `terraform-apply.yml`:
  init and apply with auto-approve.
- Merging a change to `backend/**` triggers `backend-ci-cd.yml`: tests, then deploy
  to Azure App Service if `AZURE_WEBAPP_NAME` and `AZURE_WEBAPP_PUBLISH_PROFILE` are
  configured.
- Merging a change to `frontend/**` triggers `frontend-ci-cd.yml`: build, then deploy
  to Azure Static Web Apps if `AZURE_STATIC_WEB_APPS_API_TOKEN` is configured.
- Merging a change to `backend/**` also triggers `docker-ci.yml` for Docker validation.

### Docker CI

The `docker-ci.yml` workflow builds the backend Docker image, runs the container with
test-safe environment variables (`TESTING=true`), and curls `/health`. The image is
not pushed to any registry and is not used for Azure deployment. Azure App Service
receives a source package deploy, not a container deploy.

### Ansible

`ansible/playbook.yml` targets localhost only. It ensures `.env.example` files exist
for both backend and frontend, optionally installs backend Python dependencies into
the active environment, and prints setup instructions. It does not provision any
Azure resources.

---

## Cost-Conscious Design

| Decision | Reason |
|---|---|
| Azure App Service F1 | Free tier; 60 CPU-min/day, 1 GB RAM, no charge |
| Azure Static Web Apps Free | Free tier; 100 GB bandwidth, 2 custom domains |
| MongoDB Atlas M0 | Free shared cluster; sufficient for personal/portfolio workloads |
| `always_on = false` | Required by F1; paid tiers support always-on |
| Docker for CI only | Avoids Azure Container Registry (paid) and AKS/Container Apps costs |
| Local Terraform state | Avoids creating an Azure Storage Account for state backend |
| No deployment slots | Deployment slots require Standard tier or above |
| Terraform variable validation | Prevents accidental SKU upgrades to paid tiers |

Resources deliberately excluded: AKS, ACR, Container Apps, Azure VMs, Azure SQL,
Cosmos DB, load balancers, Application Gateway, deployment slots, paid App Service
plans.

### What would change in production

- Remote Terraform state with locking (Azure Storage backend, see comment in
  `infra/terraform/providers.tf`).
- A paid App Service tier to enable always-on, custom domains with TLS, and
  deployment slots for zero-downtime releases.
- A managed identity or Azure Key Vault for secrets instead of publish profiles.
- MongoDB Atlas dedicated cluster for production workloads.
- Docker image pushed to a registry and deployed as a container if containerization
  becomes a deployment requirement.

---

## Local Prerequisites

- Git
- Python 3.11+
- Node.js 20+
- Terraform (1.6+)
- Azure CLI (`az`)
- MongoDB Atlas account with a free M0 cluster
- Ansible (optional, for local setup automation; works best through WSL on Windows)

---

## Local Setup

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env -- set MONGO_URI and SECRET_KEY
flask run
```

Backend runs on `http://localhost:5000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

### Ansible (optional local setup)

```bash
# Ensure .env.example files exist and print setup instructions
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml

# Also install backend Python dependencies into the active environment
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  -e install_backend_deps=true
```

Ansible targets localhost only. It does not touch Azure.

### Terraform

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars -- replace all REPLACE_* placeholders

terraform init
terraform fmt
terraform validate
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

Never commit `terraform.tfvars`. It is listed in `.gitignore`.

---

## Azure Service Principal

Create a service principal for GitHub Actions to authenticate with Azure:

```bash
az ad sp create-for-rbac \
  --name "github-actions-azure-devops-cicd" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP_NAME> \
  --sdk-auth
```

Notes:
- Use least-privilege role assignments where possible. Contributor on the resource
  group is sufficient once the resource group exists.
- If the resource group does not exist yet, you may need Contributor at the
  subscription scope for the first `terraform apply`, or create the resource group
  manually before scoping the service principal to it.
- The `--sdk-auth` output provides the four values needed for the GitHub secrets
  below.

---

## GitHub Secrets and Variables

Configure these in the repository under Settings > Secrets and variables > Actions.

### Secrets

| Secret | Description |
|---|---|
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal client secret |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `MONGO_URI` | MongoDB Atlas connection string; maps to Terraform `var.mongo_uri` and the App Service `MONGO_URI` app setting |
| `FLASK_SECRET_KEY` | Flask `SECRET_KEY`; maps to Terraform `var.secret_key` and the App Service `SECRET_KEY` app setting |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Publish profile XML from the Azure Web App resource |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Deployment token from the Azure Static Web App resource |

### Repository Variable

| Variable | Description |
|---|---|
| `AZURE_WEBAPP_NAME` | Must match the Terraform `app_service_name` variable value |

### Secret name mapping

- `FLASK_SECRET_KEY` is used by `terraform-plan.yml` and `terraform-apply.yml` as
  `TF_VAR_secret_key`. Terraform passes it to the Azure App Service as the `SECRET_KEY`
  app setting, which Flask reads at runtime. It is not used directly by
  `backend-ci-cd.yml`; that workflow deploys using `AZURE_WEBAPP_PUBLISH_PROFILE` and
  `AZURE_WEBAPP_NAME`.
- `MONGO_URI` follows the same pattern through `TF_VAR_mongo_uri` to the `MONGO_URI`
  app setting.

---

## Deployment Notes

- Terraform provisions the Resource Group, App Service Plan, Linux Web App, and
  Static Web App. It sets app settings including `MONGO_URI`, `SECRET_KEY`, and
  `FLASK_ENV=production`.
- GitHub Actions deploys the backend as a source package to Azure App Service using
  the `azure/webapps-deploy` action and a publish profile. The App Service build
  system installs Python dependencies via `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.
- GitHub Actions deploys the frontend to Azure Static Web Apps using the
  `Azure/static-web-apps-deploy` action.
- The Docker image built in `docker-ci.yml` is used only for CI smoke testing. It is
  not pushed to any registry and is not used by Azure.
- The publish profile is obtained from the Azure portal or CLI after the Web App is
  provisioned by Terraform.
- The Static Web Apps API token is obtained from the Azure portal or the Static Web
  App resource after provisioning.

---

## Verification Commands

Run each block from the repository root unless otherwise noted.

**Backend tests**
```bash
cd backend
python -m pytest
```

**Docker build and health check** (run from repo root)
```bash
docker build -t taskmanager-backend-ci ./backend
docker run -d --name taskmanager-backend-ci -p 5000:5000 \
  -e TESTING=true \
  -e SECRET_KEY=test-secret \
  -e MONGO_URI=mongodb://localhost:27017 \
  taskmanager-backend-ci
sleep 5
curl http://localhost:5000/health
docker stop taskmanager-backend-ci && docker rm taskmanager-backend-ci
```

**Frontend build**
```bash
cd frontend
npm run build
```

**Terraform validate**
```bash
cd infra/terraform
terraform validate
```

**Ansible syntax check** (run from repo root)
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --syntax-check
```

---

## Resume Bullets

- Provisioned Azure infrastructure using Terraform, including Resource Groups, App
  Service Plan F1, Web App, Static Web Apps, app settings, tags, outputs, and
  free-tier guardrails enforced through variable validation.

- Automated infrastructure validation and deployment using GitHub Actions with
  Terraform plan on pull requests and Terraform apply on main branch merges.

- Built CI/CD workflows for a React and Flask full-stack application using GitHub
  Actions, Azure Static Web Apps, Azure App Service, Docker, and MongoDB Atlas.

- Enforced free-tier cloud usage through Terraform variable validation, SKU
  restrictions, disabled Always On, and cost-aware infrastructure design.

- Used Docker for backend CI health validation without introducing paid registry or
  container hosting dependencies.

- Automated local developer setup with Ansible while keeping cloud provisioning in
  Terraform.
