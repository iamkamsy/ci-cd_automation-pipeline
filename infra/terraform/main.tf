locals {
  default_tags = {
    project     = "azure-devops-cicd"
    environment = var.environment
    cost_policy = "free-tier-only"
  }
  tags = merge(local.default_tags, var.tags)
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

# ---------------------------------------------------------------------------
# App Service Plan — F1 (free tier)
# ---------------------------------------------------------------------------

resource "azurerm_service_plan" "main" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku
  tags                = local.tags
}

# ---------------------------------------------------------------------------
# Linux Web App — Flask backend
# ---------------------------------------------------------------------------

resource "azurerm_linux_web_app" "backend" {
  name                = var.app_service_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id
  tags                = local.tags

  site_config {
    # F1 does not support always-on; it must be disabled.
    always_on = false

    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    MONGO_URI                      = var.mongo_uri
    SECRET_KEY                     = var.secret_key
    FLASK_ENV                      = "production"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
  }
}

# ---------------------------------------------------------------------------
# Static Web App — React frontend (Free tier)
# ---------------------------------------------------------------------------

resource "azurerm_static_web_app" "frontend" {
  name                = var.static_web_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku_tier            = var.static_web_app_sku_tier
  sku_size            = var.static_web_app_sku_size
  tags                = local.tags
}

# ---------------------------------------------------------------------------
# Azure Consumption Budget (optional)
# Only created when enable_budget_alert = true.
# Requires the Microsoft.Consumption resource provider to be registered on the
# subscription. If registration is unavailable, set enable_budget_alert = false
# and configure a budget manually in the Azure portal.
# ---------------------------------------------------------------------------

resource "azurerm_consumption_budget_resource_group" "alert" {
  count = var.enable_budget_alert ? 1 : 0

  name              = "${var.resource_group_name}-budget"
  resource_group_id = azurerm_resource_group.main.id

  amount     = var.budget_amount_usd
  time_grain = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThan"
    threshold_type = "Actual"

    contact_emails = [var.budget_alert_email]
  }

  lifecycle {
    precondition {
      condition     = var.budget_alert_email != ""
      error_message = "budget_alert_email must be set to a non-empty address when enable_budget_alert = true."
    }
  }
}
