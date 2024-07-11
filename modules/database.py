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

        self.customers       = self.supabase.table("customers")
        self.owners         = self.supabase.table("owners")
        self.restaurants    = self.supabase.table("restaurants")

    def fetch_user(self, table:SyncRequestBuilder, key, value):
        res = table.select("*").eq(key, value).execute().model_dump()['data']
        if len(res) == 0:
            return None
        return res[0]

    def fetch_user_global(self, key, value):
        customers = self.fetch_user(self.customers, key, value)
        if customers is not None:
            return customers
        
        owners = self.fetch_user(self.owners, key, value)
        if owners is not None:
            return owners
        return None

    def create_customer(self, name, email, password):
        user = self.create_user(email, password, "customer")
        user_obj = {
            "_id": user.user.id,
            "name": name, 
            "email": email,
            "order_history": []
        }
        self.customers.insert(user_obj).execute()
        return user_obj

    def create_owner(self, name, email, password):
        user = self.create_user(email, password, "owner")
        user_obj = {
            "_id": user.user.id,
            "name": name, 
            "email": email,
            "menu": {},
            "restaurants": []
        }
        self.owners.insert(user_obj).execute()
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
    
    def create_user(self, email, password, typ):
        return self.supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"type": typ}
            }
        })

    def authenticate_user(self, email, password:str):
        user = self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return user.session

    def gen_tokens(self, email):
        d = datetime.now()
        _id = self.fetch_user_global("email", email)['_id']
        access_token = jwt.encode({"_id": _id, "exp": d+timedelta(days=7), "type": "access"}, os.environ.get("secret"), algorithm="HS256")
        refresh_token = jwt.encode({"_id": _id, "exp": d+timedelta(days=90), "type": "refresh"}, os.environ.get("secret"), algorithm="HS256")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    def gen_new_access(self, refresh_token):
        try:
            data = jwt.decode(refresh_token, os.environ.get("secret"), algorithms=["HS256"])
            print(data)
            if data['type'] == "refresh":
                _id = data['_id']
                d = datetime.now()
                new_access_token = jwt.encode({"_id": _id, "exp": d+timedelta(days=7), "type": "access"}, os.environ.get("secret"), algorithm="HS256")
                new_refresh_token = jwt.encode({"_id": _id, "exp": d+timedelta(days=90), "type": "refresh"}, os.environ.get("secret"), algorithm="HS256")
                return {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token
                }
        except:
            pass
        return {}
