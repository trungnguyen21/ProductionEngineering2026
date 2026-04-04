from flask import Blueprint, request, jsonify

from app.models.user import User
from app.services.urls_services import (
    serialize_url,
    create_url,
    list_urls,
    get_url_by_id,
    update_url,
)

urls_bp = Blueprint('urls', __name__, url_prefix='/urls')

@urls_bp.route('', methods=['POST'])
def create_url_route():
    """
    Create a new URL
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
            original_url:
              type: string
            title:
              type: string
    responses:
      201:
        description: URL created
      400:
        description: Invalid constraints or payload
      404:
        description: User not found
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    user_id = data.get("user_id")
    original_url = data.get("original_url")
    title = data.get("title")
    
    if not original_url:
        return jsonify({"error": "original_url is required"}), 400
        
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
        
    try:
        url_entry = create_url(user_id=user_id, original_url=original_url, title=title)
        return jsonify(serialize_url(url_entry)), 201
    except User.DoesNotExist:
        return jsonify({"error": f"User {user_id} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@urls_bp.route('', methods=['GET'])
def list_urls_route():
    """
    List all URLs
    ---
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
    responses:
      200:
        description: A list of URL objects
    """
    user_id = request.args.get('user_id', type=int)
    urls = list_urls(user_id=user_id)
    return jsonify([serialize_url(url) for url in urls])

@urls_bp.route('/<int:url_id>', methods=['GET'])
def get_url(url_id):
    """
    Get a specific URL by ID
    ---
    parameters:
      - name: url_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: URL object
      404:
        description: URL not found
    """
    try:
        url = get_url_by_id(url_id)
        return jsonify(serialize_url(url)), 200
    except Exception:
        return jsonify({"error": "URL not found"}), 404

@urls_bp.route('/<int:url_id>', methods=['PUT'])
def update_url_route(url_id):
    """
    Update URL details
    ---
    parameters:
      - name: url_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            is_active:
              type: boolean
    responses:
      200:
        description: URL updated
      400:
        description: Invalid payload
      404:
        description: URL not found
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    try:
        url = update_url(
            url_id,
            title=data.get("title"),
            is_active=data.get("is_active"),
        )
        return jsonify(serialize_url(url)), 200
    except Exception:
        return jsonify({"error": "URL not found"}), 404
