# 🌦 Weather Service on Kubernetes

This project provides a **weather data collection service** that runs on **Kubernetes**. 
It fetches weather data for predefined cities and stores it in an **SQL Server** database. 
A **Streamlit dashboard** is also included for easy data visualization.

## 🚀 Features
- Fetches **historical weather data** using Open-Meteo API.
- Stores data in **Microsoft SQL Server** (running in Kubernetes).
- Provides a **REST API** with Flask.
- Includes a **Streamlit dashboard** for visualization.
- Uses **Kubernetes and Docker** for deployment.

## 📦 Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/YOUR_USERNAME/weather_project.git
   cd weather_project
   ```

2. **Run the installation script** (installs Kubernetes services, SQL Server, and weather service):
   ```sh
   chmod +x install.sh
   ./install.sh
   ```

## ▶️ Running the Project

After installation, run:
```sh
chmod +x run.sh
./run.sh
```

The service should now be accessible at:
- **Weather API**: `http://<EXTERNAL-IP>:5000`
- **Dashboard**: `http://localhost:8501`

To find the **EXTERNAL-IP** for the API, run:
```sh
kubectl get services
```

## 🌐 API Endpoints
| Method | Endpoint        | Description |
|--------|---------------|-------------|
| GET    | `/healthz`    | Check service health |
| GET    | `/weather`    | Fetch stored weather data |
| POST   | `/fetch`      | Trigger weather data collection |
| DELETE | `/clear_db`   | Clear all weather data from DB |

## 🛠️ Cleanup
To remove all services and data:
```sh
kubectl delete -f k8s/
```

## 📜 License
This project is licensed under the MIT License.
