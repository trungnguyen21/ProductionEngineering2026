import string
import secrets
import datetime
from flask import Blueprint, request, jsonify
from app.models.url import Url
from app.models.user import User
from app.services.services import serialize_url

urls_bp = Blueprint('urls', __name__, url_prefix='/urls')

def generate_short_code(length=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@urls_bp.route('', methods=['POST'])
def create_url():
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
    Url.create_table(safe=True)
    
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
        
    # Generate unique short code
    while True:
        short_code = generate_short_code()
        if not Url.select().where(Url.short_code == short_code).exists():
            break
            
    try:
        try:
            user = User.get(User.id == user_id)
        except User.DoesNotExist:
            return jsonify({"error": f"User {user_id} not found"}), 404
            
        url_entry = Url.create(
            user=user,
            short_code=short_code,
            original_url=original_url,
            title=title,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        return jsonify(serialize_url(url_entry)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@urls_bp.route('', methods=['GET'])
def list_urls():
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
    Url.create_table(safe=True)
    user_id = request.args.get('user_id', type=int)
    
    query = Url.select()
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
        
    return jsonify([serialize_url(url) for url in query])

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
    Url.create_table(safe=True)
    try:
        url = Url.get(Url.id == url_id)
        return jsonify(serialize_url(url)), 200
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

@urls_bp.route('/<int:url_id>', methods=['PUT'])
def update_url(url_id):
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
    Url.create_table(safe=True)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    try:
        url = Url.get(Url.id == url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404
        
    if "title" in data:
        url.title = data["title"]
    if "is_active" in data:
        url.is_active = data["is_active"]
        
    url.updated_at = datetime.datetime.now()
    url.save()
    
    return jsonify(serialize_url(url)), 200
