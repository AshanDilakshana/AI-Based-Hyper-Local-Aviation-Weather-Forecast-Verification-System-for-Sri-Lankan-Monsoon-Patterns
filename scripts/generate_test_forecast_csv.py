import csv
from datetime import datetime, timedelta

now = datetime.utcnow()
current_hour = now.replace(minute=0, second=0, microsecond=0)

filename = "test_verified_forecast_next_10h.csv"

with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "UTC", "Wind (deg/kt)", "Air Temp (deg C)", "QNH (hPa)", "Remarks"])
    
    for i in range(10):
        target_time = current_hour + timedelta(hours=i)
        date_str = target_time.strftime("%Y-%m-%d")
        utc_str = target_time.strftime("%H%M")
        
        # Some dummy data
        wind = f"0{(3 + i)*10:02d}15" if i < 7 else f"0{(1 + i)*10:02d}20" # e.g. 03015
        if len(wind) != 5:
            wind = "03015"
        
        temp = 25 - i%3
        qnh = 1010 + i%2
        remarks = "FEW015" if i%2==0 else "SCT020"
        
        writer.writerow([date_str, utc_str, wind, temp, qnh, remarks])

print(f"Generated {filename}")
