import logging
from pathlib import Path
import requests

logger = logging.getLogger("cctv_backend.telegram_sender")


class TelegramSender:
    """
    Sends alerts, photos, and videos to Telegram Bot.
    """

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_photo(self, image_path: str, caption: str = "") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("BOT_TOKEN or CHAT_ID missing; skipping Telegram photo.")
            return False

        path_obj = Path(image_path)
        if not path_obj.exists():
            print(f"[TELEGRAM ERROR] Photo file not found: {image_path}")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            with open(path_obj, "rb") as photo:
                response = requests.post(
                    url,
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    files={"photo": photo},
                    timeout=30,
                )

            if response.ok:
                print(f"[TELEGRAM] Photo sent successfully: {image_path}")
                return True

            print(f"[TELEGRAM ERROR] {response.status_code}: {response.text}")
            return False
        except Exception as error:
            print(f"[TELEGRAM ERROR] Failed sending photo: {error}")
            return False

    def send_video(self, video_path: str, caption: str = "") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("BOT_TOKEN or CHAT_ID missing; skipping Telegram video.")
            return False

        path_obj = Path(video_path)
        if not path_obj.exists():
            print(f"[TELEGRAM ERROR] Video file not found: {video_path}")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        try:
            with open(path_obj, "rb") as video:
                response = requests.post(
                    url,
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    files={"video": video},
                    timeout=180,
                )

            if response.ok:
                print(f"[TELEGRAM] Video sent successfully: {video_path}")
                return True

            print(f"[TELEGRAM ERROR] {response.status_code}: {response.text}")
            return False
        except Exception as error:
            print(f"[TELEGRAM ERROR] Failed sending video: {error}")
            return False
