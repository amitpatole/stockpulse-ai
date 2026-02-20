"""
TickerPulse AI v3.0 - Google OAuth Authentication Routes
OAuth 2.0 login flow: initiate, callback, logout, and current-user info.
"""

import logging

from flask import Blueprint, redirect, url_for, jsonify
from flask_login import login_user, logout_user, current_user

from backend.config import Config
from backend.auth_utils import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# OAuth client is initialised lazily via init_oauth() called from create_app()
_google = None


def init_oauth(app) -> None:
    """Register the Google OAuth client with the Flask app.

    Must be called from ``create_app()`` after the app object is created so
    that authlib can store state in ``app.extensions``.
    """
    global _google
    from authlib.integrations.flask_client import OAuth

    oauth = OAuth(app)
    _google = oauth.register(
        name='google',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


@auth_bp.route('/google')
def google_login():
    """Redirect the browser to Google's OAuth consent screen."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return _google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """Exchange the OAuth authorisation code for a token, upsert the user
    record, create a Flask-Login session, and redirect to the dashboard."""
    try:
        token = _google.authorize_access_token()
        userinfo = token.get('userinfo')
        if userinfo is None:
            userinfo = _google.userinfo()

        google_id = userinfo['sub']
        email = userinfo['email']
        name = userinfo.get('name')

        user = User.upsert(google_id, email, name)
        login_user(user, remember=True)
        logger.info("User authenticated: %s", email)
        return redirect(f"{Config.FRONTEND_URL}/")
    except Exception:
        logger.exception("OAuth callback failed")
        return redirect(f"{Config.FRONTEND_URL}/login?error=auth_failed")


@auth_bp.route('/logout')
def logout():
    """Clear the Flask-Login session and redirect to the login page."""
    logout_user()
    return redirect(f"{Config.FRONTEND_URL}/login")


@auth_bp.route('/me')
def me():
    """Return ``{id, email, name}`` for the authenticated user; 401 otherwise."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
    })
