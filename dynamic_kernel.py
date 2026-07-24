import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Awaitable, List, Any, Optional


@dataclass
class TelemetryFrame:
    timestamp: float
    batch_size: int
    execution_time_ms: float
    throughput_items_per_sec: float


class DynamicThroughputKernel:
    """
    Asynchronous execution kernel that dynamically tunes concurrency limits
    and batch execution bounds based on real-time execution throughput and latency.
    """

    def __init__(
        self,
        target_latency_ms: float = 50.0,
        min_batch_size: int = 1,
        max_batch_size: int = 500,
        min_concurrency: int = 1,
        max_concurrency: int = 50,
        ewma_alpha: float = 0.2,
    ):
        self.target_latency_ms = target_latency_ms
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.ewma_alpha = ewma_alpha

        # Dynamic Controller State
        self.current_batch_size: int = min_batch_size
        self.current_concurrency: int = min_concurrency
        self.ewma_latency_ms: float = target_latency_ms
        
        # Async Synchronization
        self.queue: asyncio.Queue = asyncio.Queue()
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(self.current_concurrency)
        self.telemetry_history: deque = deque(maxlen=100)
        self._is_running: bool = False

    def adjust_parameters(self, last_execution_ms: float, items_processed: int):
        """
        Calculates EWMA latency and updates dynamic bounds using multiplicative-increase/
        additive-decrease (MIAD) and adaptive backpressure tuning.
        """
        if items_processed == 0:
            return

        # Update EWMA Latency
        self.ewma_latency_ms = (
            self.ewma_alpha * last_execution_ms
            + (1.0 - self.ewma_alpha) * self.ewma_latency_ms
        )

        throughput = (items_processed / last_execution_ms) * 1000.0

        # Dynamic Adjustment Logic
        if self.ewma_latency_ms < self.target_latency_ms * 0.8:
            # Latency is low; scale up batch size and concurrency aggressively
            self.current_batch_size = min(
                self.max_batch_size, int(self.current_batch_size * 1.25) + 1
            )
            if self.current_concurrency < self.max_concurrency:
                self.current_concurrency += 1
                self.semaphore._value += 1
        elif self.ewma_latency_ms > self.target_latency_ms * 1.2:
            # Latency exceeding threshold; throttle down limits
            self.current_batch_size = max(
                self.min_batch_size, int(self.current_batch_size * 0.75)
            )
            if self.current_concurrency > self.min_concurrency:
                self.current_concurrency -= 1
                # Drain semaphore permit to contract concurrency limit
                asyncio.create_task(self.semaphore.acquire())

        # Log Metrics
        frame = TelemetryFrame(
            timestamp=time.time(),
            batch_size=self.current_batch_size,
            execution_time_ms=last_execution_ms,
            throughput_items_per_sec=throughput,
        )
        self.telemetry_history.append(frame)

    async def enqueue(self, item: Any):
        """Enqueues an payload item into the evaluation pipeline."""
        await self.queue.put(item)

    async def process_batch_worker(
        self,
        worker_id: int,
        processor_fn: Callable[[List[Any]], Awaitable[None]],
    ):
        """Worker loop managing batched payload extraction and dynamic yielding."""
        while self._is_running:
            async with self.semaphore:
                if self.queue.empty():
                    await asyncio.sleep(0.01)
                    continue

                # Drain items up to current optimal batch capacity
                items = []
                while not self.queue.empty() and len(items) < self.current_batch_size:
                    items.append(self.queue.get_nowait())

                if not items:
                    continue

                start_time = time.perf_counter()
                try:
                    await processor_fn(items)
                except Exception as err:
                    # Exception boundary to prevent worker crashes
                    pass
                finally:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    for _ in items:
                        self.queue.task_done()

                    # Trigger dynamic telemetry recalibration
                    self.adjust_parameters(elapsed_ms, len(items))

                # Cooperative Event-Loop Yield
                await asyncio.sleep(0)

    async def start(
        self,
        processor_fn: Callable[[List[Any]], Awaitable[None]],
        worker_count: Optional[int] = None,
    ):
        """Spawns worker pool and initial processing loops."""
        self._is_running = True
        workers = worker_count or self.max_concurrency
        tasks = [
            asyncio.create_task(self.process_batch_worker(i, processor_fn))
            for i in range(workers)
        ]
        return tasks

    async def stop(self):
        """Flushes queue and safely halts execution tasks."""
        await self.queue.join()
        self._is_running = False


# Usage Demonstration Execution Loop
async def dummy_processor(batch: List[Any]):
    # Simulated execution workload (e.g., state parsing / cryptographic evaluation)
    await asyncio.sleep(0.005 * len(batch))


async def main():
    kernel = DynamicThroughputKernel(
        target_latency_ms=25.0,
        min_batch_size=2,
        max_batch_size=100,
        min_concurrency=1,
        max_concurrency=8,
    )

    workers = await kernel.start(dummy_processor)

    # Ingest baseline telemetry payloads
    for i in range(1000):
        await kernel.enqueue(f"payload_data_{i}")

    # Wait for execution pipeline to clear
    await kernel.stop()

    print("Execution complete. Final Telemetry State:")
    if kernel.telemetry_history:
        latest = kernel.telemetry_history[-1]
        print(f"Optimal Batch Size: {latest.batch_size}")
        print(f"Observed EWMA Latency: {kernel.ewma_latency_ms:.2f} ms")
        print(f"Throughput: {latest.throughput_items_per_sec:.2f} items/sec")


if __name__ == "__main__":
    asyncio.run(main())