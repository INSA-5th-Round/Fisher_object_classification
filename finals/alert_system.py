import os
import json
import logging
import queue
import threading
from typing import Optional
from telegram_sender import TelegramSender
from config import settings

logger = logging.getLogger("cctv_backend.alert_system")


class AlertSystem:
    """
    Automatic Alert System for FISHER CCTV.
    Handles automatic, non-blocking dispatch of detection frames and recorded videos to Telegram.
    Enforces exactly two images (frame 1 immediately, frame 2 at +3s) and one 2-minute video per intrusion.
    """

    VIDEO_DURATION = settings.INTRUSION_VIDEO_SECONDS  # 120 seconds (2 minutes)

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None, async_mode: bool = True):
        self.bot_token = bot_token or settings.BOT_TOKEN
        self.chat_id = chat_id or settings.CHAT_ID
        self.telegram = TelegramSender(self.bot_token, self.chat_id)
        self.async_mode = async_mode

        # Queue for non-blocking background dispatch
        self._queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = True

        if self.async_mode:
            self._start_worker()

    def _start_worker(self):
        """Starts background worker thread to process Telegram notifications without blocking video feed."""
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True, name="TelegramAlertWorker")
        self._worker_thread.start()

    def _process_queue(self):
        while self._running:
            try:
                task = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                action, kwargs = task
                if action == "photo":
                    self.telegram.send_photo(kwargs["image_path"], kwargs["caption"])
                elif action == "video":
                    self.telegram.send_video(kwargs["video_path"], kwargs["caption"])
            except Exception as e:
                logger.error(f"[AlertSystem Worker Error] {e}")
            finally:
                self._queue.task_done()

    def send_initial_alert(
        self,
        frame_path: str,
        track_id: int,
        object_name: str,
        confidence: float,
        activity: str,
        timestamp: str,
    ) -> bool:
        """
        Send the first intrusion frame immediately to Telegram.
        Non-blocking: dispatches via background thread so video detection never freezes.
        """
        if not os.path.exists(frame_path):
            print(f"[ERROR] Frame not found: {frame_path}")
            return False

        conf_pct = float(confidence) * 100 if float(confidence) <= 1.0 else float(confidence)

        caption = (
            "🚨 <b>FISHER CCTV SECURITY ALERT</b> 🚨\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Restricted Area Intrusion Detected!</b>\n\n"
            f"👤 <b>Target:</b> {object_name.upper()} (ID: {track_id})\n"
            f"🎯 <b>Confidence:</b> {conf_pct:.1f}%\n"
            f"⚠️ <b>Activity:</b> {activity}\n"
            f"🕒 <b>Time:</b> {timestamp}\n\n"
            "📸 <i>First captured intrusion frame (1 of 2). Recording 2-minute incident video...</i> 🎥\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "FISHER Intelligent Defense Platform"
        )

        print(f"\n[FISHER AlertSystem] Queueing initial intrusion frame for Track ID {track_id} to Telegram...")

        if self.async_mode:
            self._queue.put(("photo", {"image_path": frame_path, "caption": caption}))
            return True
        else:
            return self.telegram.send_photo(frame_path, caption)

    def send_update_frame(
        self,
        frame_path: str,
        track_id: int,
        object_name: str,
        activity: str,
        timestamp: str,
        frame_number: int = 2,
    ) -> bool:
        """
        Send the second intrusion frame (captured exactly 3 seconds after confirmation) to Telegram.
        """
        if not os.path.exists(frame_path):
            print(f"[ERROR] Frame not found: {frame_path}")
            return False

        caption = (
            f"👀 <b>FISHER CCTV UPDATE — Frame {frame_number} (+3 Seconds)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Target:</b> {object_name.upper()} (ID: {track_id})\n"
            f"⚠️ <b>Activity:</b> {activity}\n"
            f"🕒 <b>Time:</b> {timestamp}\n\n"
            "📸 <i>Second captured intrusion frame (2 of 2). Recording 2-minute incident video...</i> 🎥\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "FISHER Intelligent Defense Platform"
        )

        print(f"\n[FISHER AlertSystem] Queueing frame 2 (+3s) for Track ID {track_id} to Telegram...")

        if self.async_mode:
            self._queue.put(("photo", {"image_path": frame_path, "caption": caption}))
            return True
        else:
            return self.telegram.send_photo(frame_path, caption)

    def send_completed_video(
        self,
        video_path: str,
        track_id: int,
        object_name: str,
        activity: str,
        timestamp: str,
    ) -> bool:
        """
        Send completed 2-minute recorded incident video to Telegram.
        Non-blocking: dispatches via background thread so video detection never freezes.
        """
        if not os.path.exists(video_path):
            print(f"[ERROR] Video not found: {video_path}")
            return False

        caption = (
            "🎥 <b>FISHER CCTV — INCIDENT VIDEO RECORDING (2 MINUTES)</b> 🎥\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚨 <i>2-minute incident video recording completed for confirmed intrusion.</i>\n\n"
            f"👤 <b>Target:</b> {object_name.upper()}\n"
            f"🆔 <b>Track ID:</b> {track_id}\n"
            f"⚠️ <b>Activity:</b> {activity}\n"
            f"🕒 <b>Incident Time:</b> {timestamp}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "FISHER Automated Incident Documentation"
        )

        print(f"\n[FISHER AlertSystem] Queueing completed 2-minute video {video_path} to Telegram...")

        if self.async_mode:
            self._queue.put(("video", {"video_path": video_path, "caption": caption}))
            return True
        else:
            return self.telegram.send_video(video_path, caption)

    def update_alert_json(self, json_path: str, video_ready: bool) -> bool:
        """Update the existing intrusion JSON."""
        if not os.path.exists(json_path):
            print(f"[ERROR] JSON not found: {json_path}")
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as file:
                alert_data = json.load(file)

            alert_data["video_ready"] = bool(video_ready)
            alert_data["status"] = "video_recording_completed" if video_ready else "video_recording_failed"

            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(alert_data, file, indent=4)

            print("[FISHER AlertSystem] Alert JSON updated.")
            return True
        except Exception as error:
            print(f"[ERROR] Could not update JSON: {error}")
            return False
