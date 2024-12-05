import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.results import UpdateResult
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, StrictBool
from dotenv import load_dotenv

load_dotenv()


class User(BaseModel):
    """
    User model representing a user in the system.

    Attributes:
        email (str | EmailStr): The email address of the user.
        phone_number (str | None): The phone number of the user. Defaults to None.
        username (str | None): The username of the user. Defaults to None.
        disabled (StrictBool | None): Indicates if the user is disabled. Defaults to False.
        description (str | None): A brief description of the user. Defaults to None.
    """

    email: str | EmailStr
    phone_number: str | None = None
    username: str | None = None
    disabled: StrictBool | None = False
    description: str | None = None


class UserInDB(User):
    """
    UserInDB is a class that extends the User class to include additional fields
    specific to database storage.

    Attributes:
        password1 (str): The user's password.
        registration_date (datetime | None): The date the user registered. Defaults to None.
        last_login (datetime | None): The date the user last logged in. Defaults to None.
        registration_ip (str | None): The IP address used during registration. Defaults to None.
        last_ip (str | None): The IP address used during the last login. Defaults to None.
        role (str | None): The role of the user. Defaults to "user".
    """

    password1: str
    registration_date: datetime | None = None
    last_login: datetime | None = None
    registration_ip: str | None = None
    last_ip: str | None = None
    role: str | None = "user"


class Item(UserInDB):
    """
    Represents an item in the database.

    Attributes:
        item_id (str): The unique identifier for the item.
        owner (str): The owner of the item.
    """

    item_id: str
    owner: str


class Thread(BaseModel):
    """
    Represents a discussion thread in the database.

    Attributes:
        thread_id (str): Unique identifier for the thread.
        title (str): Title of the thread.
        created_by (str): Username or identifier of the user who created the thread.
        created_at (datetime): Timestamp when the thread was created.
        last_updated (datetime | None): Timestamp when the thread was last updated, if applicable.
        disabled (StrictBool): Indicates whether the thread is disabled. Defaults to False.
    """

    thread_id: str
    title: str
    created_by: str
    created_at: datetime
    last_updated: datetime | None = None
    disabled: StrictBool = False


class Message(BaseModel):
    """
    Represents a message in the database.

    Attributes:
        message_id (str): Unique identifier for the message.
        content (str): The content of the message.
        created_by (str): The identifier of the user who created the message.
        created_at (datetime): The timestamp when the message was created.
        thread_id (str): The identifier of the thread to which the message belongs.
    """

    message_id: str
    content: str
    created_by: str
    created_at: datetime
    thread_id: str


class Payment(BaseModel):
    """
    Represents a payment record.

    Attributes:
        amount (float): The amount of the payment.
        currency (str): The currency in which the payment was made.
        paid_by (str): The entity that made the payment.
        date (datetime): The date when the payment was made.
        status (str | None): The status of the payment, which can be None.
    """

    amount: float
    currency: str
    paid_by: str
    date: datetime
    status: str | None = None


class Setting(BaseModel):
    """
    Setting model representing a configuration setting.

    Attributes:
        created_by (str): The identifier of the user or system that created the setting.
        key (str): The key or name of the setting.
        value (str): The value associated with the key.
    """

    created_by: str
    key: str
    value: str


class Database:
    """
    A class to interact with the MongoDB database using asynchronous operations.
    Attributes:
        client (AsyncIOMotorClient): The MongoDB client.
        db (Database): The MongoDB database.
        users (Collection): The users collection.
        threads (Collection): The threads collection.
        payments (Collection): The payments collection.
        settings (Collection): The settings collection.
        messages (Collection): The messages collection.
    Methods:
        get_object_id(collection: str, key: str, value: str) -> str | None:
            Retrieves the object ID from a specified collection based on a key-value pair.
        create_user(user: UserInDB):
            Creates a new user in the users collection.
        get_user(**kwargs) -> dict | None:
            Retrieves a user from the users collection based on provided search parameters.
        update_user(email: str, field: str, value) -> UpdateResult | None:
            Updates a user's field in the users collection based on the provided email.
        create_thread(thread: Thread):
            Creates a new thread in the threads collection.
        get_threads(**kwargs) -> list | None:
            Retrieves threads from the threads collection based on provided search parameters.
        update_thread(thread_id: str, field: str, value) -> UpdateResult | None:
            Updates a thread's field in the threads collection based on the provided thread ID.
        add_message_to_thread(thread_id: str, message: str, user_id: str):
            Adds a message to a thread and updates the thread's last updated timestamp.
        get_thread_messages(thread_id: str, created_by: str) -> list | None:
            Retrieves messages from a thread based on the thread ID and the user who created the messages.
        create_payment(payment: Payment):
            Creates a new payment in the payments collection.
        get_payment(**kwargs) -> dict | None:
            Retrieves a payment from the payments collection based on provided search parameters.
        update_payment(paid_by: str, field: str, value):
            Updates a payment's field in the payments collection based on the provided paid_by identifier.
        create_setting(setting: Setting):
            Creates a new setting in the settings collection.
        get_setting(**kwargs) -> dict | None:
            Retrieves a setting from the settings collection based on provided search parameters.
        update_setting(created_by: str, field: str, value):
            Updates a setting's field in the settings collection based on the provided created_by identifier.
    """

    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGO_URI") or "mongodb://localhost:27017")
        self.db = self.client[os.getenv("MONGO_DB") or "db"]
        self.users = self.db[os.getenv("MONGO_DB_COLLECTION_USERS") or "users"]
        self.threads = self.db[os.getenv("MONGO_DB_COLLECTION_THREADS") or "threads"]
        self.payments = self.db[os.getenv("MONGO_DB_COLLECTION_PAYMENTS") or "payments"]
        self.settings = self.db[os.getenv("MONGO_DB_COLLECTION_SETTINGS") or "settings"]
        self.messages = self.db[os.getenv("MONGO_DB_COLLECTION_MESSAGES") or "messages"]

    async def get_object_id(self, collection: str, key: str, value: str) -> str | None:
        try:
            result = await self.db[collection].find_one({key: value})
            return result["_id"] if result else None
        except Exception as e:
            return f"Error getting object id: {e}"

    async def create_user(self, user: UserInDB):
        try:
            existing_user = await self.get_user(email=user.email)
            print(existing_user)
            if existing_user is not None:
                return False
            return await self.users.insert_one(user.model_dump())
        except Exception as e:
            return f"Error creating user: {e}"

    async def get_user(self, **kwargs) -> dict | None:
        try:
            valid_fields = User.model_fields.keys()
            if not all(key in valid_fields for key in kwargs.keys()):
                return "Invalid search parameters"
            if not kwargs:
                return "At least one search parameter must be provided"
            result = await self.users.find_one(kwargs)
            if result is None:
                return result
            if result.get("disabled"):
                return "User is disabled"
            return result
        except Exception as e:
            return f"Error getting user: {e}"

    async def update_user(self, email: str, field: str, value) -> UpdateResult | None:
        try:
            valid_fields = UserInDB.model_fields.keys()
            if field not in valid_fields:
                return f"Invalid field: {field}"
            object_id = await self.get_object_id("users", "email", email)
            return await self.users.update_one({"_id": object_id}, {"$set": {field: value}})
        except Exception as e:
            return f"Error updating user: {e}"

    async def create_thread(self, thread: Thread):
        try:
            return await self.threads.insert_one(thread.model_dump())
        except Exception as e:
            return f"Error creating thread: {e}"

    async def get_threads(self, **kwargs) -> list | None:
        try:
            valid_fields = Thread.model_fields.keys()
            if not (key in valid_fields for key in kwargs.keys()):
                return "Invalid search parameters"
            if not kwargs:
                return "At least one search parameter must be provided"
            return await self.threads.find(kwargs).to_list()
        except Exception as e:
            return f"Error getting thread: {e}"

    async def update_thread(self, thread_id: str, field: str, value) -> UpdateResult | None:
        try:
            valid_fields = Thread.model_fields.keys()
            if field not in valid_fields:
                return f"Invalid field: {field}"
            return await self.threads.update_one({"thread_id": thread_id}, {"$set": {field: value}})
        except Exception as e:
            return f"Error updating thread: {e}"

    async def add_message_to_thread(self, thread_id: str, message: str, user_id: str):
        try:
            new_message = {
                "thread_id": thread_id,
                "content": message,
                "created_by": user_id,
                "created_at": datetime.now(timezone.utc),
            }
            result = await self.db.messages.insert_one(new_message)
            await self.db.threads.update_one(
                {"thread_id": thread_id},
                {"$set": {"last_updated": datetime.now(timezone.utc)}},
            )
            return result.inserted_id
        except Exception as e:
            return f"Error adding message to thread: {e}"

    async def get_thread_messages(self, thread_id: str, created_by: str) -> list | None:
        try:
            messages = (
                await self.db.messages.find({"thread_id": thread_id, "created_by": created_by})
                .sort("created_at", 1)
                .to_list(None)
            )
            return messages
        except Exception as e:
            return f"Error retrieving thread messages: {e}"

    async def create_payment(self, payment: Payment):
        try:
            return self.payments.insert_one(payment.model_dump())
        except Exception as e:
            return f"Error creating payment: {e}"

    async def get_payment(self, **kwargs) -> dict | None:
        try:
            valid_fields = Payment.model_fields.keys()
            if not (key in valid_fields for key in kwargs.keys()):
                return "Invalid search parameters"
            if not kwargs:
                return "At least one search parameter must be provided"
            return await self.payments.find_one(kwargs)
        except Exception as e:
            return f"Error getting payment: {e}"

    async def update_payment(self, paid_by: str, field: str, value):
        try:
            valid_fields = Payment.model_fields.keys()
            if field not in valid_fields:
                return f"Invalid field: {field}"
            object_id = await self.get_object_id("payments", "paid_by", paid_by)
            return await self.payments.update_one({"_id": object_id}, {"$set": {field: value}})
        except Exception as e:
            return f"Error updating payment: {e}"

    async def create_setting(self, setting: Setting):
        try:
            return await self.settings.insert_one(setting.model_dump())
        except Exception as e:
            return f"Error creating setting: {e}"

    async def get_setting(self, **kwargs) -> dict | None:
        try:
            valid_fields = Setting.model_fields.keys()
            if not (key in valid_fields for key in kwargs.keys()):
                return "Invalid search parameters"
            if not kwargs:
                return "At least one search parameter must be provided"
            return await self.settings.find_one(kwargs)
        except Exception as e:
            return f"Error getting setting: {e}"

    async def update_setting(self, created_by: str, field: str, value):
        try:
            valid_fields = Setting.model_fields.keys()
            if field not in valid_fields:
                return f"Invalid field: {field}"
            object_id = await self.get_object_id("settings", "created_by", created_by)
            return await self.settings.update_one({"_id": object_id}, {"$set": {field: value}})
        except Exception as e:
            return f"Error updating setting: {e}"


if __name__ == "__main__":
    pass
