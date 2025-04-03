# run.py
from dotenv import load_dotenv
load_dotenv(verbose=True) # Keep this for debugging if needed

from app import create_app

app = create_app()

if __name__ == '__main__':
    # --- CHANGE HERE ---
    # Explicitly pass the debug state from the app's config to app.run()
    debug_mode = app.config.get('DEBUG', False) # Get the final debug state
    print(f"--- Starting app.run() with debug={debug_mode} ---") # Add print for confirmation
    app.run(host='127.0.0.1', port=5000, debug=debug_mode)
    # --- END CHANGE ---