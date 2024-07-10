from pymongo import MongoClient
import pymongo.collection
import pymongo

from supabase import create_client, Client
from postgrest._sync.request_builder import SyncRequestBuilder
import bcrypt
import jwt

from uuid import uuid4
from datetime import datetime
from datetime import timedelta
import os

class Database:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

        self.customer       = self.supabase.table("customer")
        self.owners         = self.supabase.table("owners")
        self.restaurants    = self.supabase.table("restaurants")

    def fetch_user(self, table:SyncRequestBuilder, key, value):
        res = table.select("*").eq(key, value).execute().model_dump()
        if len(res) == 0:
            return None
        return res[0]

    def fetch_user_global(self, key, value):
        customers = self.fetch_user(self.customer, key, value)
        if customers is not None:
            return customers
        
        owners = self.fetch_user(self.owners, key, value)
        if owners is not None:
            return owners
        return None

    def check_exist(self, collection:pymongo.collection.Collection, key, value):
        return collection.find_one({key: value}) is not None

    def create_user(self, name, email, password:str):
        if self.check_exist(self.users, "email", email):
            return False
        salt = bcrypt.gensalt(rounds=15)
        hashed = bcrypt.hashpw(password.encode(), salt)
        user_obj = {
            "_id": str(uuid4()),
            "type": "user",
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
            "type": "owner",
            "name": name, 
            "email": email,
            "password": hashed,
            "created": datetime.now().timestamp(),
            "verified": False,
            "menu": {},
            "restaurants": []
        }
        self.owners.insert_one(user_obj)
        return user_obj

    def create_restaurant(self, owner, name, addr):
        res_id = str(uuid4())
        res_obj = {
            "_id": res_id,
            "owner": owner,
            "name": name, 
            "addr": addr,
            "created": datetime.now().timestamp(),
            "menu": [],
            "order_history": []
        }
        self.owners.update_one({"_id": owner}, {"$push": {"restaurants": res_id}})
        self.restaurants.insert_one(res_obj)
        return res_obj

    def verify_user(self, mode, user):
        db = self.users if mode == "user" else self.owners
        db.update_one({"_id": user}, {"$set": {"verified": True}})

    def fetch_user(self, key, value):
        user = self.users.find_one({key: value})
        if user is None:
            user = self.owners.find_one({key: value})
        return user

    def authenticate_user(self, email, password:str):
        user = self.fetch_user("email", email)
        if user:
            return bcrypt.checkpw(password.encode(), user['password'])

    def gen_token(self, email):
        d = (datetime.now() + timedelta(days=7))
        _id = self.fetch_user("email", email)['_id']
        token = jwt.encode({"_id": _id, "exp": d}, os.environ.get("secret"), algorithm="HS256")
        return token

    def authenticate_token(self, token):
        try:
            data = jwt.decode(token, os.environ.get("secret"), algorithms=["HS256"])
            return data['_id']
        except:
            return False