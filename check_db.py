import sqlite3
import pandas as pd

conn = sqlite3.connect('../weather_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

for t in tables:
    table_name = t[0]
    print(f"\nSchema for {table_name}:")
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
    print(df.info())
    print(df.head())

conn.close()
