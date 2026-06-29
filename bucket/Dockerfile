FROM quay.io/minio/minio

LABEL org.opencontainers.image.title="BioAcervo Bucket"
LABEL org.opencontainers.image.description="MinIO object storage for BioAcervo uploads and exports"

VOLUME ["/data"]

EXPOSE 9000 9001

CMD ["server", "/data", "--console-address", ":9001"]
