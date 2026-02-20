from app.db.utils import serialize_item, serialize_items
from app.db import DB
from bson import ObjectId

# User Collection Name
USER_COLLECTION = "users"

# User fields
USERNAME = "name"
EMAIL = "email"
PASSWORD_HASH = "password_hash"
PHONE = "phone"
ROLE = "role" #"member" ,"trainer", "admin"


class UserResource:

    def __init__(self):
        self.collection = DB.get_collection(USER_COLLECTION)

    def create_user(self, username: str, email: str, password_hash: str, phone: str | None = None, role: str = "member"):
        user = {
            USERNAME: username,
            EMAIL: email,
            PASSWORD_HASH: password_hash,
            PHONE: phone,
            ROLE: role,
        }
        result = self.collection.insert_one(user)
        return str(result.inserted_id)

    def get_user_by_username(self, username: str):
        user = self.collection.find_one({USERNAME: username})
        return serialize_item(user)
        
    def get_user_by_email(self, email: str):
        user = self.collection.find_one({EMAIL: email})
        return serialize_item(user)

    def get_user_by_id(self, user_id: str): #look up a user by their MongoDB _id string. Returns a serialized user dict or None.
        try:
            obj_id = ObjectId(user_id) #convert string to ObjectId
        except Exception:
            return None #if str invalid, return None, no valid user

        user = self.collection.find_one({"_id": obj_id}) 
        return serialize_item(user) 
