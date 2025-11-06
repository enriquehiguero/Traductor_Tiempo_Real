"""
Structured Logging Module for Real-time Translation App

Provides professional logging with JSON output, performance tracking,
and context-aware error reporting.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs for easy parsing
    and analysis. Includes performance metrics and context tracking.
    """

    def __init__(self, name: str, log_file: Optional[Path] = None,
                 console_output: bool = True, json_output: bool = False):
        """
        Initialize structured logger

        Args:
            name: Logger name (usually module name)
            log_file: Optional file path for log output
            console_output: Enable console logging
            json_output: Output logs in JSON format (vs human-readable)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.json_output = json_output

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            if json_output:
                console_handler.setFormatter(self._json_formatter())
            else:
                console_handler.setFormatter(self._human_formatter())

            self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self._json_formatter())
            self.logger.addHandler(file_handler)

    def _json_formatter(self) -> logging.Formatter:
        """Create JSON formatter for structured logs"""
        return JsonFormatter()

    def _human_formatter(self) -> logging.Formatter:
        """Create human-readable formatter"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def _log(self, level: str, message: str, **context):
        """
        Internal logging method with context

        Args:
            level: Log level
            message: Log message
            **context: Additional context fields
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "logger": self.name,
            "level": level,
            "message": message,
            **context
        }

        if self.json_output:
            log_message = json.dumps(log_entry)
        else:
            log_message = message

        getattr(self.logger, level.lower())(log_message, extra=context)

    def debug(self, message: str, **context):
        """Log debug message"""
        self._log("DEBUG", message, **context)

    def info(self, message: str, **context):
        """Log info message"""
        self._log("INFO", message, **context)

    def warning(self, message: str, **context):
        """Log warning message"""
        self._log("WARNING", message, **context)

    def error(self, message: str, **context):
        """Log error message"""
        self._log("ERROR", message, **context)

    def critical(self, message: str, **context):
        """Log critical message"""
        self._log("CRITICAL", message, **context)

    # Specialized logging methods for translation app

    def log_audio_capture(self, device_name: str, sample_rate: int,
                         chunk_size: int, source_type: str):
        """Log audio capture event"""
        self.info(
            f"Audio capture started: {device_name}",
            event="audio_capture_started",
            device=device_name,
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            source_type=source_type
        )

    def log_transcription(self, text: str, language: str,
                         duration_ms: float, model: str):
        """Log speech-to-text transcription event"""
        self.info(
            f"Transcription completed: '{text[:50]}...'",
            event="transcription_completed",
            text=text,
            language=language,
            duration_ms=duration_ms,
            model=model
        )

    def log_translation(self, original: str, translated: str,
                       source_lang: str, target_lang: str,
                       duration_ms: float, model: str):
        """Log translation event"""
        self.info(
            f"Translation completed: {source_lang}->{target_lang}",
            event="translation_completed",
            original_text=original,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            duration_ms=duration_ms,
            model=model
        )

    def log_tts(self, text: str, voice: str, duration_ms: float):
        """Log text-to-speech event"""
        self.info(
            f"TTS completed: '{text[:50]}...'",
            event="tts_completed",
            text=text,
            voice=voice,
            duration_ms=duration_ms
        )

    def log_performance(self, operation: str, duration_ms: float,
                       success: bool = True, **metrics):
        """Log performance metrics"""
        self.info(
            f"Performance: {operation} took {duration_ms:.2f}ms",
            event="performance_metric",
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            **metrics
        )

    def log_error_with_context(self, error: Exception, context: str,
                              **additional_context):
        """Log error with rich context"""
        self.error(
            f"Error in {context}: {str(error)}",
            event="error_occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            **additional_context
        )


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add any extra fields
        if hasattr(record, 'event'):
            log_data['event'] = record.event

        # Add all custom attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename',
                          'funcName', 'levelname', 'levelno', 'lineno',
                          'module', 'msecs', 'message', 'pathname',
                          'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text',
                          'stack_info']:
                log_data[key] = value

        return json.dumps(log_data)


# Global logger factory
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, log_file: Optional[Path] = None,
               console_output: bool = True,
               json_output: bool = False) -> StructuredLogger:
    """
    Get or create a structured logger

    Args:
        name: Logger name
        log_file: Optional log file path
        console_output: Enable console output
        json_output: Use JSON format

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(
            name=name,
            log_file=log_file,
            console_output=console_output,
            json_output=json_output
        )

    return _loggers[name]


# Convenience function for quick setup
def setup_app_logging(log_dir: Optional[Path] = None,
                     json_output: bool = False) -> StructuredLogger:
    """
    Setup application-wide logging

    Args:
        log_dir: Directory for log files
        json_output: Use JSON format

    Returns:
        Main application logger
    """
    if log_dir:
        log_file = log_dir / f"translation_app_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_file = None

    return get_logger(
        name="translation_app",
        log_file=log_file,
        console_output=True,
        json_output=json_output
    )
