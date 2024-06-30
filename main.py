from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
from dotenv import load_dotenv
from flask_cors import CORS 

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

@app.route("/register/<mode>", methods=["POST"])
def register(mode):
    if mode not in ["user", "owner"]:
        return "Invalid mode", 404
    
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if mode == "user":
        user = db.create_user(username, email, password)
    else:
        user = db.create_owner(username, email, password)
    if not user:
        return "email exists", 406

    uri = f"{os.environ.get("DOMAIN")}/verify/{mode}/{encode(os.environ.get("TOKEN"), user['_id'])}"
    html =f"""
<p>Hello! Thank you for signing up to Rateaurant!</p>
<p>To Verify your email address, <a href="{uri}">click this link</a></p>
"""
    send_email(user['email'], html)

    return "Registered", 201

@app.route("/verify/<mode>/<code>")
def verify(mode, code):
    if mode not in ["user", "owner"]:
        return "Invalid mode", 404
    user_id = decode(os.environ.get("TOKEN"), code)
    if not db.check_exist(db.users, "_id", user_id) and not db.check_exist(db.owners, "_id", user_id):
        return "Invalid code", 406
    db.verify_user(mode, user_id)
    return "Verified", 202

if __name__ == "__main__":
    app.run(debug=True)