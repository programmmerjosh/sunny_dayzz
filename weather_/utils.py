import requests
import time

from requests.exceptions import RequestException

def safe_get(url, source_name, retries=3):
    for attempt in range(retries):
        try:
            print(f"📡 Requesting from {source_name} (attempt {attempt+1})...", flush=True)
            response = requests.get(url, timeout=10)
            print(f"📄 {source_name}. URL: {response.url}", flush=True)

            if source_name == "OpenMeteo":
                print(f"\n\n👇👇👇👇👇 JSON response on attempt {attempt+1}: {response.json()}\n\n", flush=True)

            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"⚠️ {source_name} error: {e}", flush=True)
            time.sleep(1)  # short pause before retry
    return None