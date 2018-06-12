# Register startup scripts. These scripts will be rendered and used when
# machines boot up.

data "template_file" "timesketch" {
  template = "${file("${path.module}/startup_scripts/timesketch.sh")}"
  vars {}
}