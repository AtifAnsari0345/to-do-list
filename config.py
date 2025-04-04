import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/todo_app'
    DEBUG = os.environ.get('DEBUG') or True
    BCRYPT_LOG_ROUNDS = 12