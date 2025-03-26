FROM redis:7.2.11-alpine

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --start-interval=1s --retries=1 \
    CMD ["redis-cli", "ping"]
