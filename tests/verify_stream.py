import sys
import time
import socket
import requests

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

URL = "http://127.0.0.1:8000/api/v1/chat/stream"

payload = {
    "message": "Hello TITAN, please respond with a short greeting.",
    "org_id": None,
    "location_id": None,
    "enable_sql": True,
}


def wait_for_server(timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False


def main():
    if not wait_for_server():
        print("Server did not become available within 30 seconds.")
        return 5

    try:
        with requests.post(URL, json=payload, stream=True, timeout=60) as resp:
            print(f"Status: {resp.status_code}")
            if not resp.ok:
                print("Response body:")
                print(resp.text)
                return 1

            done_event = False
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                print(line)
                if line.startswith("event: done"):
                    done_event = True
                elif done_event and line.startswith("data:"):
                    break
    except requests.exceptions.ConnectionError as exc:
        print(f"ConnectionError: {exc}")
        return 2
    except requests.exceptions.ReadTimeout as exc:
        print(f"ReadTimeout: {exc}")
        return 3
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())
