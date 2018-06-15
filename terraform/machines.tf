resource "google_compute_instance" "timesketch" {
  name         = "timesketch"
  machine_type = "g1-small"
  zone         = "${var.zone}"

  # Allow to stop/start the machine to enable change machine type.
  allow_stopping_for_update = true

  # Use default Ubuntu image as operating system.
  boot_disk {
    initialize_params {
      image = "${var.ubuntu_1604_image}"
    }
  }

  # Assign a generated public IP address. Needed for SSH access.
  network_interface {
    network       = "default"
    access_config = {}
  }

  # Allow HTTP(S) traffic
  tags = ["http-server", "https-server"]

  # Provision the machine with a script.
  metadata_startup_script = "${data.template_file.timesketch.rendered}"
}

