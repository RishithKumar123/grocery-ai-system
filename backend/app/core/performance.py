import time
import functools
from typing import Any, Callable, Optional
from app.core.logging import logger


class PerformanceMonitor:
    """Monitor and log performance metrics for AI operations."""
    
    @staticmethod
    def measure_time(func: Callable) -> Callable:
        """Decorator to measure and log function execution time."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            logger.info(f"{func.__name__} executed in {duration_ms:.2f}ms")
            
            # Log warning if exceeds threshold
            if duration_ms > 200:
                logger.warning(f"{func.__name__} exceeded 200ms threshold: {duration_ms:.2f}ms")
            
            return result
        return wrapper
    
    @staticmethod
    def measure_async_time(func: Callable) -> Callable:
        """Decorator to measure async function execution time."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            logger.info(f"{func.__name__} executed in {duration_ms:.2f}ms")
            
            if duration_ms > 200:
                logger.warning(f"{func.__name__} exceeded 200ms threshold: {duration_ms:.2f}ms")
            
            return result
        return wrapper


class CacheManager:
    """Simple in-memory cache for frequently accessed data."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache: dict = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.timestamps: dict = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            self.remove(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp."""
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            self.remove(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def remove(self, key: str) -> None:
        """Remove key from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def size(self) -> int:
        """Return current cache size."""
        return len(self.cache)


# Global cache instances
embedding_cache = CacheManager(max_size=500, ttl_seconds=600)  # 10 min TTL for embeddings
product_cache = CacheManager(max_size=1000, ttl_seconds=300)  # 5 min TTL for product data
ocr_cache = CacheManager(max_size=200, ttl_seconds=180)  # 3 min TTL for OCR results


def cached_result(cache: CacheManager, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        return wrapper
    return decorator


class AsyncBatchProcessor:
    """Process items in batches asynchronously for better performance."""
    
    def __init__(self, batch_size: int = 8, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    async def process_batch(
        self,
        items: list,
        process_func: Callable,
        *args,
        **kwargs
    ) -> list:
        """Process items in batches."""
        import asyncio
        
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                asyncio.create_task(process_func(item, *args, **kwargs))
                for item in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {str(result)}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results


class GPUMonitor:
    """Monitor GPU availability and usage."""
    
    @staticmethod
    def is_gpu_available() -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @staticmethod
    def get_gpu_memory() -> dict:
        """Get GPU memory usage if available."""
        try:
            import torch
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                reserved = torch.cuda.memory_reserved() / 1024**3  # GB
                return {
                    "allocated_gb": allocated,
                    "reserved_gb": reserved,
                    "device_name": torch.cuda.get_device_name(0)
                }
        except ImportError:
            pass
        return {}
    
    @staticmethod
    def clear_gpu_cache() -> None:
        """Clear GPU cache if available."""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("GPU cache cleared")
        except ImportError:
            pass


class PerformanceOptimizer:
    """Main performance optimization coordinator."""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.gpu_monitor = GPUMonitor()
    
    def optimize_inference(self, use_gpu: bool = True) -> str:
        """Determine optimal device for inference."""
        if use_gpu and self.gpu_monitor.is_gpu_available():
            gpu_memory = self.gpu_monitor.get_gpu_memory()
            # Use GPU if available and has sufficient memory
            if gpu_memory.get("allocated_gb", 0) < 8:  # Less than 8GB allocated
                return "cuda"
        
        return "cpu"
    
    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        return {
            "gpu_available": self.gpu_monitor.is_gpu_available(),
            "gpu_memory": self.gpu_monitor.get_gpu_memory(),
            "cache_sizes": {
                "embeddings": embedding_cache.size(),
                "products": product_cache.size(),
                "ocr": ocr_cache.size()
            }
        }
