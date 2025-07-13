terraform {
  required_version = ">= 1.9.0"
  required_providers {
    fly = { source = "pi3ch/fly", version = "~>0.0.24" }
  }
  # cloud {
  #   organization = "<YOUR-TF-CLOUD-ORG>"
  #   workspaces { name = "auto-options-screener-dev" }
  # }
}

provider "fly" {}

#############################
# ⛔️  TEMPORARILY REMOVED PG
#############################
# module "pg" {...}

#############################
# ✅  Phase-1 placeholder
#############################
resource "null_resource" "db_stub" {
  triggers = { note = "Replace with Fly Postgres in Phase-4" }
} 