import sqlite3
from cryptography.fernet import Fernet
import os

class ModelRegistry:
    def __init__(self, db_path='model_registry.db'):
        self.db_path = db_path
        # Create tables and close connection
        self._initialize_database()
        
    def _get_connection(self):
        """Get a new database connection"""
        return sqlite3.connect(self.db_path)
            
    def _initialize_database(self):
        """Initialize database tables and close connection"""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        provider TEXT NOT NULL PRIMARY KEY,
                        api TEXT NOT NULL,
                        api_env_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )              
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider TEXT NOT NULL,
                        display_name TEXT NOT NULL,
                        model_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS personality (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        personality_name TEXT NOT NULL UNIQUE,
                        personality_description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
        except sqlite3.Error as e:
            raise ValueError(f"Error initializing database: {e}") from e
        finally:
            conn.close()

    def register_model(self, display_name, name, provider):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute('''
                    INSERT INTO models (provider, display_name, model_name)
                    VALUES (?, ?, ?)
                ''', (provider, display_name, name))
                conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Model with name '{name}' already exists for provider '{provider}'.") from e
        finally:
            conn.close()

    
    def register_config(self, provider, api, api_env_name):
        conn = self._get_connection()
        try:
            # Encrypt the API key before storing
            encrypted_api = self.encrypt_api_key(api)
            conn.execute('''
                INSERT INTO config (provider, api, api_env_name)
                VALUES (?, ?, ?)
            ''', (provider, encrypted_api, api_env_name))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Configuration for provider '{provider}' already exists.") from e
        finally:
            conn.close()
            
    def register_personality(self, personality_name, personality_description):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute('''
                    INSERT INTO personality (personality_name, personality_description)
                    VALUES (?, ?)
                ''', (personality_name, personality_description))
                conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Personality with name '{personality_name}' already exists.") from e
        finally:
            conn.close()
            
    # Fetch all registered personalities
    def get_all_personalities(self):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT distinct personality_name FROM personality')
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching personalities: {e}") from e
        finally:
            conn.close()
            
    # Edit personality description by name
    def edit_personality_description(self, personality_name, new_description):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE personality SET personality_description = ? WHERE personality_name = ?', 
                               (new_description, personality_name))
                if cursor.rowcount == 0:
                    raise ValueError(f"Personality '{personality_name}' not found.")
                conn.commit()
        except sqlite3.Error as e:
            raise ValueError(f"Error updating personality '{personality_name}': {e}") from e
        finally:
            conn.close()
            
    # Delete personality by name
    def delete_personality(self, personality_name):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM personality WHERE personality_name = ?', (personality_name,))
                if cursor.rowcount == 0:
                    raise ValueError(f"Personality '{personality_name}' not found.")
                conn.commit()
        except sqlite3.Error as e:
            raise ValueError(f"Error deleting personality '{personality_name}': {e}") from e
        finally:
            conn.close()
            
    # Fetch personality description by name
    def get_personality_description(self, personality_name):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT personality_description FROM personality WHERE personality_name = ?', (personality_name,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching description for personality '{personality_name}': {e}") from e
        finally:
            conn.close()
            
    # Fetch all providers
    def get_all_providers(self):
        conn = self._get_connection()
        # How can I fetch and close the cursor?
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT distinct provider FROM models')
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching providers: {e}") from e
        finally:
            conn.close()
    
    # Fetch all models for a specific provider
    def get_models_by_provider(self, provider):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT model_name, display_name FROM models WHERE provider = ?', (provider,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching models for provider '{provider}': {e}") from e
        finally:
            conn.close()
    
    # Get model display name by provider and model name
    def get_model_display_name(self, provider, model):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT display_name FROM models WHERE provider = ? AND model_name = ?', (provider, model))
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching display name for model '{model}' from provider '{provider}': {e}") from e
        finally:
            conn.close()
    
    # Fetch api key for a specific provider and model
    def get_api_key(self, provider):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT api FROM config WHERE provider = ?', (provider,))
                result = cursor.fetchone()
                if result:
                    try:
                        # Decrypt the API key if it's encrypted
                        return self.decrypt_api_key(result[0])
                    except Exception as e:
                        # If decryption fails, assume it's stored as plain text
                        return result[0]
                return None
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching API key for provider '{provider}': {e}") from e
        finally:
            conn.close()
        
    
    def get_api_env_name(self, provider):
        conn = self._get_connection()
        """Get the environment variable name for the API key of a specific provider."""
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT api_env_name FROM config WHERE provider = ?', (provider,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching environment variable name for provider '{provider}': {e}") from e
        finally:
            conn.close()
    
    # Load fernet key from secret.key file
    def load_key(self):
        if not os.path.exists('secret.key'):
            self.generate_key()
        # Load the key from the file
        with open('secret.key', 'rb') as key_file:
            key = key_file.read()
        return key
    
    # encrypt the api key
    def encrypt_api_key(self, api_key):
        key = self.load_key()
        if not key:
            raise ValueError("Encryption key is not available.")
        fernet = Fernet(key)
        encrypted_api_key = fernet.encrypt(api_key.encode('utf-8'))
        return encrypted_api_key
    
    # decrypt the api key
    def decrypt_api_key(self, encrypted_api_key):
        key = self.load_key()
        if not key:
            raise ValueError("Encryption key is not available.")
        fernet = Fernet(key)
        decrypted_api_key = fernet.decrypt(encrypted_api_key)  
        if not decrypted_api_key:
            raise ValueError("Decryption failed. Invalid encrypted API key.")
        return decrypted_api_key.decode('utf-8')
    
    # generate a new key for encryption if not exists
    def generate_key(self): 
        if not os.path.exists('secret.key'):
            key = Fernet.generate_key()
            with open('secret.key', 'wb') as key_file:
                key_file.write(key)
                
            
    # Deletre a model by provider and name
    def delete_model(self, provider, model):
        conn = self._get_connection()
        """Delete a model by provider and name."""
        try:
            with conn:
                conn.execute('DELETE FROM models WHERE provider = ? AND name = ?', (provider, model))
        finally:
            conn.close()
            
    # Update model configuration
    def delete_config(self, provider):
        conn = self._get_connection()
        """Delete a configuration by provider."""
        try:
            with conn:
                conn.execute('DELETE FROM models WHERE provider = ?', (provider))
        finally:
            conn.close()
            
    # Get privider and model names
    def get_provider_model_names(self):
        conn = self._get_connection()
        try:
            with conn:
                # Fetch all provider and model names
                cursor = conn.cursor()
                cursor.execute('SELECT provider, display_name, model_name FROM models')
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching provider and model names: {e}") from e
        finally:
            conn.close()
            
    def get_provider_configurations(self):
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('SELECT provider, api_env_name FROM config')
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise ValueError(f"Error fetching provider configurations: {e}") from e
        finally:
            conn.close()