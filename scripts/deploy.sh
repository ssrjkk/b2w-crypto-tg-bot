#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t crypto-platform:latest .

echo "Creating Kubernetes namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Applying ConfigMap and Secrets..."
kubectl apply -f k8s/config.yaml

echo "Applying storage (PVC, Redis, Postgres)..."
kubectl apply -f k8s/storage.yaml

echo "Waiting for databases to be ready..."
sleep 30

echo "Applying API deployment..."
kubectl apply -f k8s/deployment.yaml

echo "Applying Celery deployments..."
kubectl apply -f k8s/celery-deployment.yaml

echo "Applying Ingress..."
kubectl apply -f k8s/ingress.yaml

echo "Applying HPA..."
kubectl apply -f k8s/autoscaling.yaml

echo "Checking deployment status..."
kubectl get pods -n crypto-platform

echo "Done! Your application is being deployed."
