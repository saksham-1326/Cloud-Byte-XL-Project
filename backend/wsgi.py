"""Render entry point. No dotenv, migrations, workers or live observers at import."""
import os
os.environ['PYTHON_DOTENV_DISABLED']='1'
from .hosting import validate_environment,register_public_demo
allowed=validate_environment()
from .app import app,get_db_connection
register_public_demo(app,get_db_connection,allowed)
