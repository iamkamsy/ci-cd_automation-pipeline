# Terraform — Azure Free-Tier Infrastructure

## What this creates

| Resource | Type | SKU |
|---|---|---|
| Resource Group | `azurerm_resource_group` | — |
| App Service Plan | `azurerm_service_plan` (Linux) | **F1** |
| Linux Web App (Flask backend) | `azurerm_linux_web_app` | — |
| Static Web App (React frontend) | `azurerm_static_web_app` | **Free** |
| Consumption Budget *(optional)* | `azurerm_consumption_budget_resource_group` | — |

---

## Cost-policy decisions

### Why F1 and Free SKUs are enforced

Variable validation blocks any value other than `F1` (App Service Plan) or
`Free` (Static Web App). This prevents accidental drift to paid tiers during
`plan` or `apply`. The F1 plan provides 60 CPU-minutes/day and 1 GB RAM at no
cost; the Free Static Web App tier provides 100 GB bandwidth and 2 custom
domains at no cost.

### Why `always_on = false`

`always_on = true` is not supported on the F1 SKU. Enabling it would cause the
`apply` to fail. The Flask app will cold-start on the first request after idle
periods, which is acceptable for a dev/demo workload.

### Why there is no remote state by default

Local state keeps the setup self-contained and dependency-free for individual
contributors. **Production deployments must use remote state** (e.g. an Azure
Storage backend) to prevent state conflicts during concurrent applies and to
store state securely. See the commented-out `backend "azurerm"` block in
`providers.tf` for the recommended configuration.

---

## Required variables

The following variables have **no default** and must be supplied in
`terraform.tfvars` (or via `-var`):

| Variable | Description |
|---|---|
| `mongo_uri` | MongoDB connection string (sensitive) |
| `secret_key` | Flask `SECRET_KEY` (sensitive) |

All other variables have safe defaults. See `variables.tf` for the full list
and `terraform.tfvars.example` for example values.

---

## Usage

```bash
cd infra/terraform

# 1. Copy and fill in the example vars file (never commit terraform.tfvars).
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — replace every REPLACE_* placeholder.

# 2. Initialise providers and backend.
terraform init

# 3. Format and validate.
terraform fmt
terraform validate

# 4. Preview changes.
terraform plan -var-file="terraform.tfvars"

# 5. Apply.
terraform apply -var-file="terraform.tfvars"
```

---

## Static Web App — provider note

`azurerm_static_web_app` requires **azurerm provider >= 3.57**. The `sku_tier`
and `sku_size` attributes map directly to the Azure API's `Free` tier. If your
provider version is older, run `terraform init -upgrade` or pin a newer version
in `providers.tf`.

---

## Optional budget alert

Set `enable_budget_alert = true` in `terraform.tfvars` and supply the two
required companion values to create a monthly consumption budget on the resource
group:

| Variable | Required when alert enabled | Description |
|---|---|---|
| `budget_alert_email` | **Yes** — must be non-empty | Email that receives the notification |
| `budget_start_date` | Recommended | RFC-3339 first day of the billing month, e.g. `"2025-01-01T00:00:00Z"` |
| `budget_amount_usd` | No (default `5`) | Monthly threshold in USD |

`budget_alert_email` is enforced by a `lifecycle precondition` on the budget
resource: Terraform will error at plan time if it is left empty while
`enable_budget_alert = true`.

`budget_start_date` is a plain variable so the value is stable across runs.
Using `timestamp()` was avoided because it re-evaluates on every `plan`/`apply`
and would produce a perpetual diff.

The `Microsoft.Consumption` resource provider must be registered on your
subscription before `apply`:

```bash
az provider register --namespace Microsoft.Consumption
```

If you prefer to skip Terraform-managed budgets, create one manually:
**Azure Portal → Cost Management + Billing → Budgets → Add**.

---

## Security reminders

- **Never commit `terraform.tfvars`** — it contains real secrets.
- `terraform.tfvars` and `*.tfstate*` are already listed in the root
  `.gitignore`. Verify before pushing.
- Rotate `secret_key` and `mongo_uri` via the Azure portal or a secrets
  manager; do not store them in source control.
