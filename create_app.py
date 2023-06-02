from flask import Flask
from flask_pymongo import PyMongo

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
    app.secret_key = 'dgusoftwareengineeringverysecretkey'
    mongo.init_app(app)

    return app
