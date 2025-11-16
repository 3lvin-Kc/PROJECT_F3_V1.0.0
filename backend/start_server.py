#!/usr/bin/env python3
"""
F3 Backend Server Startup Script
================================
This script properly sets up the Python path and starts the F3 backend server.
"""

import sys
import os
from pathlib import Path

# Add the server directory to Python path
backend_dir = Path(__file__).parent
server_dir = backend_dir / "server"
sys.path.insert(0, str(server_dir))

# Now import and run the server
if __name__ == "__main__":
    import uvicorn
    
    print("  Starting F3 Backend Server...")
    print(f"  Backend directory: {backend_dir}")
    print(f"  Server directory: {server_dir}")
    print("  Server will be available at: http://localhost:8000")
    print("  API docs will be available at: http://localhost:8000/docs")
    print("-" * 60)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(server_dir)]
    )
