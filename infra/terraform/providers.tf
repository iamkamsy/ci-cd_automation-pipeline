terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }

  # No remote state is configured here. Local state is sufficient for individual
  # development, but production deployments should use remote state with locking,
  # for example:
  #
  #   backend "azurerm" {
  #     resource_group_name  = "tfstate-rg"
  #     storage_account_name = "tfstateaccount"
  #     container_name       = "tfstate"
  #     key                  = "prod.terraform.tfstate"
  #   }
  #
  # Remote state prevents concurrent apply conflicts and stores state securely.
}

provider "azurerm" {
  features {}
}
