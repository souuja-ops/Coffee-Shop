import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES


@app.route("/")
def home():
    hiText = "Hi Guys"
    return str(hiText)


@app.route('/drinks', methods=['GET'])
def get_all_drinks():
    try:
        drinks = Drink.query.all()
        if drinks:
            data = [drink.short() for drink in drinks]
        else:
            data = []
    except Exception as e:
        print(e)
        abort(500)
    return jsonify({"success": True, "drinks": data})


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_details(*args, **kwargs):
    try:
        drinks = Drink.query.all()
        drink_long = [drink.long() for drink in drinks]
        return jsonify({
            'success': True,
            'drinks': drink_long
        }), 200
    except:
        abort(400)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def new_drink(jwt):
    try:
        data = request.get_json()
        recipe = data['recipe']
        title = data['title']
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()
        return jsonify({
            "success": True,
            "drinks": drink.long()
        }), 200
    except:
        abort(422, 'error. Failed to save drink to database.')


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink_by_id(*args, **kwargs):
    try:
        id = kwargs['id']
        drink = Drink.query.filter_by(id=id).first()
        if drink is None:
            abort(404)
        data = request.get_json()
        try:
            drink.title = data.get('title')
        except:
            print('error. No title')
        try:
            if json.dumps(data.get('recipe'))!=null:
                drink.recipe = json.dumps(data.get('recipe'))
        except:
            print('error. No recipe')    
        drink.insert()
    except SQLAlchemyError as e:
        print(e)
        abort(400, 'Error. Failed to patch drink.')
    return jsonify({
        'success': True,
        'drinks': drink.long()
    }), 200


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(*args, **kwargs):
    id = kwargs['id']
    drink = Drink.query.filter_by(id=id).first()
    try:
        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        }), 200
    except:
        abort(400, 'failed to delete drink')


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Sorry for the request is incorrect"
    }), 400

@app.errorhandler(401)
def unauthorised(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Sorry for the request is unauthorised"
    }), 401

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
