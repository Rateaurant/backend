from pymongo import MongoClient
import pymongo.collection
import pymongo
import bcrypt

from uuid import uuid4
from datetime import datetime
import os

class Database:
    def __init__(self):
        self.client         = MongoClient(os.environ.get('MONGO_URL'))
        self.db             = self.client.rateaurant

        self.users          = self.db.users
        self.owners         = self.db.owners
        self.restaurants    = self.db.restaurants

    def check_exist(self, collection:pymongo.collection.Collection, key, value):
        return collection.find_one({key: value}) is not None

    def create_user(self, name, email, password:str):
        if self.check_exist(self.users, "email", email):
            return False
        salt = bcrypt.gensalt(rounds=15)
        hashed = bcrypt.hashpw(password.encode(), salt)
        user_obj = {
            "_id": str(uuid4()),
            "name": name, 
            "email": email,
            "password": hashed,
            "created": datetime.now().timestamp(),
            "verified": False,
            "order_history": []
        }
        self.users.insert_one(user_obj)
        return user_obj
    
    def create_owner(self, name, email, password:str):
        if self.check_exist(self.owners, "email", email):
            return False
        salt = bcrypt.gensalt(rounds=15)
        hashed = bcrypt.hashpw(password.encode(), salt)
        user_obj = {
            "_id": str(uuid4()),
            "name": name, 
            "email": email,
            "password": hashed,
            "created": datetime.now().timestamp(),
            "menu": {},
            "restaurants": []
        }
        self.owners.insert_one(user_obj)
        return user_obj

    def create_restaurant(self, owner, name, addr, contact_no):
        res_id = str(uuid4())
        res_obj = {
            "_id": res_id,
            "owner": owner,
            "name": name, 
            "addr": addr,
            "contact_no": contact_no,
            "created": datetime.now().timestamp(),
            "menu": [],
            "order_history": []
        }
        self.owners.update_one({"_id": owner}, {"$push": {"restaurants": res_id}})
        self.restaurants.insert_one(res_obj)
        return res_obj
    
    def verify_user(self, user):
        self.users.update_one({"_id": user}, {"$set": {"verified": True}})