from flask import Blueprint, jsonify

from app.services.events_services import list_events, serialize_event

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
    events = list_events()
    return jsonify([serialize_event(e) for e in events]), 200
