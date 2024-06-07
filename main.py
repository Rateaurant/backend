from flask import Flask, render_template, request, redirect, url_for
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return " Rateaurant API"

if __name__ == "__main__":
    app.run(debug=True)