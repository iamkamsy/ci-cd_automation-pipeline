variable "project_name" {
  type        = string
  description = "Short name used to namespace resources."
  default     = "azure-devops-cicd"
}

variable "environment" {
  type        = string
  description = "Deployment environment label (e.g. dev, staging, prod)."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region for all resources."
  default     = "East US"
}

variable "resource_group_name" {
  type        = string
  description = "Name of the Azure Resource Group."
  default     = "taskmanager-rg"
}

variable "app_service_plan_name" {
  type        = string
  description = "Name of the App Service Plan."
  default     = "taskmanager-plan"
}

variable "app_service_name" {
  type        = string
  description = "Name of the Linux Web App (must be globally unique)."
  default     = "taskmanager-backend"
}

variable "app_service_sku" {
  type        = string
  description = "SKU name for the App Service Plan. Must be F1 to stay within the free tier."
  default     = "F1"

  validation {
    condition     = var.app_service_sku == "F1"
    error_message = "Only the F1 (free) SKU is permitted by this project's cost policy."
  }
}

variable "static_web_app_name" {
  type        = string
  description = "Name of the Azure Static Web App (must be globally unique)."
  default     = "taskmanager-frontend"
}

variable "static_web_app_sku_tier" {
  type        = string
  description = "SKU tier for the Static Web App. Must be Free to stay within the free tier."
  default     = "Free"

  validation {
    condition     = var.static_web_app_sku_tier == "Free"
    error_message = "Only the Free SKU tier is permitted by this project's cost policy."
  }
}

variable "static_web_app_sku_size" {
  type        = string
  description = "SKU size for the Static Web App. Must be Free to stay within the free tier."
  default     = "Free"

  validation {
    condition     = var.static_web_app_sku_size == "Free"
    error_message = "Only the Free SKU size is permitted by this project's cost policy."
  }
}

variable "mongo_uri" {
  type        = string
  description = "MongoDB connection string passed to the Flask backend as an app setting."
  sensitive   = true
}

variable "secret_key" {
  type        = string
  description = "Flask SECRET_KEY passed to the backend as an app setting. Must be a strong random value in production."
  sensitive   = true
}

variable "tags" {
  type        = map(string)
  description = "Additional tags merged with the default cost/policy tags on every resource."
  default     = {}
}

# Budget alert variables — only active when enable_budget_alert = true.

variable "enable_budget_alert" {
  type        = bool
  description = "Set to true to create an Azure consumption budget with an email notification."
  default     = false
}

variable "budget_amount_usd" {
  type        = number
  description = "Monthly budget threshold in USD. Only used when enable_budget_alert = true."
  default     = 5
}

variable "budget_alert_email" {
  type        = string
  description = "Email address for budget alert notifications. Must be a non-empty address when enable_budget_alert = true."
  default     = ""
}

variable "budget_start_date" {
  type        = string
  description = "RFC-3339 start date for the monthly budget period (first day of a month, e.g. 2025-01-01T00:00:00Z). Set this to the first day of the month you want billing to begin. Only used when enable_budget_alert = true."
  default     = "2025-01-01T00:00:00Z"
}
