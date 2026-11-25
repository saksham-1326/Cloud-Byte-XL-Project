"""Render WSGI entry point with a fail-closed public, SELECT-only API.

An optional, bounded historical AI worker uses a separate scoped database
identity. It is best-effort on Render Free, which sleeps after inactivity.
"""
import os
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
from .hosting import validate_environment, register_public_demo
allowed = validate_environment()
from .app import app, get_db_connection
register_public_demo(app, get_db_connection, allowed)
from .hosted_ai import launch
launch()
