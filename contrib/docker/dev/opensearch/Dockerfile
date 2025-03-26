FROM opensearchproject/opensearch:2.15.0

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --start-interval=5s --retries=1 \
    CMD ["curl", "-f", "-s", "http://localhost:9200/_cluster/health"]

