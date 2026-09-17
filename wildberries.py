import os
import requests


REEF_API_KEY = os.getenv("REEF_API_KEY", "").strip()

REEF_URL = "https://api.reefapi.com/wildberries/v1/search"


def test_reefapi():
    print("=" * 60)
    print("STYLEFLOW — REEFAPI TEST")
    print("=" * 60)

    if not REEF_API_KEY:
        print("❌ REEF_API_KEY не найден")
        return

    print("🔑 API ключ найден")
    print(f"🌐 URL: {REEF_URL}")
    print("📡 Отправляем запрос...")
    print()

    headers = {
        "x-api-key": REEF_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "query": "кроссовки",
        "country": "by",
        "page": 1,
    }

    try:
        response = requests.post(
            REEF_URL,
            headers=headers,
            json=payload,
            timeout=(10, 30),
        )

        print(f"✅ HTTP: {response.status_code}")
        print()

        print("Ответ сервера:")
        print(response.text[:5000])

    except requests.exceptions.ConnectTimeout:
        print("❌ ConnectTimeout")
        print("Не удалось установить соединение с ReefAPI.")

    except requests.exceptions.ReadTimeout:
        print("❌ ReadTimeout")
        print("ReefAPI установил соединение, но не ответил.")

    except requests.exceptions.ConnectionError as e:
        print("❌ ConnectionError")
        print(e)

    except requests.exceptions.RequestException as e:
        print("❌ RequestException")
        print(e)

    except Exception as e:
        print("❌ Неожиданная ошибка:")
        print(repr(e))


if __name__ == "__main__":
    test_reefapi()
