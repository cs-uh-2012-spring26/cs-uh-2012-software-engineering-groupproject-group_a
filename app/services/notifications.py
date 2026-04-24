from dataclasses import dataclass

@dataclass
class ReminderData:
    recipient_email: str
    recipient_name: str
    class_name: str
    start_time: str
    location: str

