import os
from app import create_app
from flask import jsonify
from flask_cors import CORS
from swagger import add_swagger, swagger_template
from app.germany_app import germany_section as germany_blueprint
from app.routes import main as main_blueprint

app = create_app()
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "https://germany-app.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Register both blueprints
app.register_blueprint(main_blueprint, name='main_routes')  # Give unique name
app.register_blueprint(germany_blueprint, name='germany_routes')

# Error handler for 400 Bad Request
@app.errorhandler(400)
def custom_400(error):
    response = jsonify({
        "error": "Bad Request",
        "message": str(error)
    })
    response.status_code = 400
    return response

# Health check endpoint for Vercel
@app.route('/')
def home():
    return jsonify({
        "status": "healthy",
        "message": "API is running"
    })

# Routes listing endpoint
@app.route('/routes')
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        url = urllib.parse.unquote(f"{rule}")
        line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {url}")
        output.append(line)
    
    return "<pre>" + "\n".join(sorted(output)) + "</pre>"

# Swagger configuration
app.secret_key = '1356674150b388010f47dbe1eb04370ddb2402ada0618484'
add_swagger(app)

@app.route('/static/swagger.json')
def swagger_json():
    return jsonify(swagger_template)

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"App is running now on port {port}")
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=True
    )