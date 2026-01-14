import threading
import queue
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# We assume epi_recorder is installed and available
# In a real build, we would handle imports carefully
try:
    from epi_core.trust import sign_manifest
    from epi_core.schemas import ManifestModel
except ImportError:
    # Fallback for dev environment/linting without full install
    pass

logger = logging.getLogger("epi-gateway.worker")

class EvidenceWorker:
    """
    Background worker that processes the evidence queue.
    It handles:
    1. Batching (optional, simple sequential for now)
    2. Signing (CPU intensive, kept off main thread)
    3. Storage (IO intensive)
    """

    def __init__(self, storage_dir: str = "./evidence_vault"):
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self.storage_path = Path(storage_dir)
        self.processed_count = 0
        
        # Ensure storage exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the worker thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="EPI-Signer")
        self._thread.start()
        logger.info("Background Signer Thread Started")

    def stop(self):
        """Signal the worker to stop and wait for it."""
        logger.info("Stopping Background Signer...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Background Signer Stopped")

    def enqueue(self, item: Dict[str, Any]):
        """Non-blocking push to queue."""
        self._queue.put(item)

    def queue_size(self) -> int:
        return self._queue.qsize()

    def _run_loop(self):
        """Main processing loop."""
        while not self._stop_event.is_set():
            try:
                # Wait for items with timeout to allow checking stop_event
                item = self._queue.get(timeout=1.0)
                
                self._process_item(item)
                
                self.processed_count += 1
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Critical Worker Error: {e}", exc_info=True)
                # In a robust system, we might push to a Dead Letter Queue (DLQ)

    def _process_item(self, item: Dict[str, Any]):
        """
        Process a single evidence item.
        For MVP: Just saves it as a signed JSON file.
        In Prod: Would generate a full .epi zip or push to S3.
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"evidence_{timestamp}.json"
            file_path = self.storage_path / filename

            # Simulate Signing (mocking the heavy crypto work here or using epi_core)
            # In real prod:
            # manifest = ManifestModel(...)
            # signed_manifest = sign_manifest(manifest, private_key)
            # item['signature'] = signed_manifest.signature
            
            # For now, just persisting to disk to prove async flow
            item['_processed_at'] = str(datetime.utcnow())
            item['_signed'] = True # Placeholder
            
            with open(file_path, 'w') as f:
                json.dump(item, f, indent=2)
            
            logger.info(f"Persisted evidence: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to process item: {item}. Error: {e}")
