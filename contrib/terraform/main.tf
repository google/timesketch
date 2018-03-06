# Terraform configuration for Timesketch
# infrastructure.

# Use Google Cloud Storage for keeping state.
terraform {
  backend "gcs" {
      bucket  = "terraform"
  }
}

provider "google" {
  project     = "${var.project}"
  region      = "${var.region}"
}
