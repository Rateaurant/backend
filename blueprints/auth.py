from flask import Blueprint, redirect, jsonify, url_for, request
import jwt

from threading import Thread
import re
import os
import sys
from gotrue.errors import AuthApiError


class Auth(object):
    def __init__(self, db, modules) -> None:
        self.auth_router = Blueprint("auth", __name__)
        self.db = db
        self.modules = modules

        self.auth_router.add_url_rule("/register/<mode>", "register", self.register, methods=["POST"])
        self.auth_router.add_url_rule("/login", "login", self.login, methods=["POST"])
        self.auth_router.add_url_rule("/gen_tokens", "gen_tokens", self.gen_token)

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
        
        if self.db.fetch_user_global("email", email) is not None:
            return jsonify({"message": "email alredy registered"}), 406
        
        
        if mode == "user":
            user = self.db.create_customer(username, email, password)
        else:
            user = self.db.create_owner(username, email, password)
        if not user:
            return jsonify({"message": "email alredy registered"}), 406

        return jsonify({"message": "registered"}), 201
    
    def login(self):
        email = request.form.get("email")
        password = request.form.get("password")
        
        if (
                not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)
                or password.strip() == ""
            ):
            return jsonify({"message": "malformed data"}), 400
        
        if not self.db.fetch_user_global("email", email):
            return jsonify({"message": "email not registered"}), 406

        try:
            self.db.authenticate_user(email, password)
        except AuthApiError:
            return jsonify({"message": "not authenticated"}), 401
        
        tokens = self.db.gen_tokens(email)
        tokens['message'] = "success"
        return jsonify(tokens), 200
    
    def gen_token(self):
        refresh_token = request.args.get("refresh_token")
        if refresh_token is None:
            return jsonify({"message": "refresh token not provided"})
        # print(refresh_token)
        new_tokens:dict = self.db.gen_new_access(refresh_token)
        print(new_tokens)
        if "access_token" not in new_tokens:
            new_tokens['message'] = "invalid token"
        else:
            new_tokens['message'] = "success"
        return jsonify(new_tokens)