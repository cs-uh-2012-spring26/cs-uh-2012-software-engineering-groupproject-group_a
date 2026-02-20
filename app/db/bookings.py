from app.db.utils import serialize_item, serialize_items
from app.db import DB
from datetime import datetime

#Booking collection name
BOOKING_COLLECTION = "bookings"
#Booking fields
USER_ID = "user_id"
CLASS_ID = "class_id"
BOOKING_DATETIME = "booking_datetime"


class BookingResource:
    def __init__(self):
        self.collection = DB.get_collection(BOOKING_COLLECTION)

    def create_booking(self, user_id: str, class_id: str):
        booking = { #build a new booking from input given by user
            USER_ID: user_id,
            CLASS_ID: class_id,
            BOOKING_DATETIME: datetime.now().isoformat()
        }
        result = self.collection.insert_one(booking)
        return str(result.inserted_id)

    def get_user_bookings(self, user_id: str):
        bookings = self.collection.find({USER_ID: user_id})
        return serialize_items(list(bookings))
    
    def get_class_bookings(self, class_id: str):
        bookings = self.collection.find({CLASS_ID: class_id})
        return serialize_items(list(bookings))

    def get_booking(self, user_id: str, class_id: str):
        booking = self.collection.find_one({USER_ID: user_id, CLASS_ID: class_id})
        return serialize_item(booking)
    


