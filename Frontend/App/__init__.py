from flask import Flask

config = {"CACHE_TYPE": "filesystem", "CACHE_DIR": "cache-directory"}


def init_app():
    """Construct core Flask application with embedded Dash app."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(config)

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes

        # Import Dash application
        from .plotlydash.dashboard import init_dashboard

        app = init_dashboard(app)

        return app
