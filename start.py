"""
Startup script to run both FastAPI API and Orchestrator
"""
import asyncio
import logging
import uvicorn
from multiprocessing import Process
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_api():
    """Run FastAPI server"""
    logger.info("Starting FastAPI server on port 8000...")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )


def run_orchestrator():
    """Run orchestrator"""
    logger.info("Starting orchestrator...")
    from orchestrator import main
    asyncio.run(main())


if __name__ == "__main__":
    # Start FastAPI in a separate process
    api_process = Process(target=run_api, name="FastAPI-Server")
    api_process.start()
    
    # Run orchestrator in main process
    try:
        run_orchestrator()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        api_process.terminate()
        api_process.join()
        sys.exit(0)
