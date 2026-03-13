import boto3
from botocore.exceptions import ClientError
from app.config import get_required_environ

AWS_REGION        = get_required_environ("AWS_REGION")  
SES_SENDER_EMAIL  = get_required_environ("SES_SENDER_EMAIL")

def send_reminder_email(recipient_email: str, recipient_name: str, class_name: str, start_time: str, location: str) -> bool:
    """
    Send a single reminder email via Amazon SES
    Returns True on success, False on failure
    """
    subject = f"Reminder: Your {class_name} class is coming up!"
    body_text = (
        f"Hi {recipient_name},\n\n"
        f"This is a reminder that you are registered for {class_name}.\n"
        f"Start time : {start_time}\n"
        f"Location   : {location}\n\n"
        f"See you there!\n"
    )
    body_html = f"""
    <html>
      <body>
        <p>Hi {recipient_name},</p>
        <p>This is a reminder that you are registered for <strong>{class_name}</strong>.</p>
        <ul>
          <li><strong>Start time:</strong> {start_time}</li>
          <li><strong>Location:</strong> {location}</li>
        </ul>
        <p>See you there!</p>
      </body>
    </html>
    """
 
    client = boto3.client("ses", region_name=AWS_REGION)
    try:
        client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
        return True
    except ClientError:
        return False
 