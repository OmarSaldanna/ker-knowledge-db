import os
from flask import jsonify
from .auth import api_key_manager, log_operation, is_admin

#########################################################################
######################### Validation ####################################
#########################################################################

def validate_required_fields(data, required_fields):
    """Valida que los campos requeridos estén presentes en los datos"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

#########################################################################
######################### Chat ##########################################
#########################################################################

def chat_handler(data, user_email):
    """Handler para el endpoint de chat"""
    try:
        # Validar campos requeridos
        validate_required_fields(data, ['collection', 'prompt'])
        
        collection = data.get('collection').strip()
        prompt = data.get('prompt').strip()
        only_embeddings = data.get('onlyembeddings', False)
        
        # Validaciones adicionales
        if len(prompt) < 3:
            raise ValueError("Prompt must be at least 3 characters long")
        
        if len(prompt) > 10000:
            raise ValueError("Prompt is too long (maximum 10000 characters)")
        
        # Log de la operación
        input_data = f"collection: {collection}, prompt_length: {len(prompt)}, only_embeddings: {only_embeddings}"
        
        # TODO: Aquí va la lógica del chat con la colección
        # Integrar el código necesario para procesar el chat
        
        # Por ahora retornamos una respuesta de ejemplo
        answer = f"Chat response for collection '{collection}' with prompt of {len(prompt)} characters"
        if only_embeddings:
            answer += " (embeddings only)"
        
        log_operation(user_email, "CHAT", input_data, answer[:100])
        
        return jsonify({
            'success': True,
            'answer': answer,
            'collection': collection,
            'only_embeddings': only_embeddings
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Chat processing failed: {str(e)}'}), 500

def manage_collection_handler(data, user_email):
    """Handler para crear y agregar elementos a una colección"""
    try:
        # Validar campos requeridos
        validate_required_fields(data, ['collection'])
        
        collection = data.get('collection').strip()
        items = data.get('items', [])
        
        # Validaciones adicionales
        if not collection.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Collection name can only contain letters, numbers, hyphens and underscores")
        
        if len(collection) < 2 or len(collection) > 50:
            raise ValueError("Collection name must be between 2 and 50 characters")
        
        # Validar tipos de archivo permitidos
        allowed_types = ['pdf', 'md', 'pptx', 'txt', 'docx']
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i+1} must be an object")
            
            item_type = item.get('type', '').lower()
            if item_type not in allowed_types:
                raise ValueError(f"Invalid file type '{item_type}' in item {i+1}. Allowed: {', '.join(allowed_types)}")
            
            # Validar que tenga contenido o URL
            if not item.get('content') and not item.get('url') and not item.get('file_path'):
                raise ValueError(f"Item {i+1} must have content, url, or file_path")
        
        # Log de la operación
        input_data = f"collection: {collection}, items_count: {len(items)}"
        
        # TODO: Aquí va la lógica para procesar los archivos y crear/actualizar la colección
        # Integrar el código necesario para:
        # 1. Crear la colección si no existe
        # 2. Procesar los archivos según su tipo
        # 3. Generar embeddings
        # 4. Almacenar en la base de datos vectorial
        
        # Por ahora simulamos el procesamiento
        processed_items = len(items)
        answer = f"Successfully processed {processed_items} items for collection '{collection}'"
        
        log_operation(user_email, "COLLECTION_CREATE", input_data, answer)
        
        return jsonify({
            'success': True,
            'answer': answer,
            'collection': collection,
            'processed_items': processed_items
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Collection creation failed: {str(e)}'}), 500

def get_collections_handler():
    """Handler para listar todas las colecciones disponibles"""
    try:
        # TODO: Aquí va la lógica para obtener todas las colecciones
        # Integrar el código necesario para:
        # 1. Conectar a la base de datos
        # 2. Obtener lista de colecciones
        # 3. Obtener metadatos básicos de cada colección
        
        # Por ahora retornamos datos de ejemplo
        collections = [
            {
                'name': 'example_collection_1',
                'items_count': 15,
                'created_at': '2024-01-15T10:30:00',
                'last_updated': '2024-01-20T14:45:00'
            },
            {
                'name': 'example_collection_2',
                'items_count': 8,
                'created_at': '2024-01-18T09:15:00',
                'last_updated': '2024-01-19T16:20:00'
            }
        ]
        
        return jsonify({
            'success': True,
            'collections': collections,
            'total_collections': len(collections)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve collections: {str(e)}'}), 500

def get_collection_info_handler(collection_name):
    """Handler para obtener información detallada de una colección específica"""
    try:
        if not collection_name or not collection_name.strip():
            raise ValueError("Collection name cannot be empty")
        
        collection_name = collection_name.strip()
        
        # TODO: Aquí va la lógica para obtener información detallada de la colección
        # Integrar el código necesario para:
        # 1. Verificar que la colección existe
        # 2. Obtener metadatos detallados
        # 3. Obtener estadísticas de uso
        # 4. Obtener lista de documentos/items
        
        # Por ahora retornamos datos de ejemplo
        if collection_name == "nonexistent":
            raise FileNotFoundError(f"Collection '{collection_name}' not found")
        
        collection_info = {
            'name': collection_name,
            'description': f'Collection {collection_name} description',
            'items_count': 25,
            'total_size_bytes': 1024000,
            'created_at': '2024-01-15T10:30:00',
            'last_updated': '2024-01-20T14:45:00',
            'embedding_model': 'text-embedding-ada-002',
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'items': [
                {
                    'id': 'item_1',
                    'name': 'document1.pdf',
                    'type': 'pdf',
                    'size_bytes': 512000,
                    'chunks_count': 15,
                    'added_at': '2024-01-15T10:35:00'
                },
                {
                    'id': 'item_2',
                    'name': 'notes.md',
                    'type': 'md',
                    'size_bytes': 25600,
                    'chunks_count': 3,
                    'added_at': '2024-01-16T11:20:00'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'collection': collection_info
        })
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve collection info: {str(e)}'}), 500

def update_collection_handler(data, user_email):
    """Handler para actualizar una colección existente"""
    try:
        # Validar campos requeridos
        validate_required_fields(data, ['collection'])
        
        collection = data.get('collection').strip()
        action = data.get('action', 'update').lower()
        
        # Validar acción
        allowed_actions = ['update', 'add_items', 'remove_items', 'update_settings']
        if action not in allowed_actions:
            raise ValueError(f"Invalid action '{action}'. Allowed: {', '.join(allowed_actions)}")
        
        # Log de la operación
        input_data = f"collection: {collection}, action: {action}"
        
        # TODO: Aquí va la lógica para actualizar la colección según la acción
        # Integrar el código necesario para:
        # 1. Verificar que la colección existe
        # 2. Procesar la acción específica:
        #    - update: actualizar metadatos generales
        #    - add_items: agregar nuevos elementos
        #    - remove_items: eliminar elementos específicos
        #    - update_settings: cambiar configuración (chunk_size, modelo, etc.)
        
        # Por ahora simulamos la actualización
        if action == 'update':
            answer = f"Successfully updated collection '{collection}'"
        elif action == 'add_items':
            items = data.get('items', [])
            answer = f"Successfully added {len(items)} items to collection '{collection}'"
        elif action == 'remove_items':
            item_ids = data.get('item_ids', [])
            answer = f"Successfully removed {len(item_ids)} items from collection '{collection}'"
        elif action == 'update_settings':
            answer = f"Successfully updated settings for collection '{collection}'"
        
        log_operation(user_email, "COLLECTION_UPDATE", input_data, answer)
        
        return jsonify({
            'success': True,
            'answer': answer,
            'collection': collection,
            'action': action
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Collection update failed: {str(e)}'}), 500

def get_llms_handler():
    """Handler para obtener proveedores de LLM disponibles"""
    try:
        # TODO: Aquí va la lógica para obtener los proveedores de LLM
        # Integrar el código necesario para obtener proveedores configurados
        
        providers = [
            {
                'name': 'OpenAI',
                'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo-preview'],
                'status': 'available'
            },
            {
                'name': 'Anthropic',
                'models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
                'status': 'available'
            },
            {
                'name': 'Ollama',
                'models': ['llama2', 'mistral', 'codellama'],
                'status': 'available'
            }
        ]
        
        return jsonify({
            'success': True,
            'providers': providers
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve LLM providers: {str(e)}'}), 500

def get_embeddings_handler():
    """Handler para obtener proveedores de embeddings disponibles"""
    try:
        # TODO: Aquí va la lógica para obtener los proveedores de embeddings
        # Integrar el código necesario para obtener proveedores configurados
        
        providers = [
            {
                'name': 'OpenAI',
                'models': ['text-embedding-ada-002', 'text-embedding-3-small', 'text-embedding-3-large'],
                'status': 'available'
            },
            {
                'name': 'HuggingFace',
                'models': ['sentence-transformers/all-MiniLM-L6-v2', 'sentence-transformers/all-mpnet-base-v2'],
                'status': 'available'
            },
            {
                'name': '