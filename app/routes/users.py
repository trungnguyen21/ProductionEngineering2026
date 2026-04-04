import csv
import io
import peewee
from datetime import datetime

from flask import Blueprint, request, jsonify

from app.models.user import User
from app.database import db
from app.services.user_services import peewee_chunked, get_users, serialize_user

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/bulk', methods=['POST'])
def upload_users():
    """
    Upload users via CSV file
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: CSV file containing user data
    responses:
      201:
        description: Bulk upload successful
      400:
        description: Invalid file format
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        User.create_table(safe=True)
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        users_to_insert = []
        for row in csv_input:
            try:
                created_at = datetime.strptime(row['created_at'], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                created_at = datetime.now()
            
            users_to_insert.append({
                'id': int(row['id']),
                'username': row['username'],
                'email': row['email'],
                'created_at': created_at
            })
            
        with db.atomic():
            for batch in peewee_chunked(users_to_insert, 100):
                User.insert_many(batch).on_conflict_ignore().execute()
            
        return jsonify({"imported": len(users_to_insert)}), 201

    return jsonify({"error": "Invalid file format. Please upload a CSV"}), 400

@users_bp.route('', methods=['GET'])
def list_users():
    """
    List all users
    ---
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: per_page
        in: query
        type: integer
        required: false
        default: 10
    responses:
      200:
        description: A list of users
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        users = get_users(page, per_page)
        return jsonify({"users": users})
    except Exception as e:
        print("Failed to get users")
        return jsonify({"error": "Failed to get users"}), 400



@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a specific user by ID
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The ID of the user
    responses:
      200:
        description: The user object
      404:
        description: User not found
    """
    try:
        user = User.get(User.id == user_id)
        return jsonify(serialize_user(user)), 200
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404

@users_bp.route('', methods=['POST'])
def create_user():
    """
    Create a new user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
    responses:
      201:
        description: User created
      400:
        description: Invalid payload
      409:
        description: Username or email already exists
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
    
    username = data.get("username")
    email = data.get("email")
    
    if not isinstance(username, str) or not isinstance(email, str):
        return jsonify({"error": "username and email must be strings"}), 400
        
    try:
        user = User.create(username=username, email=email, created_at=datetime.now())
        return jsonify(serialize_user(user)), 201
    except peewee.IntegrityError:
        return jsonify({"error": "username or email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update an existing user
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
    responses:
      200:
        description: User updated
      400:
        description: Invalid payload
      404:
        description: User not found
      409:
        description: Username or email already exists
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    try:
        user = User.get(User.id == user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404
        
    username = data.get("username")
    email = data.get("email")
    
    if username is not None:
        if not isinstance(username, str):
            return jsonify({"error": "username must be a string"}), 400
        user.username = username
        
    if email is not None:
        if not isinstance(email, str):
            return jsonify({"error": "email must be a string"}), 400
        user.email = email
        
    try:
        user.save()
        return jsonify(serialize_user(user)), 200
    except peewee.IntegrityError:
        return jsonify({"error": "username or email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 400


