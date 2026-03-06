from typing import Any
import logging
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import Row

from tickerpulse.models.user import User
from tickerpulse.config import get_config

db = SQLAlchemy()
onboarding_bp = Blueprint('onboarding', __name__)

logger = logging.getLogger(__name__)

@onboarding_bp.route('/start-tour', methods=['POST'])
async def start_tour() -> Any:
    """
    Start the onboarding tour for a user.
    """
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    async with db.session.begin_nested() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Mark the user as having started the onboarding tour
        user.onboarding_tour_started = True
        await session.commit()

    return jsonify({"message": "Onboarding tour started"}), 200

@onboarding_bp.route('/get-tour-status', methods=['GET'])
async def get_tour_status() -> Any:
    """
    Get the status of the onboarding tour for a user.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    async with db.session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"onboarding_tour_started": user.onboarding_tour_started}), 200