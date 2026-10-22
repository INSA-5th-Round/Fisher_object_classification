import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from config import settings

logger = logging.getLogger("cctv_backend.telegram")


class TelegramService:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or settings.BOT_TOKEN
        self.chat_id = chat_id or settings.CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def verify_credentials(self) -> Dict[str, Any]:
        """Test if the Telegram bot token is valid."""
        if not self.bot_token:
            return {"valid": False, "error": "BOT_TOKEN is not configured in .env"}
        try:
            res = requests.get(f"{self.base_url}/getMe", timeout=10)
            data = res.json()
            if res.ok and data.get("ok"):
                return {
                    "valid": True,
                    "bot_name": data["result"].get("first_name"),
                    "username": data["result"].get("username"),
                    "chat_id_configured": bool(self.chat_id),
                }
            return {"valid": False, "error": data.get("description", "Unknown Telegram error")}
        except Exception as e:
            logger.error(f"Telegram verify failed: {e}")
            return {"valid": False, "error": str(e)}

    def send_message(self, text: str) -> bool:
        """Send a text message alert."""
        if not self.bot_token or not self.chat_id:
            logger.warning("BOT_TOKEN or CHAT_ID missing; cannot send Telegram message.")
            return False
        try:
            url = f"{self.base_url}/sendMessage"
            res = requests.post(
                url,
                data={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=15,
            )
            if res.ok:
                logger.info("Telegram text message sent successfully.")
                return True
            logger.error(f"Telegram error sending text: {res.text}")
            return False
        except Exception as e:
            logger.error(f"Telegram exception: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Send photo alert."""
        if not self.bot_token or not self.chat_id:
            return False
        path_obj = Path(photo_path)
        if not path_obj.exists():
            logger.error(f"Photo path does not exist: {photo_path}")
            return False
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(path_obj, "rb") as photo:
                res = requests.post(
                    url,
                    data={"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"},
                    files={"photo": photo},
                    timeout=30,
                )
            return res.ok
        except Exception as e:
            logger.error(f"Telegram photo error: {e}")
            return False

    def send_video(self, video_path: str, caption: str = "") -> bool:
        """Send video clip."""
        if not self.bot_token or not self.chat_id:
            return False
        path_obj = Path(video_path)
        if not path_obj.exists():
            logger.error(f"Video path does not exist: {video_path}")
            return False
        try:
            url = f"{self.base_url}/sendVideo"
            with open(path_obj, "rb") as video:
                res = requests.post(
                    url,
                    data={"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"},
                    files={"video": video},
                    timeout=180,
                )
            return res.ok
        except Exception as e:
            logger.error(f"Telegram video error: {e}")
            return False


telegram_service = TelegramService()
