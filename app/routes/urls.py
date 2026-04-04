from flask import Blueprint, request, jsonify, redirect

from app.models.user import User
from app.services.urls_services import (
    serialize_url,
    create_url,
    list_urls,
    get_url_by_id,
    get_url_by_short_code,
    update_url,
    delete_url,
)
from app.services.events_services import create_event

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
      - name: is_active
        in: query
        type: boolean
        required: false
    responses:
      200:
        description: A list of URL objects
    """
    user_id = request.args.get('user_id', type=int)
    is_active_str = request.args.get('is_active')
    is_active = None
    if is_active_str is not None:
        is_active = is_active_str.lower() in ('true', '1', 'yes')
    urls = list_urls(user_id=user_id, is_active=is_active)
    return jsonify([serialize_url(url) for url in urls])


@urls_bp.route('/<string:short_code>/redirect', methods=['GET'])
def redirect_short_code(short_code):
    """
    Redirect to the original URL for a given short code
    ---
    parameters:
      - name: short_code
        in: path
        type: string
        required: true
    responses:
      301:
        description: Redirect to original URL
      404:
        description: Short code not found or URL inactive
    """
    try:
        url = get_url_by_short_code(short_code)
    except Exception:
        return jsonify({"error": "Short code not found"}), 404

    if not url.is_active:
        return jsonify({"error": "URL is not active"}), 410

    # Hidden bonus: auto-create a "redirect" event for observability
    try:
        create_event(url_id=url.id, event_type="redirect", details={"referrer": request.referrer})
    except Exception:
        pass  # Don't fail the redirect if event creation fails

    return redirect(url.original_url, code=302)


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


@urls_bp.route('/<int:url_id>', methods=['DELETE'])
def delete_url_route(url_id):
    """
    Delete a URL by ID
    ---
    parameters:
      - name: url_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: URL deleted
      404:
        description: URL not found
    """
    try:
        url = delete_url(url_id)
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
