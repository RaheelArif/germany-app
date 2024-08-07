# app.py

import os
from app import create_app

app = create_app()

app.secret_key = '1356674150b388010f47dbe1eb04370ddb2402ada0618484'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
