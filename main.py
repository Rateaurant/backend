from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from dotenv import load_dotenv
from flask_cors import CORS 

import json
import os
import re

from database import Database
from emails import send_email
from logic import encode, decode

load_dotenv()

app = Flask(__name__)
db = Database()

CORS(app) 

@app.route("/")
def index():
    return " Rateaurant API"

@app.route("/auth/register/<mode>", methods=["POST"])
def register(mode):
    if mode not in ["user", "owner"]:
        return "Invalid mode", 404

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if (
            not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email) 
            or username.strip() == "" 
            or password.strip() == ""
        ):
        return "Malformed Data", 400

    if db.check_exist_global("email", email) is not None:
        return "Email alredy registered", 406

    if mode == "user":
        user = db.create_user(username, email, password)
    else:
        user = db.create_owner(username, email, password)
    if not user:
        return "Email alredy registered", 406

    uri = f"{os.environ.get("DOMAIN")}/verify/{mode}/{encode(os.environ.get("TOKEN"), user['_id'])}"
    html =f"""
<p>Hello! Thank you for signing up to Rateaurant!</p>
<p>To Verify your email address, <a href="{uri}">click this link</a></p>
"""
    send_email(user['email'], html)

    return "Registered", 201

@app.route("/auth/verify/<mode>/<code>")
def verify(mode, code):
    if mode not in ["user", "owner"]:
        return "Invalid mode", 404
    user_id = decode(os.environ.get("TOKEN"), code)
    if not db.check_exist(db.users, "_id", user_id) and not db.check_exist(db.owners, "_id", user_id):
        return "Invalid code", 406
    db.verify_user(mode, user_id)
    return "Verified", 202

@app.route("/auth/login")
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    
    if (
            not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)
            or password.strip() == ""
        ):
        return "Malformed Data", 400
    
    if db.check_exist_global("email", email) is None:
        return "Email not registered", 406
    
    if not db.authenticate_user(email, password):
        return "Invalid Password", 401
    
    # user = db.fetch_user("email", email)
    token = db.gen_token(email)
    return jsonify({"status": "success", "token": token}), 200


if __name__ == "__main__":
    app.run(debug=True)