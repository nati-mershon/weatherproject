import pyodbc
conn_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=sqlserver,1433;DATABASE=WeatherDB;UID=sa;PWD=YourPassword123;TrustServerCertificate=yes;"
try:
    conn = pyodbc.connect(conn_string)
    print("✅ Connected to SQL Server from Weather Service!")
    conn.close()
except pyodbc.Error as e:
    print(f"❌ Connection failed: {e.args}")
