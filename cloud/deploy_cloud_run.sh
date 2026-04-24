#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID='your-gcp-project-id'
REGION='us-central1'
SERVICE='echo-a2a-agent'
REPO='a2a-lab'
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:latest"

gcloud artifacts repositories create ${REPO} \
  --repository-format=docker \
  --location=${REGION} \
  --project=${PROJECT_ID} \
  --quiet 2>/dev/null || true

gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

docker build -t ${IMAGE} ./server
docker push ${IMAGE}

gcloud run deploy ${SERVICE} \
  --image=${IMAGE} \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --port=8080 \
  --project=${PROJECT_ID}

SERVICE_URL=$(gcloud run services describe ${SERVICE} \
  --platform=managed \
  --region=${REGION} \
  --format='value(status.url)' \
  --project=${PROJECT_ID})

echo "Service URL: ${SERVICE_URL}"
