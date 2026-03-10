"""
Main entry point for SecureSteg backend.
Run: python run.py
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    env = os.getenv("ENVIRONMENT", "development")
    debug = env.lower() == "development"
    
    print("""
    ========================================================
         SecureSteg - Steganography Platform
              Starting Backend Server
    ========================================================
    """)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=debug,
        log_level="info"
    )
