import requests
import time

from requests.exceptions import RequestException

def safe_get(url, source_name, retries=3):
    for attempt in range(retries):
        try:
            print(f"📡 Requesting from {source_name} (attempt {attempt+1})...", flush=True)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"⚠️ {source_name} error: {e}", flush=True)
            time.sleep(1)  # short pause before retry
    return None