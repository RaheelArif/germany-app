swagger_template = {
  "swagger": "2.0",
  "info": {
    "title": "Flask API",
    "description": "Swagger documentation for Flask API",
    "version": "1.0.0"
  },
  "basePath": "/api",
  "schemes": [
    "http"
  ],

  "paths": {
    "/germany_section/home": {
      "get": {
        "tags": ["germany_section"],
        "summary": "Home page",
        "responses": {
          "200": {
            "description": "Home Page",
            "schema": {
              "type": "object",
              "properties": {
                "message": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "/germany_section/pdf_upload": {
      "post": {
        "tags": ["germany_section"],
        "summary": "Upload a PDF file",
        "consumes": ["multipart/form-data"],
        "parameters": [
          {
            "name": "file",
            "in": "formData",
            "description": "The file to upload",
            "required": True,
            "type": "file"
          }
        ],
        "responses": {
          "200": {
            "description": "File has been uploaded",
            "schema": {
              "type": "object",
              "properties": {
                "message": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Invalid input",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/germany_section/download/{filename}": {
            "get": {
                "tags": ["germany_section"],
                "summary": "Download a file from the server",
                "parameters": [
                    {
                        "name": "filename",
                        "in": "path",
                        "type": "string",
                        "required": True,
                        "description": "Name of the file to download"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "File downloaded successfully",
                        "schema": {
                            "type": "string",
                            "format": "binary"
                        }
                    },
                    "404": {
                        "description": "File not found"
                    }
                }
            }
        }
  },
  "definitions": {
    "Example": {
      "type": "object",
      "properties": {
        "id": {
          "type": "integer"
        },
        "name": {
          "type": "string"
        }
      }
    }
  }
}

def add_swagger(app):
    from flask_swagger_ui import get_swaggerui_blueprint

    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json' 

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Revanoo API"
        }
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
