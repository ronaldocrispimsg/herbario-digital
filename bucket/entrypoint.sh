#!/bin/sh
set -eu

USER="${MINIO_ROOT_USER:-bioacervo}"
PASS="${MINIO_ROOT_PASSWORD:-bioacervo_minio_password}"

mkdir -p /etc/seaweedfs /data/filerldb2 /data/images /data/exports

cat <<EOF > /etc/seaweedfs/s3.json
{
  "identities": [
    {
      "name": "${USER}",
      "credentials": [
        {
          "accessKey": "${USER}",
          "secretKey": "${PASS}"
        }
      ],
      "actions": [
        "Admin",
        "Read",
        "Write",
        "List",
        "Tagging"
      ]
    },
    {
      "name": "anonymous",
      "actions": [
        "Read",
        "List"
      ]
    }
  ]
}
EOF

echo "Iniciando SeaweedFS (Master, Volume, Filer e S3 Gateway na porta 9000)..."
exec weed server -dir=/data -filer -s3 -s3.port=9000 -s3.config=/etc/seaweedfs/s3.json
