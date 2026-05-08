import pandas as pd
import numpy as np
import os

def preprocess_and_engineer_features(input_path, output_path):
    # 1. Load Data
    if not os.path.exists(input_path):
        print(f"Error: The file {input_path} was not found.")
        return

    print("Loading METAR data...")
    df = pd.read_csv(input_path)
    
    # 2. Map exact column names from the CSV
    # Your dataset uses 'RH(%)' and 'QNH (hPa)'
    rh_col = 'RH(%)'
    qnh_col = 'QNH (hPa)'
    
    # 3. Handle Missing Values
    # Weather data often has trailing commas or empty strings; convert to NaN then fill
    df[rh_col] = pd.to_numeric(df[rh_col], errors='coerce')
    df[qnh_col] = pd.to_numeric(df[qnh_col], errors='coerce')
    df = df.ffill()
    
    # 4. Feature Engineering for Second Inter-Monsoon
    print("Engineering features for RH and QNH...")
    
    # Rate of change over previous 3 records
    df['qnh_drop_3h'] = df[qnh_col].diff(periods=3)
    df['rh_change_3h'] = df[rh_col].diff(periods=3)
    
    # Interaction Feature: High Humidity combined with Pressure
    # Creating a stability index based on the interaction
    df['rh_qnh_interaction'] = df[rh_col] / df[qnh_col]
    
    # Define Target: Change in QNH over the next 3 time steps
    df['target_future_qnh_drop'] = df[qnh_col].shift(-3) - df[qnh_col]
    
    # Drop rows with NaN values created by shifting/diffing
    df = df.dropna()
    
    # 5. Save Processed Data
    df.to_csv(output_path, index=False)
    print(f"Success! Processed data saved to: {output_path}")

if __name__ == "__main__":
    # Ensure the path matches your actual filename in the data folder
    RAW_DATA = './data/BIA_METAR_DATA_(2019_2024).xlsx'
    PROCESSED_DATA = '../data/processed_features.csv'
    
    preprocess_and_engineer_features(RAW_DATA, PROCESSED_DATA)