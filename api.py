import os
from datetime import datetime
from flask import Flask, request, jsonify
# functions and controllers
from controllers.auth import require_api_key, require_admin, api_key_manager
from controllers.functions import (
    chat_handler, 
    manage_collection_handler, 
    get_collections_handler,
    get_collection_info_handler,
    update_collection_handler,
    get_llms_handler, 
    get_embeddings_handler, 
    get_settings_handler, 
    generate_api_key_handler
)

#########################################################################
######################### Init and Functions ############################
#########################################################################

app = Flask(__name__)

# environment and api variables
API_KEY_HOST = os.getenv('API_KEY_HOST', '0.0.0.0')
API_KEY_PORT = int(os.getenv('API_KEY_PORT', 5000))
API_LOG_FILE = os.getenv('API_LOG_FILE', 'log.txt')

# check that the request comes in json
def validate_json_request():
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    # if it's json
    try:
        # get the data
        data = request.get_json()
        if data is None:
            return {'error': 'Invalid JSON data'}, 400
        return data, None
    # if something is wrong
    except Exception as e:
        return {'error': f'JSON parsing error: {str(e)}'}, 400

# function to handle errors
def handle_request_error(func):
    # decorator to handle errors
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': f'Validation error: {str(e)}'}), 400
        except PermissionError as e:
            return jsonify({'error': f'Permission denied: {str(e)}'}), 403
        except FileNotFoundError as e:
            return jsonify({'error': f'Resource not found: {str(e)}'}), 404
        except Exception as e:
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
    wrapper.__name__ = func.__name__
    return wrapper

#########################################################################
################################# Routes ################################
#########################################################################

################################# chat and embeddings ###################

@app.route('/chat', methods=['POST'])
@require_api_key
@handle_request_error
def chat():
    """Endpoint para chat con colección"""
    data, error = validate_json_request()
    if error:
        return jsonify(error[0]), error[1]
    
    return chat_handler(data, request.user_email)


## falta embeddings

################################# collection handling ###################

@app.route('/collection', methods=['POST'])
@require_api_key
@handle_request_error
def create_collection():
    """Endpoint para crear y agregar a colección"""
    data, error = validate_json_request()
    if error:
        return jsonify(error[0]), error[1]
    
    return manage_collection_handler(data, request.user_email)

@app.route('/collection', methods=['GET'])
@handle_request_error
def get_collections():
    """Endpoint para listar colecciones o obtener info de una colección específica"""
    collection_name = request.args.get('collection')
    
    if collection_name:
        # Obtener información de una colección específica
        return get_collection_info_handler(collection_name)
    else:
        # Listar todas las colecciones
        return get_collections_handler()

@app.route('/collection', methods=['PUT'])
@require_api_key
@handle_request_error
def update_collection():
    """Endpoint para actualizar una colección"""
    data, error = validate_json_request()
    if error:
        return jsonify(error[0]), error[1]
    
    return update_collection_handler(data, request.user_email)

################################# Get models and settings ###############

@app.route('/llms', methods=['GET'])
@handle_request_error
def get_llms():
    """Endpoint para obtener proveedores de LLM"""
    return get_llms_handler()

@app.route('/embeddings', methods=['GET'])
@handle_request_error
def get_embeddings():
    """Endpoint para obtener proveedores de embeddings"""
    return get_embeddings_handler()

@app.route('/settings', methods=['GET'])
@handle_request_error
def get_settings():
    """Endpoint para obtener configuración de colección"""
    collection = request.args.get('collection')
    
    if not collection:
        return jsonify({'error': 'collection parameter is required'}), 400
    
    return get_settings_handler(collection)

################################# API Keys ##############################

@app.route('/apk', methods=['POST'])
@require_api_key
@require_admin
@handle_request_error
def generate_api_key():
    """Endpoint para generar nuevas API keys (solo admins)"""
    data, error = validate_json_request()
    if error:
        return jsonify(error[0]), error[1]
    
    return generate_api_key_handler(data, request.user_email)

################################# Monitor ###############################

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

#########################################################################
################################# Errors ################################
#########################################################################

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'details': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized access', 'details': 'Invalid or missing API key'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden', 'details': 'Insufficient privileges'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'details': 'The requested resource does not exist'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed', 'details': 'The HTTP method is not supported for this endpoint'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'details': 'An unexpected error occurred'}), 500

#########################################################################
################################# API Running ###########################
#########################################################################

if __name__ == '__main__':
    # Crear archivos iniciales si no existen
    if not os.path.exists(API_LOG_FILE):
        try:
            with open(API_LOG_FILE, 'w') as f:
                f.write(f"API Log initialized at {datetime.now().isoformat()}\n")
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
    
    # Crear directorio controllers si no existe
    if not os.path.exists('controllers'):
        os.makedirs('controllers')
    
    # Generar una API key inicial para el primer admin si no existe archivo de keys
    try:
        if not os.path.exists(os.getenv('API_KEYS_FILE', '.apikeys')):
            from controllers.auth import get_admin_emails
            admin_emails = get_admin_emails()
            if admin_emails:
                initial_key = api_key_manager.generate_api_key(admin_emails[0])
                print(f"Initial admin API key generated: {initial_key}")
                print(f"Admin email: {admin_emails[0]}")
            else:
                print("Warning: No admin emails found. Please create .admins file with admin emails.")
    except Exception as e:
        print(f"Warning: Could not generate initial API key: {e}")
    
    print(f"Starting API server on {API_KEY_HOST}:{API_KEY_PORT}")
    app.run(debug=True, host=API_KEY_HOST, port=API_KEY_PORT)