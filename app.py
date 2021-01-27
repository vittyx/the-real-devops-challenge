from os import environ

from bson import json_util
from bson.objectid import ObjectId
from flask import Flask, jsonify, Response
from flask_pymongo import PyMongo

from src.mongoflask  import MongoJSONEncoder, ObjectIdConverter, find_restaurants

app = Flask(__name__)
app.config["MONGO_URI"] = environ.get("MONGO_URI")
#app.config['MONGO_HOST'] = 'localhost'
#app.config['MONGO_PORT'] = '27017'
#app.config['MONGO_DBNAME'] = 'prueba'
#app.config['MONGO_USERNAME'] = 'root'
#app.config['MONGO_PASSWORD'] = 'example'
#app.config['MONGO_AUTH_SOURCE'] = 'admin' 
app.json_encoder = MongoJSONEncoder
app.url_map.converters["objectid"] = ObjectIdConverter
mongo = PyMongo(app)


@app.route("/api/v1/restaurant")
def restaurants():
    restaurants = find_restaurants(mongo)
    return jsonify(restaurants)


@app.route("/api/v1/restaurant/<id>")
def restaurant(id):
    restaurants = find_restaurants(mongo, id)
    if restaurants is not None:
      return jsonify(restaurants)
    return Response("{'a':'b'}", status=204, mimetype='application/json')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
