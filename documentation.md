# Azure-Based CI/CD Automation Pipeline — Technical Documentation

## Overview

This project implements a full CI/CD pipeline for a Flask web application with a C++ microservice, deployed to Azure Web App. The pipeline automates the build, test, and deployment lifecycle using GitHub Actions, Docker, and Ansible — covering everything from local development through production.

---

## Full Tech Stack

### Application Layer

| Component | Technology | Purpose |
|---|---|---|
| Web Application | Python (Flask) | Core web service — handles HTTP requests, business logic, API endpoints |
| Validation Microservice | C++ | Pre-deployment validation tests — runs checks before production deploys |
| Package Management | pip + `requirements.txt` | Python dependency management |
| Build Tool (C++) | CMake | Compiles and links the C++ microservice |

### Source Control & Branching

| Component | Technology | Purpose |
|---|---|---|
| Version Control | Git | Tracks all source changes |
| Branching Strategy | Gitflow | Structured branching: `main`, `develop`, `feature/*`, `release/*`, `hotfix/*` |
| Remote Repository | GitHub | Hosts source code, triggers CI/CD via push/PR events |

**Gitflow branch conventions:**
- `main` — production-ready code only; deploys to Azure production slot
- `develop` — integration branch; deploys to staging slot on merge
- `feature/*` — short-lived feature branches; merged into `develop` via PR
- `release/*` — stabilization branch before merging to `main`
- `hotfix/*` — emergency patches branched from `main`, merged back to both `main` and `develop`

### CI/CD Orchestration

| Component | Technology | Purpose |
|---|---|---|
| Pipeline Runner | GitHub Actions | Triggers on push/PR; orchestrates build, test, deploy stages |
| Workflow Files | YAML (`.github/workflows/`) | Defines pipeline jobs and steps |
| Secrets Management | GitHub Secrets | Stores Azure credentials, Docker Hub tokens, environment variables |

**Recommended workflow structure:**
```
.github/workflows/
  ci.yml          # Runs on all PRs: lint, unit tests, C++ build & validation
  cd-staging.yml  # Runs on merge to develop: build image, push, deploy to staging
  cd-prod.yml     # Runs on merge to main: deploy staging image to production
```

### Containerization

| Component | Technology | Purpose |
|---|---|---|
| Container Runtime | Docker | Packages Flask app and dependencies into a portable image |
| Image Registry | Docker Hub (recommended: Azure Container Registry) | Stores and versions container images |
| Compose (local dev) | Docker Compose | Runs Flask + any local services together during development |

**Recommended Dockerfile approach:**
- Multi-stage build: builder stage installs dependencies, final stage copies only what's needed — keeps image lean
- Base image: `python:3.11-slim`
- Non-root user for security

### Infrastructure Provisioning & Configuration

| Component | Technology | Purpose |
|---|---|---|
| Configuration Management | Ansible | Automates environment setup, installs dependencies, configures servers |
| Inventory | Ansible inventory file or dynamic inventory | Targets staging and production environments |
| Playbooks | YAML | Defines provisioning steps (install Docker, configure app settings, etc.) |

**Recommended playbook structure:**
```
ansible/
  inventory/
    staging.ini
    production.ini
  playbooks/
    provision.yml     # Install Docker, set up firewall, create app user
    deploy.yml        # Pull latest image, restart container
    rollback.yml      # Re-deploy previous image tag on failure
  roles/
    docker/
    flask-app/
```

### Cloud Infrastructure

| Component | Technology | Purpose |
|---|---|---|
| Hosting | Azure Web App (Linux) | Runs the containerized Flask application |
| Deployment Slots | Azure Deployment Slots | Staging slot for pre-production validation; swap to production with zero downtime |
| App Configuration | Azure App Service Configuration | Stores environment variables (DB connection strings, API keys) |
| Monitoring | Azure Monitor + Application Insights (recommended) | Tracks uptime, errors, response times |
| Container Source | Azure Container Registry (recommended over Docker Hub) | Private registry co-located with Azure for faster pulls |

### C++ Microservice Integration

| Component | Technology | Purpose |
|---|---|---|
| Build System | CMake | Builds the C++ validation binary |
| Test Runner | Custom binary or Google Test (recommended) | Runs pre-deployment checks (schema validation, integration probes, etc.) |
| Pipeline Integration | GitHub Actions step | Compiles and executes C++ binary; fails the pipeline if validation fails |

The C++ microservice runs as a pipeline step — not as a deployed service. It compiles during CI, executes validation tests against the staging environment or build artifacts, and exits with a non-zero code to block deployment if checks fail.

---

## How It All Connects

```
Developer pushes feature branch
        |
        v
GitHub Actions triggers ci.yml
  - Lint Python (flake8/ruff)
  - Run Python unit tests (pytest)
  - Compile C++ microservice (cmake + make)
  - Run C++ validation tests
        |
  All green? --> PR can be merged to develop
        |
        v
Merge to develop triggers cd-staging.yml
  - Build Docker image
  - Tag image with commit SHA
  - Push to Azure Container Registry
  - Ansible runs deploy.yml against staging slot
  - Azure Web App staging slot pulls new image
  - Smoke tests run against staging URL
        |
  Staging verified? --> Open PR to main
        |
        v
Merge to main triggers cd-prod.yml
  - C++ validation runs one final time against staging
  - Azure slot swap: staging --> production (zero downtime)
  - Ansible updates production config if needed
  - Azure Monitor confirms healthy response
        |
        v
Production is live
```

---

## Likely Challenges and How to Overcome Them

### 1. Azure Credentials and Secrets Rotation

**Challenge:** GitHub Actions needs Azure service principal credentials. These expire and rotation is easy to forget, causing production deploys to fail silently.

**Solution:**
- Use a dedicated service principal with the minimum required RBAC roles (`Website Contributor`, `AcrPush`)
- Store credentials in GitHub Secrets (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
- Set a calendar reminder for credential rotation (every 90 days)
- Recommended: Use Azure Workload Identity Federation with OIDC — eliminates long-lived secrets entirely by letting GitHub Actions authenticate to Azure without a stored password

---

### 2. C++ Build Environment Consistency

**Challenge:** The C++ microservice compiles fine locally but fails in the GitHub Actions runner due to missing system libraries or compiler version mismatches.

**Solution:**
- Pin the GitHub Actions runner OS (`ubuntu-22.04`, not `ubuntu-latest`) to prevent unexpected upgrades
- Use a Docker container in CI for the C++ build step to guarantee a consistent environment
- Cache CMake build output using `actions/cache` to speed up subsequent runs

---

### 3. Docker Image Bloat

**Challenge:** Naive Docker builds include dev tools, test dependencies, and cache files — images balloon to hundreds of MB and slow deployment.

**Solution:**
- Use multi-stage Dockerfiles: compile/install in one stage, copy only runtime artifacts to a slim final stage
- Use `.dockerignore` to exclude `__pycache__`, `.git`, test files, and docs
- Regularly audit image size with `docker image ls` and `docker history`

---

### 4. Ansible Idempotency Issues

**Challenge:** Ansible playbooks that are not properly idempotent can corrupt state when re-run — for example, appending the same config line twice, or restarting services unnecessarily.

**Solution:**
- Always use Ansible modules (`copy`, `lineinfile` with `state: present`, `service`) rather than raw shell commands
- Test playbooks with `--check` (dry run) and `--diff` flags before applying to production
- Validate idempotency by running the same playbook twice and confirming no changes on the second run

---

### 5. Zero-Downtime Slot Swaps

**Challenge:** Azure deployment slot swaps occasionally expose users to mixed responses if the swap is not warmed up properly.

**Solution:**
- Configure slot warm-up rules in Azure (`applicationInitialization` in `web.config` or app settings)
- Use Azure's built-in auto-swap only after health checks pass on the staging slot
- Monitor swap events in Azure Activity Log; set an alert for failed swaps

---

### 6. Flaky Tests Blocking Deploys

**Challenge:** Non-deterministic tests (time-dependent, network-dependent) occasionally fail in CI and block valid deployments.

**Solution:**
- Mark known flaky tests and quarantine them in a separate suite that does not gate the pipeline
- Use `pytest-retry` for tests that are inherently subject to transient failures
- Track flake rate over time — if a test fails more than 5% of the time, fix or remove it

---

### 7. Pipeline Secret Sprawl

**Challenge:** As the project grows, secrets accumulate across GitHub, Azure, and Docker — making auditing and rotation difficult.

**Solution:**
- Use Azure Key Vault as the single source of truth for all secrets
- Reference Key Vault from both Ansible and Azure App Service configuration
- Audit secret access logs quarterly

---

## What Could Be Improved in Future Versions

### Short-Term Improvements

**1. Switch to Azure Container Registry (ACR) from Docker Hub**
ACR is co-located with Azure, so image pulls during deployment are faster and private. It also integrates natively with Azure Web App's managed identity, eliminating Docker Hub credentials entirely.

**2. Add Infrastructure-as-Code with Bicep or Terraform**
Currently, Ansible handles configuration but the Azure resources themselves (Web App, slots, ACR) are presumably created manually. Replacing this with Bicep (Azure-native) or Terraform makes the entire infrastructure reproducible and version-controlled.

**3. Replace Ansible with Azure Web App's native deployment config**
For simple container deployments, Azure Web App can pull directly from ACR on a configured cadence. Ansible adds value for multi-server setups or complex config, but for a single Web App it may be unnecessary overhead.

**4. Add SAST and dependency scanning to CI**
Integrate `bandit` (Python security linter), `safety` (checks for known vulnerable packages), and GitHub's Dependabot to catch security issues before they reach production.

---

### Medium-Term Improvements

**5. Observability stack**
Add Azure Application Insights to the Flask app (via `opencensus-ext-azure` or `opentelemetry-sdk`) to get distributed tracing, custom metrics, and structured logging. Currently the 95% deployment success rate is tracked manually — Application Insights can surface this automatically.

**6. Automated rollback**
If post-deployment health checks fail, the pipeline should automatically swap the production slot back. This can be implemented as a GitHub Actions step that calls `az webapp deployment slot swap` in reverse if a smoke test step returns non-zero.

**7. Environment promotion gating**
Add a manual approval step in the GitHub Actions workflow before the production deploy (using GitHub Environments with required reviewers). This creates a human gate between staging and production without slowing down the staging deploy.

**8. C++ microservice as a sidecar or separate service**
If the validation logic grows more complex, consider deploying the C++ component as a long-running sidecar container rather than a one-shot CI step. This would allow it to run continuous integrity checks against the live application.

---

### Long-Term Improvements

**9. Migrate to Azure Kubernetes Service (AKS)**
Azure Web App is simple to operate but limits horizontal scaling and multi-service orchestration. AKS would allow the Flask app and C++ microservice to run as separate pods with independent scaling, health checks, and rolling update strategies.

**10. Feature flagging**
Integrate a feature flag system (LaunchDarkly, Azure App Configuration feature flags) to decouple deployment from release. This allows code to be deployed to production without being active for users — enabling dark launches and gradual rollouts without pipeline changes.

**11. GitOps model**
Replace push-based deployments (GitHub Actions telling Azure to deploy) with a pull-based GitOps approach using ArgoCD or Flux. The cluster watches the repository for manifest changes and reconciles itself — improving auditability and making rollbacks trivial.

**12. Dedicated secrets management in pipeline**
Replace GitHub Secrets with HashiCorp Vault or Azure Key Vault references natively in GitHub Actions using the `azure/get-keyvault-secrets` action. This centralizes rotation and audit trails.

---

## Project Metrics Summary

| Metric | Value |
|---|---|
| Workflow automation coverage | ~90% of build, test, and deploy steps |
| Deployment success rate | 95% |
| Average deployment runtime | ~3 minutes |
| Verification efficiency improvement (C++ microservice) | +20% |
| Environment setup time reduction (Ansible) | Significant reduction vs. manual setup |
