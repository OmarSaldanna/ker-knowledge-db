import os
import json
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import request, jsonify

#########################################################################
######################### Globals #######################################
#########################################################################

# Configuración desde variables de entorno
API_KEYS_FILE = os.getenv('API_KEYS_FILE', '.apikeys')
API_KEY_LENGTH = int(os.getenv('API_KEY_LENGTH', 64))
ADMINS_FILE = os.getenv('ADMINS_FILE', '.admins')
API_LOG_FILE = os.getenv('API_LOG_FILE', 'log.txt')


#########################################################################
######################### Admins ########################################
#########################################################################

def get_admin_emails():
    """Carga la lista de emails de administradores desde el archivo"""
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r') as f:
                emails = [line.strip() for line in f.readlines() if line.strip()]
                return emails
        else:
            print(f"Warning: Admin emails file '{ADMINS_FILE}' not found")
            return []
    except Exception as e:
        print(f"Error loading admin emails: {e}")
        return []

#########################################################################
######################### API Keys ######################################
#########################################################################

class APIKeyManager:
    def __init__(self, keys_file):
        self.keys_file = keys_file
        self.admin_emails = get_admin_emails()
        self.load_keys()
    
    def load_keys(self):
        """Carga las API keys desde el archivo"""
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.keys = json.loads(content)
                    else:
                        self.keys = {}
            else:
                self.keys = {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in API keys file: {e}")
            self.keys = {}
        except Exception as e:
            print(f"Error loading API keys: {e}")
            self.keys = {}
    
    def save_keys(self):
        """Guarda las API keys en el archivo"""
        try:
            with open(self.keys_file, 'w') as f:
                json.dump(self.keys, f, indent=2)
        except Exception as e:
            print(f"Error saving API keys: {e}")
            raise Exception(f"Failed to save API keys: {e}")
    
    def generate_api_key(self, email):
        """Genera una nueva API key para un email"""
        if not email or not email.strip():
            raise ValueError("Email is required and cannot be empty")
        
        email = email.strip().lower()
        
        # Validar formato básico de email
        if '@' not in email or '.' not in email.split('@')[1]:
            raise ValueError("Invalid email format")
        
        # Generar una clave aleatoria segura
        raw_key = secrets.token_urlsafe(API_KEY_LENGTH)
        
        # Hash de la clave para almacenamiento seguro
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Verificar si ya existe una key activa para este email
        for key_data in self.keys.values():
            if key_data.get('email') == email and key_data.get('active', False):
                raise ValueError(f"Active API key already exists for email: {email}")
        
        # Guardar el hash y la información del usuario
        self.keys[key_hash] = {
            'email': email,
            'created_at': datetime.now().isoformat(),
            'active': True,
            'last_used': None
        }
        
        self.save_keys()
        return raw_key
    
    def validate_api_key(self, api_key):
        """Valida una API key y retorna el email del usuario"""
        if not api_key or not api_key.strip():
            return None
        
        try:
            key_hash = hashlib.sha256(api_key.strip().encode()).hexdigest()
            
            if key_hash in self.keys and self.keys[key_hash].get('active', False):
                # Actualizar último uso
                self.keys[key_hash]['last_used'] = datetime.now().isoformat()
                try:
                    self.save_keys()
                except:
                    pass  # No fallar la validación si no se puede guardar el último uso
                
                return self.keys[key_hash]['email']
            
            return None
        except Exception as e:
            print(f"Error validating API key: {e}")
            return None
    
    def revoke_api_key(self, api_key):
        """Revoca una API key"""
        if not api_key:
            return False
        
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if key_hash in self.keys:
                self.keys[key_hash]['active'] = False
                self.keys[key_hash]['revoked_at'] = datetime.now().isoformat()
                self.save_keys()
                return True
            return False
        except Exception as e:
            print(f"Error revoking API key: {e}")
            return False
    
    def list_api_keys(self, admin_email):
        """Lista todas las API keys (solo para admins)"""
        if admin_email not in self.admin_emails:
            raise PermissionError("Admin privileges required")
        
        keys_info = []
        for key_hash, key_data in self.keys.items():
            keys_info.append({
                'email': key_data.get('email'),
                'created_at': key_data.get('created_at'),
                'active': key_data.get('active', False),
                'last_used': key_data.get('last_used'),
                'key_hash': key_hash[:8] + '...'  # Solo mostrar parte del hash
            })
        
        return keys_info

# Inicializar el gestor de API key
api_key_manager = APIKeyManager(API_KEYS_FILE)

#########################################################################
######################### Logs ##########################################
#########################################################################

def log_operation(email, operation, input_data, output_data):
    """Registra una operación en el log"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sanitizar datos para evitar inyección de comandos
        email_clean = email.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        operation_clean = operation.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        input_clean = str(input_data).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        output_clean = str(output_data).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        
        log_entry = f'"{email_clean}" | "{operation_clean}" | "{input_clean}" > "{output_clean}" ? "{timestamp}"\n'
        
        # Escribir directamente al archivo en lugar de usar os.system
        with open(API_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"Error logging operation: {e}")

#########################################################################
######################### Utils for API #################################
#########################################################################

def require_api_key(f):
    """Decorador para requerir autenticación con API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar header de API key
        api_key = request.headers.get('X-SECRET-KER')
        
        if not api_key:
            return jsonify({
                'error': 'Authentication required',
                'details': 'API key required in X-SECRET-KER header'
            }), 401
        
        # Validar API key
        email = api_key_manager.validate_api_key(api_key)
        if not email:
            return jsonify({
                'error': 'Invalid authentication',
                'details': 'Invalid or expired API key'
            }), 401
        
        # Agregar el email al contexto de la request
        request.user_email = email
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar que el usuario esté autenticado
        if not hasattr(request, 'user_email'):
            return jsonify({
                'error': 'Authentication required',
                'details': 'Must be authenticated to access admin endpoints'
            }), 401
        
        # Recargar emails de admin por si han cambiado
        admin_emails = get_admin_emails()
        
        # Verificar permisos de admin
        if request.user_email not in admin_emails:
            return jsonify({
                'error': 'Insufficient privileges',
                'details': 'Administrator privileges required for this operation'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def is_admin(email):
    """Verifica si un email tiene permisos de administrador"""
    admin_emails = get_admin_emails()
    return email in admin_emails