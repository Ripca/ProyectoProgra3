import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', 'admin'),
    database=os.getenv('DB_NAME', 'db_biometrico'),
    use_pure=True
)

cursor = conn.cursor()

with open('database/migration_redesign.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Execute statements one by one
statements = sql_script.split(';')
for statement in statements:
    if statement.strip():
        try:
            cursor.execute(statement)
            try:
                cursor.fetchall()
            except mysql.connector.errors.InterfaceError:
                pass # No result set to fetch
            print(f"Executed: {statement.strip()[:50]}...")
        except Exception as e:
            print(f"Error executing {statement.strip()[:50]}: {e}")

conn.commit()
cursor.close()
conn.close()
print("Migration completed successfully.")
