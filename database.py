from pymongo import MongoClient
import pymongo.collection
import pymongo
import bcrypt

from uuid import uuid4
import random
from datetime import timedelta, datetime
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

class Database:
    def __init__(self):
        self.client         = MongoClient(os.environ.get('MONGO_URL'))
        self.db             = self.client.rateaurant

        self.users          = self.db.users
        self.owners         = self.db.owners
        self.restaurants    = self.db.restaurants
        self.menus          = self.db.menus

    def check_exist(self, collection:pymongo.collection.Collection, key, value):
        return collection.find_one({key: value}) is not None

    def create_user(self, name, email, password:str):
        if not self.check_exist(self.users, "email", email):
            salt = bcrypt.gensalt(rounds=15)
            hashed = bcrypt.hashpw(password.encode(), salt)
            user_obj = {
                "_id": str(uuid4()),
                "name": name, 
                "email": email,
                "password": hashed,
                "order_history": []
            }
            self.users.insert_one(user_obj)
            return user_obj
        return False