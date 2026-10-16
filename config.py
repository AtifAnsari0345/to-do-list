import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/todo_app")
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    BCRYPT_LOG_ROUNDS = 12
