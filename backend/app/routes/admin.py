from flask import Blueprint, jsonify, session
from sqlalchemy import func, extract
from app.models import db, SearchHistory

admin_bp = Blueprint('admin', __name__)


def require_admin():
    return session.get('role') == 'admin'


@admin_bp.route('/stats', methods=['GET'])
def stats():
    if not require_admin():
        return jsonify({'error': 'Forbidden'}), 403

    total_searches = db.session.query(func.count(SearchHistory.id)).scalar() or 0
    unique_users   = db.session.query(func.count(func.distinct(SearchHistory.user_id))).scalar() or 0

    top_origins = [
        {'origin': o, 'count': c}
        for o, c in (
            db.session.query(SearchHistory.origin, func.count(SearchHistory.id).label('count'))
            .group_by(SearchHistory.origin)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(10).all()
        )
    ]

    top_destinations = [
        {'destination': d, 'count': c}
        for d, c in (
            db.session.query(SearchHistory.destination, func.count(SearchHistory.id).label('count'))
            .group_by(SearchHistory.destination)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(10).all()
        )
    ]

    top_route_types = [
        {'route_type': rt, 'count': c}
        for rt, c in (
            db.session.query(SearchHistory.route_type, func.count(SearchHistory.id).label('count'))
            .group_by(SearchHistory.route_type)
            .order_by(func.count(SearchHistory.id).desc())
            .all()
        )
    ]

    top_pairs = [
        {'origin': o, 'destination': d, 'count': c}
        for o, d, c in (
            db.session.query(
                SearchHistory.origin, SearchHistory.destination,
                func.count(SearchHistory.id).label('count')
            )
            .group_by(SearchHistory.origin, SearchHistory.destination)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(10).all()
        )
    ]

    hourly_distribution = [
        {'hour': int(h or 0), 'count': int(c or 0)}
        for h, c in (
            db.session.query(
                extract('hour', SearchHistory.created_at).label('hour'),
                func.count(SearchHistory.id).label('count')
            )
            .group_by(extract('hour', SearchHistory.created_at))
            .order_by(extract('hour', SearchHistory.created_at))
            .all()
        )
    ]

    return jsonify({
        'success': True,
        'totals': {
            'searches':     int(total_searches),
            'unique_users': int(unique_users),
        },
        'top_origins':          top_origins,
        'top_destinations':     top_destinations,
        'top_route_types':      top_route_types,
        'top_pairs':            top_pairs,
        'hourly_distribution':  hourly_distribution,
    }), 200
