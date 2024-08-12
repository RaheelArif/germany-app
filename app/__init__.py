from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    with app.app_context():
        # Ensure the necessary directories exist
        uploads_dir = os.path.join(app.root_path, 'uploads')
        downloads_dir = os.path.join(app.root_path, 'downloads')

        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        # Import and register the blueprints


        from .routes import main
        app.register_blueprint(main)


        from .germany_app import germany_section
        app.register_blueprint(germany_section)
        
        from .feedback_app import feedback
        app.register_blueprint(feedback)

    return app