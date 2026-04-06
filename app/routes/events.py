from flask import Blueprint, request, jsonify

from app.services.events_services import list_events, create_event, serialize_event
from app.services.services import limiter

events_bp = Blueprint('events', __name__, url_prefix='/events')


@events_bp.route('', methods=['GET'])
def list_events_route():
    """
    List all Events
    ---
    responses:
      200:
        description: A list of Event objects
    """
    payload = request.get_json(silent=True) or {}
    url_id = request.args.get('url_id', type=int) if 'url_id' in request.args else payload.get('url_id')
    event_type = request.args.get('event_type') if 'event_type' in request.args else payload.get('event_type')
    
    if url_id is not None:
        try:
            url_id = int(url_id)
        except ValueError:
            pass

    events = list_events(url_id=url_id, event_type=event_type)
    return jsonify([serialize_event(e) for e in events]), 200


@events_bp.route('', methods=['POST'])
@limiter.limit("30/minute")
def create_event_route():
    """
    Create a new Event
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            url_id:
              type: integer
            user_id:
              type: integer
            event_type:
              type: string
            details:
              type: object
    responses:
      201:
        description: Event created
      400:
        description: Invalid payload
      404:
        description: URL or User not found
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    url_id = data.get("url_id")
    event_type = data.get("event_type")
    user_id = data.get("user_id")
    details = data.get("details")

    if url_id is None:
        return jsonify({"error": "url_id is required"}), 400
    if not event_type:
        return jsonify({"error": "event_type is required"}), 400
        
    if details is not None and not isinstance(details, dict):
        return jsonify({"error": "details must be an object"}), 400

    try:
        event = create_event(url_id=url_id, event_type=event_type, user_id=user_id, details=details)
        return jsonify(serialize_event(event)), 201
    except Exception as e:
        err = str(e)
        if "DoesNotExist" in err or "does not exist" in err.lower():
            return jsonify({"error": err}), 404
        return jsonify({"error": err}), 400
