terraform {

  # Use local state storafe by default. For production environments please
  # consider  using a more robust backend.
  backend "local" {
    path = "terraform.tfstate"
  }

  /*
  # Use Google Cloud Storage for state storage.
  # Note: The bucket name need to be globally unique.
  backend "gcs" {
    bucket = "GLOBALY UNIQUE BUCKET NAME "
  }
  */
}

provider "google" {
  project = "${var.project}"
  region  = "${var.region}"
}