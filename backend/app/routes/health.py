from flask import Blueprint, jsonify
from app import cache as redis_cache

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status':  'healthy',
        'service': 'MargaMetis Route Optimizer',
        'cache':   redis_cache.stats(),
    }), 200


@health_bp.route('/cache/stats', methods=['GET'])
def cache_stats():
    return jsonify(redis_cache.stats()), 200
