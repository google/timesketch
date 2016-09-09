if(ctx._source.timesketch_label.contains (timesketch_label)) {
    ctx._source.timesketch_label.remove(timesketch_label)
} else {
    ctx._source.timesketch_label += timesketch_label
}