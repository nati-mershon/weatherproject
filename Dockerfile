# 1️⃣ שימוש בתמונה רשמית של Python 3.12
FROM python:3.12

# 2️⃣ התקנת ODBC Driver כדי לאפשר חיבור ל-SQL Server
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    libssl-dev \
    libffi-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3️⃣ הורדת והתקנת ODBC Driver של Microsoft עבור SQL Server (תיקון apt-key)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | tee /usr/share/keyrings/microsoft.asc && \
    echo "deb [signed-by=/usr/share/keyrings/microsoft.asc] https://packages.microsoft.com/ubuntu/20.04/prod focal main" \
    | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y \
    msodbcsql17 \
    mssql-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4️⃣ הוספת mssql-tools ל-PATH כדי להשתמש ב-SQLCMD בקלות
ENV PATH="$PATH:/opt/mssql-tools/bin"

# 5️⃣ הגדרת משתנה סביבה למנוע יצירת קבצי pyc ולהשתמש בקידוד UTF-8
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

# 6️⃣ יצירת תיקייה לאפליקציה
WORKDIR /app

# 7️⃣ העתקת קובץ התלויות requirements.txt לפני העתקת כל הקוד
COPY requirements.txt /app/

# 8️⃣ התקנת התלויות (flask, pyodbc, requests וכו')
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir prometheus-flask-exporter
# 9️⃣ העתקת שאר הקבצים לקונטיינר
COPY . /app

# 🔟 הפעלת השירות
CMD ["python", "weather_service.py"]
