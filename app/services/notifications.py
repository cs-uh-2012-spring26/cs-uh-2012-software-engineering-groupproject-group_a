from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ReminderData:
    recipient_email: str
    recipient_name: str
    class_name: str
    start_time: str
    location: str

class BaseNotifier(ABC):
    @abstractmethod
    def send(self, reminder: ReminderData) -> bool:
        '''Sends a reminder, returns True on success and False on failure'''

class EmailNotifier(BaseNotifier):
    def send(self, reminder: ReminderData):
        from app.services.email import send_reminder_email
        return send_reminder_email(
            recipient_email=reminder.recipient_email,
            recipient_name=reminder.recipient_name,
            class_name=reminder.class_name,
            start_time=reminder.start_time,
            location=reminder.location,
        )
    
class NotificationService:
    def __init__(self):
        self._notifiers: dict[str, BaseNotifier] =  {"email": EmailNotifier(),}

    def notify(self, reminder: ReminderData, prefs: list[str]):
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

