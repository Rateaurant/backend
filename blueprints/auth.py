from flask import Blueprint, redirect, jsonify, url_for, request
import jwt

from threading import Thread
import re
import os
import sys


class Auth(object):
    def __init__(self, db, modules) -> None:
        self.auth_router = Blueprint("auth", __name__)
        self.db = db
        self.modules = modules

        self.auth_router.add_url_rule("/register/<mode>", "register", self.register, methods=["POST"])
        self.auth_router.add_url_rule("/verify", "verify", self.verify)
        self.auth_router.add_url_rule("/login", "login", self.login, methods=["POST"])
    
    # @auth_router.route("/register/<mode>", methods=["POST"])
    def register(self, mode):
        if mode not in ["user", "owner"]:
            return jsonify({"message": "invalid mode"}), 404
        
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if (
                username is None
                or password is None
                or not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email) 
                or username.strip() == "" 
                or password.strip() == ""
            ):
            return jsonify({"message": "malformed data"}), 404
        
        if self.db.check_exist_global("email", email):
            return jsonify({"message": "email alredy registered"}), 406
        
        
        if mode == "user":
            user = self.db.create_user(username, email, password)
        else:
            user = self.db.create_owner(username, email, password)
        if not user:
            return jsonify({"message": "email alredy registered"}), 406
        
        token = jwt.encode({"_id": user['_id'], "mode": mode}, os.environ.get("secret"), algorithm="HS256")
        uri = f"{os.environ.get("HOME")}/verify/?code={token}"

        html =f"""
<p>Hello! Thank you for signing up to Rateaurant!</p>
<p>To Verify your email address, <a href="{uri}">click this link</a></p>
"""
        Thread(target=self.modules.emails.send_email, args=(user['email'], html)).start()
        # send_email(user['email'], html)

        return jsonify({"message": "registered"}), 201
    
    def verify(self):
        code = request.args.get("code")
        try:
            obj = jwt.decode(code, os.environ.get("secret"), algorithms=["HS256"])
        except:
            return jsonify({"message": "invalid code"}), 406
        print(obj)
        self.db.verify_user(obj['mode'], obj['_id'])
        return jsonify({"message": "Verified"}), 202
    
    def login(self):
        email = request.form.get("email")
        password = request.form.get("password")
        
        if (
                not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)
                or password.strip() == ""
            ):
            return jsonify({"message": "malformed data"}), 400
        
        if not self.db.check_exist_global("email", email):
            return jsonify({"message": "email not registered"}), 406
        
        if not self.db.authenticate_user(email, password):
            return jsonify({"message": "invalid password"}), 401
        
        # user = db.fetch_user("email", email)
        token = self.db.gen_token(email)
        res = jsonify({"message": "success"})
        res.headers['set-cookie'] = token
        return res, 200