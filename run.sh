#!/bin/bash
echo "🚀 Running Weather Service..."

# Get external IP of the weather service
WEATHER_IP=$(kubectl get service weather-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "🌐 Weather Service API available at: http://$WEATHER_IP:5000"

# Run Streamlit dashboard
echo "🖥️ Starting dashboard on http://localhost:8501"
streamlit run dashboard.py
