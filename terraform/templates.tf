# Register startup scripts. These scripts will be rendered and used when
# machines boot up.

data "template_file" "timesketch" {
  template = "${file("${path.module}/startup_scripts/timesketch.sh")}"
  vars {
    elasticsearch_node = "${google_compute_instance.elasticsearch.*.name[0]}"
  }
}

data "template_file" "elasticsearch" {
  template = "${file("${path.module}/startup_scripts/elasticsearch.sh")}"
  vars {
    es_cluster_name = "${var.es_cluster_name}"
    project = "${var.project}"
    zone = "${var.zone}"
  }
}