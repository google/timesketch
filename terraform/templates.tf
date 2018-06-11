data "template_file" "timesketch" {
  template = "${file("${path.module}/startup_scripts/timesketch.sh")}"

  # Any variables to pass on to the script.
  vars {}
}