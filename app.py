# app.py

import os
from app import create_app
from flask import jsonify
from flask_cors import CORS


from swagger import add_swagger, swagger_template

app = create_app()

CORS(app)

@app.errorhandler(400)
def custom_400(error):
    response = jsonify({
        "error": "Bad Request",
        "message": str(error)
    })
    response.status_code = 400
    return response


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


app.secret_key = '1356674150b388010f47dbe1eb04370ddb2402ada0618484'


add_swagger(app)

@app.route('/static/swagger.json')
def swagger_json():
    return jsonify(swagger_template)


print("App is running now of port ", int(os.environ.get('PORT', 5001)))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)


