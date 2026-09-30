import time
import requests

start = time.time()
try:
    resp = requests.get('http://localhost:8000/forecasts/ai-predict-all')
    print("Status code:", resp.status_code)
except Exception as e:
    print(e)
print("Time taken: {:.2f}s".format(time.time() - start))
