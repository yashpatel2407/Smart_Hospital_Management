"""
Vercel Serverless Entry Point
Exposes the Flask app as a Vercel serverless function.
"""
import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()
