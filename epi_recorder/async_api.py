"""
Async API for EPI Recording.

Provides async/await compatible recording for modern agent frameworks
like LangChain, CrewAI, and AutoGPT that use asyncio.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
from pathlib import Path

from epi_recorder.patcher import (
    RecordingContext,
    set_recording_context,
    get_recording_context,
    patch_all
)


class AsyncRecorder:
    """Async-native recorder for modern agent frameworks."""
    
    def __init__(self, output_dir: Path, enable_redaction: bool = True):
        """
        Initialize async recorder.
        
        Args:
            output_dir: Directory for recording output
            enable_redaction: Whether to enable secret redaction
        """
        self.output_dir = Path(output_dir)
        self.enable_redaction = enable_redaction
        self.context: Optional[RecordingContext] = None
        self._token: Optional[Any] = None
        self._step_queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start async recording session."""
        # Create recording context
        self.context = RecordingContext(
            output_dir=self.output_dir,
            enable_redaction=self.enable_redaction
        )
        
        # Set context (thread-safe)
        self._token = set_recording_context(self.context)
        
        # Activate monkey patches
        patch_all()
        
        # Initialize async step queue for non-blocking writes
        self._step_queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._flush_worker())
    
    async def _flush_worker(self) -> None:
        """Background task to flush queued steps."""
        while True:
            try:
                # Check if we should exit
                step = await asyncio.wait_for(
                    self._step_queue.get(),
                    timeout=0.1
                )
                
                if step is None:  # Shutdown signal
                    break
                
                # Process step (this would be custom async step handling)
                # For now, the RecordingContext handles steps synchronously
                
                self._step_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in flush worker: {e}")
    
    async def stop(self) -> Path:
        """
        Stop recording and finalize.
        
        Returns:
            Path to finalized recording
        """
        # Signal worker to stop
        if self._step_queue:
            await self._step_queue.put(None)
            await self._step_queue.join()
        
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
        
        # Finalize storage
        if self.context and self.context.storage:
            final_path = self.context.storage.finalize()
        else:
            final_path = self.output_dir / "steps.jsonl"
        
        # Clear context
        if self._token:
            set_recording_context(None)
        
        return final_path


@asynccontextmanager
async def record_async(
    output_dir: Path,
    enable_redaction: bool = True
) -> AsyncGenerator[AsyncRecorder, None]:
    """
    Async context manager for recording agent execution.
    
    Usage:
        async with record_async(Path("./recording")) as recorder:
            await agent.arun("task")
    
    Args:
        output_dir: Directory for recording output
        enable_redaction: Whether to enable secret redaction
        
    Yields:
        AsyncRecorder instance
    """
    recorder = AsyncRecorder(output_dir, enable_redaction)
    await recorder.start()
    try:
        yield recorder
    finally:
        await recorder.stop()


# Convenience function for simple async recording
async def record_async_simple(output_dir: Path, func, *args, **kwargs):
    """
    Record an async function execution.
    
    Usage:
        result = await record_async_simple(
            Path("./recording"),
            my_async_agent_function,
            arg1, arg2, kwarg1=value1
        )
    
    Args:
        output_dir: Directory for recording output
        func: Async function to record
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func execution
    """
    async with record_async(output_dir) as recorder:
        result = await func(*args, **kwargs)
        return result
