import peewee

from flask import Blueprint, request, jsonify

from app.services.users_services import (
    bulk_import_users,
    get_users,
    get_user_by_id,
    create_user,
    update_user,
    delete_user,
    serialize_user,
)
from app.services.services import limiter

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/bulk', methods=['POST'])
@limiter.limit("5/minute")
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
        count = bulk_import_users(file.stream)
        return jsonify({"imported": count}), 201

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
        user = get_user_by_id(user_id)
        return jsonify(serialize_user(user)), 200
    except Exception:
        return jsonify({"error": "User not found"}), 404

@users_bp.route('', methods=['POST'])
@limiter.limit("10/minute")
def create_user_route():
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
        user = create_user(username=username, email=email)
        return jsonify(serialize_user(user)), 201
    except peewee.IntegrityError:
        return jsonify({"error": "username or email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user_route(user_id):
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

    username = data.get("username")
    email = data.get("email")

    if username is not None and not isinstance(username, str):
        return jsonify({"error": "username must be a string"}), 400
    if email is not None and not isinstance(email, str):
        return jsonify({"error": "email must be a string"}), 400

    try:
        user = update_user(user_id, username=username, email=email)
        return jsonify(serialize_user(user)), 200
    except peewee.PeeweeException as e:
        if isinstance(e, peewee.IntegrityError):
            return jsonify({"error": "username or email already exists"}), 409
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    """
    Delete a user by ID
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User deleted
      404:
        description: User not found
    """
    try:
        user = delete_user(user_id)
        return jsonify(serialize_user(user)), 200
    except Exception:
        return jsonify({"error": "User not found"}), 404
