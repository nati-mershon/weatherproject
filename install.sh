#!/bin/bash
echo "🚀 Installing Weather Service on Kubernetes..."

# Create Kubernetes namespace (if needed)
kubectl create namespace weather-ns || echo "Namespace already exists"

# Deploy SQL Server
kubectl apply -f k8ssqlserver-deployment.yml
kubectl apply -f k8ssqlserver-service.yml

# Wait for database to be ready
echo "⏳ Waiting for SQL Server to initialize..."
sleep 20

# Deploy Weather Service
kubectl apply -f k8sweather-service-deployment.yml
kubectl apply -f k8sweather-service-service.yml

echo "✅ Installation complete!"
