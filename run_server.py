import uvicorn
import os
import sys

# Ensure backend directory is in Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

if __name__ == "__main__":
    print("==========================================================================")
    print("Starting M365 Administration & AI Governance Platform (FastAPI Gateway)")
    print("==========================================================================")
    print("Frontend UI & Dashboard: http://127.0.0.1:8000")
    print("Interactive API Docs:    http://127.0.0.1:8000/api/v1/docs")
    print("Accessible over LAN/IP:  http://<YOUR_SERVER_IP>:8000")
    print("==========================================================================")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["backend", "frontend"])
