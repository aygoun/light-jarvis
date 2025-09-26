"""Notification client for system notifications and reminders."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
import threading
import time

from jarvis_shared.logger import get_logger

try:
    from plyer import notification

    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class NotificationClient:
    """Client for system notifications and reminders."""

    def __init__(self):
        self.logger = get_logger("jarvis.notification.client")
        self.scheduled_reminders = {}
        self.reminder_thread = None
        self.running = False

    async def send_notification(
        self, title: str, message: str, timeout: int = 10
    ) -> bool:
        """Send a system notification."""
        try:
            if PLYER_AVAILABLE:
                notification.notify(title=title, message=message, timeout=timeout)
                self.logger.info(f"📢 Notification sent: {title}")
                return True
            else:
                # Fallback to console notification
                self.logger.info(f"📢 NOTIFICATION: {title} - {message}")
                return True

        except Exception as e:
            self.logger.error(f"❌ Failed to send notification: {e}")
            return False

    async def schedule_reminder(
        self, reminder_id: str, title: str, message: str, remind_at: datetime
    ) -> bool:
        """Schedule a reminder notification."""
        try:
            if remind_at <= datetime.now():
                # Send immediately if time has passed
                return await self.send_notification(title, message)

            self.scheduled_reminders[reminder_id] = {
                "title": title,
                "message": message,
                "remind_at": remind_at,
                "created_at": datetime.now(),
            }

            # Start reminder thread if not running
            if not self.running:
                self._start_reminder_thread()

            self.logger.info(f"⏰ Reminder scheduled: {title} at {remind_at}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to schedule reminder: {e}")
            return False

    async def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a scheduled reminder."""
        if reminder_id in self.scheduled_reminders:
            del self.scheduled_reminders[reminder_id]
            self.logger.info(f"🚫 Reminder cancelled: {reminder_id}")
            return True
        return False

    def list_reminders(self) -> List[Dict[str, Any]]:
        """List all scheduled reminders."""
        reminders = []
        for reminder_id, reminder in self.scheduled_reminders.items():
            reminders.append(
                {
                    "id": reminder_id,
                    "title": reminder["title"],
                    "message": reminder["message"],
                    "remind_at": reminder["remind_at"].isoformat(),
                    "created_at": reminder["created_at"].isoformat(),
                }
            )
        return reminders

    def _start_reminder_thread(self):
        """Start the reminder checking thread."""
        if self.reminder_thread is None or not self.reminder_thread.is_alive():
            self.running = True
            self.reminder_thread = threading.Thread(
                target=self._reminder_worker, daemon=True
            )
            self.reminder_thread.start()
            self.logger.info("🔄 Reminder thread started")

    def _reminder_worker(self):
        """Worker thread to check and send scheduled reminders."""
        while self.running and self.scheduled_reminders:
            try:
                current_time = datetime.now()
                expired_reminders = []

                for reminder_id, reminder in self.scheduled_reminders.items():
                    if current_time >= reminder["remind_at"]:
                        # Send notification
                        asyncio.run(
                            self.send_notification(
                                reminder["title"], reminder["message"]
                            )
                        )
                        expired_reminders.append(reminder_id)

                # Remove expired reminders
                for reminder_id in expired_reminders:
                    del self.scheduled_reminders[reminder_id]
                    self.logger.info(f"✅ Reminder sent and removed: {reminder_id}")

                # Sleep for 30 seconds before next check
                time.sleep(30)

            except Exception as e:
                self.logger.error(f"❌ Reminder worker error: {e}")
                time.sleep(60)  # Wait longer on error

        self.running = False
        self.logger.info("🛑 Reminder thread stopped")

    def stop_reminders(self):
        """Stop the reminder system."""
        self.running = False
        if self.reminder_thread and self.reminder_thread.is_alive():
            self.reminder_thread.join(timeout=5)
        self.logger.info("🛑 Reminder system stopped")
