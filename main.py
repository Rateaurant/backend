from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
from dotenv import load_dotenv

from database import Database
from emails import send_email
from logic import encode, decode

load_dotenv()

app = Flask(__name__)
db = Database()

@app.route("/")
def index():
    return " Rateaurant API"

@app.route("/register/user", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.args.get("email")
    password = request.args.get("password")
    user = db.create_user(username, email, password)
    if not user:
        return "email exists", 406
    uri = f"{os.environ.get("DOMAIN")}/verify/{encode(os.environ.get("TOKEN"), user['_id'])}"
    html =f"""
<p>Hello! Thank you for signing up to Rateaurant!</p>
<p>To Verify your email address, <a href="{uri}">click this link</a></p>
"""
    send_email(user['email'], html)
    return "Registered", 200

if __name__ == "__main__":
    app.run(debug=True)