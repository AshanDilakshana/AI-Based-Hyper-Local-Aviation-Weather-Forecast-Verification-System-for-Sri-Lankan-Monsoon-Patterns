import pandas as pd
import numpy as np

def process_aviation_data(file_path):
    # දත්ත පූරණය
    df = pd.read_excel(file_path)
    
    # දෙවන අන්තර් මෝසම් (ඔක්තෝබර් සහ නොවැම්බර්) සඳහා පමණක් පෙරීම
    sim_data = df[df['Month'].isin([10, 11])].copy()
    
    # දත්ත වර්ග සංඛ්‍යාත්මක කිරීම සහ හිස් දත්ත ඉවත් කිරීම
    sim_data['QNH (hPa)'] = pd.to_numeric(sim_data['QNH (hPa)'], errors='coerce')
    sim_data['RH(%)'] = pd.to_numeric(sim_data['RH(%)'], errors='coerce')
    sim_data = sim_data.dropna(subset=['RH(%)', 'QNH (hPa)'])
    
    # Feature Engineering: පීඩන වෙනස්වීම් සහ ආර්ද්‍රතා උච්චයන්
    sim_data['QNH_Trend'] = sim_data['QNH (hPa)'].diff().fillna(0)
    sim_data['RH_Peak'] = (sim_data['RH(%)'] > sim_data['RH(%)'].mean()).astype(int)
    
    return sim_data