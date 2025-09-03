import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Deshabilitado en producción
        log_level="info",
        workers=1  # PM2 manejará los workers
    )
