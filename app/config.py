# app/config.py
import os
from dotenv import load_dotenv

#print("--- Loading .env file ---")
# Add verbose=True to see which .env file is loaded (if any)
loaded_dotenv = load_dotenv(verbose=True)
#print(f"--- .env file loaded: {loaded_dotenv} ---")

# Print the raw environment variable value *after* load_dotenv
flask_debug_env_var = os.environ.get('FLASK_DEBUG')
#print(f"--- FLASK_DEBUG from os.environ: '{flask_debug_env_var}' (type: {type(flask_debug_env_var)}) ---")


class Config:
    SECRET_KEY = os.environ.get('change this while your running ->SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    # Explicitly read FLASK_DEBUG here within the class definition
    debug_value_str = os.environ.get('FLASK_DEBUG', 'False') # Default to 'False' string
    DEBUG = debug_value_str.lower() in ('true', '1', 't')
    #print(f"--- Inside Config - Read FLASK_DEBUG as string: '{debug_value_str}' ---")
    #print(f"--- Inside Config - Calculated Config.DEBUG: {DEBUG} (type: {type(DEBUG)}) ---")