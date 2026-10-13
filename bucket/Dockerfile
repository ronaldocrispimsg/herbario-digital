FROM chrislusf/seaweedfs:latest

LABEL org.opencontainers.image.title="BioAcervo Bucket (SeaweedFS)"
LABEL org.opencontainers.image.description="SeaweedFS object storage com API S3 compatível para BioAcervo"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/data"]

EXPOSE 9000 8888 9333

ENTRYPOINT ["/entrypoint.sh"]
