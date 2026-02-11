FROM postgres:13.1-alpine

COPY --chown=root:root --chmod=755 ["docker-healthcheck.sh", "/usr/local/bin/"]

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --start-interval=2s --retries=1 \
    CMD ["/usr/local/bin/docker-healthcheck.sh"]
