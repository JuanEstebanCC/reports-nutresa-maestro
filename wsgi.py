"""
WSGI entry point for Apache deployment
This file allows Apache to serve the FastAPI application
"""

import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app.main import app

# WSGI application object
application = app

if __name__ == "__main__":
    # This allows testing the WSGI file directly
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
