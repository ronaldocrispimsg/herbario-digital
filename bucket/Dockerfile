FROM alpine:3.20

LABEL org.opencontainers.image.title="BioAcervo Bucket"
LABEL org.opencontainers.image.description="Local persistent file bucket for BioAcervo uploads and exports"

RUN mkdir -p /data/images /data/exports

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/data"]

ENTRYPOINT ["/entrypoint.sh"]
