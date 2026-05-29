output "resource_group_name" {
  description = "Name of the Azure Resource Group."
  value       = azurerm_resource_group.main.name
}

output "app_service_name" {
  description = "Name of the Linux Web App (Flask backend)."
  value       = azurerm_linux_web_app.backend.name
}

output "backend_url" {
  description = "Default HTTPS hostname of the Flask backend."
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "frontend_url" {
  description = "Default HTTPS hostname of the Static Web App (React frontend)."
  value       = "https://${azurerm_static_web_app.frontend.default_host_name}"
}
