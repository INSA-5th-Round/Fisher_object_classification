import os
import time
import json
import urllib.request
import urllib.parse

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

API = f"https://api.telegram.org/bot{TOKEN}"


def telegram(method, data=None):
    url = f"{API}/{method}"

    if data:
        encoded = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, data=encoded)
    else:
        request = urllib.request.Request(url)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def send_message(chat_id, text):
    return telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


def main():
    print("FISHER Telegram bot started...")
    offset = None

    while True:
        try:
            data = {"timeout": 30}

            if offset is not None:
                data["offset"] = offset

            result = telegram("getUpdates", data)

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                print(f"Message received: {text}")

                if text == "/start":
                    reply = (
                        "🚨 FISHER Alert Bot\n\n"
                        "Bot is online and ready."
                    )

                elif text.lower() == "hello":
                    reply = "Hello 👋 FISHER Alert Bot is working!"

                else:
                    reply = f"Received: {text}"

                send_message(chat_id, reply)
                print("Response sent.")

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
