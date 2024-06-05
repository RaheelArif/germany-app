from flask import Flask
import os

def create_app():
    app = Flask(__name__)

    # Ensure the necessary directories exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    with app.app_context():
        # Import and register the blueprints
        from .routes import main
        app.register_blueprint(main)

    return app
