
FROM python:3.12


RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    libssl-dev \
    libffi-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | tee /usr/share/keyrings/microsoft.asc && \
    echo "deb [signed-by=/usr/share/keyrings/microsoft.asc] https://packages.microsoft.com/ubuntu/20.04/prod focal main" \
    | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y \
    msodbcsql17 \
    mssql-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


ENV PATH="$PATH:/opt/mssql-tools/bin"


ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8


WORKDIR /app


COPY requirements.txt /app/


RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir prometheus-flask-exporter

COPY . /app


CMD ["python", "weather_service.py"]
