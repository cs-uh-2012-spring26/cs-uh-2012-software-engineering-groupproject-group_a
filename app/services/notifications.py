from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ReminderData:
    recipient_name: str
    class_name: str
    start_time: str
    location: str
    email: str = None
    telegram_chat_id: str = None

class BaseNotifier(ABC):
    @abstractmethod
    def send(self, reminder: ReminderData) -> bool:
        '''
        Sends a reminder
        Returns True on success and False on failure
        '''

class EmailNotifier(BaseNotifier):
    def send(self, reminder: ReminderData):
        from app.services.email import send_reminder_email
        if not reminder.email:
            return False
        try:
            return send_reminder_email(
                recipient_email=reminder.email,
                recipient_name=reminder.recipient_name,
                class_name=reminder.class_name,
                start_time=reminder.start_time,
                location=reminder.location,
            )
        except Exception:
            return False
        
class TelegramNotifier(BaseNotifier):
    def send(self, reminder: ReminderData):
        from app.services.telegram import send_reminder_telegram
        if not reminder.telegram_chat_id:
            return False
        try:
            return send_reminder_telegram(
                chat_id=reminder.telegram_chat_id,
                recipient_name=reminder.recipient_name,
                class_name=reminder.class_name,
                start_time=reminder.start_time,
                location=reminder.location,
            )
        except Exception:
            return False
    
class NotificationService:
    def __init__(self):
        self._notifiers: dict[str, BaseNotifier] =  {
            "email": EmailNotifier(),
            "telegram": TelegramNotifier(),
        }

    def notify(self, reminder: ReminderData, prefs: list):
        # Send notifications to all channels present in prefs
        sent = 0
        failed = 0
        for channel in prefs:
            notifier = self._notifiers.get(channel)
            if notifier is None:
                continue
            if notifier.send(reminder):
                sent += 1
            else:
                failed += 1
        return sent, failed

