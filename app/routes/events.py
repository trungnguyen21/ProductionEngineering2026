from flask import Blueprint, jsonify
from app.models.event import Event
from app.services.services import serialize_event

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('', methods=['GET'])
def list_events():
    """
    List all Events
    ---
    responses:
      200:
        description: A list of Event objects
    """
    Event.create_table(safe=True)
    events = Event.select()
    return jsonify([serialize_event(e) for e in events]), 200
