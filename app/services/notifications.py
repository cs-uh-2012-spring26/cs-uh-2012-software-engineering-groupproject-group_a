from dataclasses import dataclass
from abc import ABC, abstractmethod
from app.services.email import send_reminder_email
from app.services.telegram import send_reminder_telegram

@dataclass
class ReminderData:
    recipient_name: str
    class_name: str
    start_time: str
    location: str

class BaseNotifier(ABC):
    @abstractmethod
    def send(self, reminder: ReminderData, contact_details: dict) -> bool:
        '''
        Sends a reminder using details from contact_details
        Returns True on success and False on failure
        '''

class EmailNotifier(BaseNotifier):
    def send(self, reminder: ReminderData, contact_details: dict):
        email = contact_details.get("email")
        if not email:
            return False
        try:
            return send_reminder_email(
                recipient_email=email,
                recipient_name=reminder.recipient_name,
                class_name=reminder.class_name,
                start_time=reminder.start_time,
                location=reminder.location,
            )
        except Exception:
            return False
        
class TelegramNotifier(BaseNotifier):
    def send(self, reminder: ReminderData, contact_details: dict):
        chat_id = contact_details.get("telegram")
        if not chat_id:
            return False
        try:
            return send_reminder_email(
                chat_id=chat_id,
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

    def notify(self, reminder: ReminderData, prefs: dict):
        # Send notifications to all channels present in prefs
        sent = 0
        failed = 0
        for channel in prefs:
            notifier = self._notifiers.get(channel)
            if notifier is None:
                continue
            if notifier.send(reminder, prefs):
                sent += 1
            else:
                failed += 1
        return sent, failed

