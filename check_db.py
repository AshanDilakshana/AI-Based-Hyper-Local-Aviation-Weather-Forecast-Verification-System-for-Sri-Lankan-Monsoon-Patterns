import sqlite3
import pandas as pd

conn = sqlite3.connect('weather_data_.db')
print("Tables:", pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn))
print("Sample Data:")
print(pd.read_sql_query("SELECT * FROM weather_data LIMIT 5", conn))
