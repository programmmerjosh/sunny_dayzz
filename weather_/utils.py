import httpx
import time

from requests.exceptions import RequestException

async def safe_get(url, source_name, retries=3):
    for attempt in range(retries):
        try:

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)

            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"⚠️ {source_name} error (in safe_get): {e}", flush=True)
            time.sleep(1)  # short pause before retry
    return None