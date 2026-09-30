import sys
from pathlib import Path

# Add project root directory to Python module search path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Expose the FastAPI application instance for Vercel Serverless
from backend.main import app

# Export as handler / app for Vercel ASGI runtime
handler = app
