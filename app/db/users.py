from app.db.utils import serialize_item
from app.db import DB
from bson import ObjectId
from enum import Enum

# User Collection Name
USER_COLLECTION = "users"

# User fields
USERNAME = "name"
EMAIL = "email"
PASSWORD_HASH = "password_hash"
PHONE = "phone"
ROLE = "role" #"member" ,"trainer", "admin"

class Role(str, Enum):
    MEMBER = "member"
    TRAINER = "trainer"
    ADMIN = "admin"


class UserResource:

    def __init__(self):
        self.collection = DB.get_collection(USER_COLLECTION)

    def create_user(self, username: str, email: str, password_hash: str, phone: str | None = None, role: str = Role.MEMBER.value):
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
    
    def parse_role(self, role):
        if isinstance(role,Role): #if already a Role enum, use it
            return role.value
        if role is None: #else default to MEMBER
            return Role.MEMBER.value
        value = str(role).strip().lower() #normalize to string, ex: if parse_role("Trainer")
        if value not in {r.value for r in Role}:
            raise ValueError(f"Invalid role: {role}")
        return value
    
    def is_trainer(self, user):
        return bool(user) and user.get(ROLE) == Role.TRAINER.value

    def is_admin(self, user):
        return bool(user) and user.get(ROLE) == Role.ADMIN.value

    def can_create_class(self, user):
        return is_trainer(user) or is_admin(user)
    

    

