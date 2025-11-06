"""
Performance Metrics Module for Real-time Translation App

Tracks latency, throughput, and quality metrics for the translation pipeline.
"""
import time
import numpy as np
from collections import deque
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class PipelineMetrics:
    """Metrics for a single translation pipeline run"""
    timestamp: datetime
    stt_latency_ms: float
    translation_latency_ms: float
    tts_latency_ms: float
    total_latency_ms: float
    audio_chunk_size: int
    text_length: int
    success: bool


class PerformanceMetrics:
    """
    Tracks and analyzes performance metrics for the translation pipeline

    Monitors:
    - Latency per component (STT, Translation, TTS)
    - Total end-to-end latency
    - Throughput (chunks/sec)
    - Success rate
    - Memory usage
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize performance metrics tracker

        Args:
            max_history: Maximum number of metrics to keep in history
        """
        self.max_history = max_history

        # Latency tracking (circular buffers)
        self.stt_latencies = deque(maxlen=max_history)
        self.translation_latencies = deque(maxlen=max_history)
        self.tts_latencies = deque(maxlen=max_history)
        self.total_latencies = deque(maxlen=max_history)

        # Pipeline metrics history
        self.pipeline_history: deque[PipelineMetrics] = deque(maxlen=max_history)

        # Success tracking
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0

        # Throughput tracking
        self.start_time = time.time()
        self.chunks_processed = 0

        # Thread safety
        self._lock = threading.Lock()

    def record_stt_latency(self, latency_ms: float):
        """Record STT processing latency"""
        with self._lock:
            self.stt_latencies.append(latency_ms)

    def record_translation_latency(self, latency_ms: float):
        """Record translation processing latency"""
        with self._lock:
            self.translation_latencies.append(latency_ms)

    def record_tts_latency(self, latency_ms: float):
        """Record TTS processing latency"""
        with self._lock:
            self.tts_latencies.append(latency_ms)

    def record_pipeline_run(self, stt_ms: float, translation_ms: float,
                           tts_ms: float, chunk_size: int, text_length: int,
                           success: bool = True):
        """
        Record a complete pipeline run with all metrics

        Args:
            stt_ms: STT latency in milliseconds
            translation_ms: Translation latency in milliseconds
            tts_ms: TTS latency in milliseconds
            chunk_size: Size of audio chunk processed
            text_length: Length of transcribed text
            success: Whether the pipeline run was successful
        """
        with self._lock:
            total_ms = stt_ms + translation_ms + tts_ms

            metrics = PipelineMetrics(
                timestamp=datetime.now(),
                stt_latency_ms=stt_ms,
                translation_latency_ms=translation_ms,
                tts_latency_ms=tts_ms,
                total_latency_ms=total_ms,
                audio_chunk_size=chunk_size,
                text_length=text_length,
                success=success
            )

            self.pipeline_history.append(metrics)

            # Update component latencies
            self.stt_latencies.append(stt_ms)
            self.translation_latencies.append(translation_ms)
            self.tts_latencies.append(tts_ms)
            self.total_latencies.append(total_ms)

            # Update counters
            self.total_runs += 1
            if success:
                self.successful_runs += 1
                self.chunks_processed += 1
            else:
                self.failed_runs += 1

    def get_latency_stats(self, component: str = 'total') -> Dict[str, float]:
        """
        Get latency statistics for a component

        Args:
            component: 'stt', 'translation', 'tts', or 'total'

        Returns:
            Dictionary with min, max, mean, median, p50, p95, p99 latencies
        """
        with self._lock:
            latencies_map = {
                'stt': self.stt_latencies,
                'translation': self.translation_latencies,
                'tts': self.tts_latencies,
                'total': self.total_latencies
            }

            latencies = list(latencies_map.get(component, self.total_latencies))

            if not latencies:
                return {
                    'min': 0.0,
                    'max': 0.0,
                    'mean': 0.0,
                    'median': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0,
                    'count': 0
                }

            latencies_array = np.array(latencies)

            return {
                'min': float(np.min(latencies_array)),
                'max': float(np.max(latencies_array)),
                'mean': float(np.mean(latencies_array)),
                'median': float(np.median(latencies_array)),
                'p50': float(np.percentile(latencies_array, 50)),
                'p95': float(np.percentile(latencies_array, 95)),
                'p99': float(np.percentile(latencies_array, 99)),
                'count': len(latencies)
            }

    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        with self._lock:
            if self.total_runs == 0:
                return 0.0
            return (self.successful_runs / self.total_runs) * 100

    def get_throughput(self) -> float:
        """Get throughput in chunks per second"""
        with self._lock:
            elapsed = time.time() - self.start_time
            if elapsed == 0:
                return 0.0
            return self.chunks_processed / elapsed

    def get_component_breakdown(self) -> Dict[str, float]:
        """
        Get percentage breakdown of latency by component

        Returns:
            Dictionary with percentage of total time spent in each component
        """
        stats = {
            'stt': self.get_latency_stats('stt')['mean'],
            'translation': self.get_latency_stats('translation')['mean'],
            'tts': self.get_latency_stats('tts')['mean']
        }

        total = sum(stats.values())

        if total == 0:
            return {'stt': 0.0, 'translation': 0.0, 'tts': 0.0}

        return {
            component: (latency / total) * 100
            for component, latency in stats.items()
        }

    def get_recent_performance(self, last_n: int = 10) -> List[PipelineMetrics]:
        """
        Get recent pipeline metrics

        Args:
            last_n: Number of recent runs to retrieve

        Returns:
            List of recent PipelineMetrics
        """
        with self._lock:
            return list(self.pipeline_history)[-last_n:]

    def get_summary(self) -> Dict[str, any]:
        """
        Get comprehensive performance summary

        Returns:
            Dictionary with all performance metrics
        """
        return {
            'total_runs': self.total_runs,
            'successful_runs': self.successful_runs,
            'failed_runs': self.failed_runs,
            'success_rate_pct': self.get_success_rate(),
            'throughput_chunks_per_sec': self.get_throughput(),
            'latency_stats': {
                'stt': self.get_latency_stats('stt'),
                'translation': self.get_latency_stats('translation'),
                'tts': self.get_latency_stats('tts'),
                'total': self.get_latency_stats('total')
            },
            'component_breakdown_pct': self.get_component_breakdown()
        }

    def print_summary(self):
        """Print formatted performance summary"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)

        print(f"\nRuns: {summary['total_runs']} total, "
              f"{summary['successful_runs']} successful, "
              f"{summary['failed_runs']} failed")
        print(f"Success Rate: {summary['success_rate_pct']:.2f}%")
        print(f"Throughput: {summary['throughput_chunks_per_sec']:.2f} chunks/sec")

        print("\nLatency Statistics (ms):")
        print("-" * 60)

        for component in ['stt', 'translation', 'tts', 'total']:
            stats = summary['latency_stats'][component]
            print(f"\n{component.upper()}:")
            print(f"  Mean:   {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  P95:    {stats['p95']:.2f}ms")
            print(f"  P99:    {stats['p99']:.2f}ms")
            print(f"  Min:    {stats['min']:.2f}ms")
            print(f"  Max:    {stats['max']:.2f}ms")

        print("\nComponent Time Breakdown:")
        print("-" * 60)
        breakdown = summary['component_breakdown_pct']
        print(f"  STT:         {breakdown['stt']:.1f}%")
        print(f"  Translation: {breakdown['translation']:.1f}%")
        print(f"  TTS:         {breakdown['tts']:.1f}%")

        print("\n" + "="*60 + "\n")

    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.stt_latencies.clear()
            self.translation_latencies.clear()
            self.tts_latencies.clear()
            self.total_latencies.clear()
            self.pipeline_history.clear()

            self.total_runs = 0
            self.successful_runs = 0
            self.failed_runs = 0
            self.start_time = time.time()
            self.chunks_processed = 0


class LatencyTimer:
    """
    Context manager for timing operations

    Usage:
        with LatencyTimer() as timer:
            # do some work
            pass
        print(f"Operation took {timer.elapsed_ms}ms")
    """

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000

    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        return self.elapsed_ms
