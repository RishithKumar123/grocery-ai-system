import logging
import sys
import os
from pathlib import Path
from app.core.config import settings

# Define custom logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


def setup_logging():
    """Sets up global application logging with file handlers for ML operations."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Base logging config
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Disable too verbose logs from third-party libraries if necessary
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # ML-specific loggers with file handlers
    _setup_ml_loggers(logs_dir, log_level)

    logger = logging.getLogger("grocery_system")
    logger.info("Logging configured successfully.")
    return logger


def _setup_ml_loggers(logs_dir: Path, log_level: int) -> None:
    """Setup specific loggers for ML operations."""
    
    # Training logger
    training_logger = logging.getLogger("ml.training")
    training_logger.setLevel(log_level)
    training_handler = logging.FileHandler(logs_dir / "training.log")
    training_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    training_logger.addHandler(training_handler)
    
    # Inference logger
    inference_logger = logging.getLogger("ml.inference")
    inference_logger.setLevel(log_level)
    inference_handler = logging.FileHandler(logs_dir / "inference.log")
    inference_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    inference_logger.addHandler(inference_handler)
    
    # Prediction logger
    prediction_logger = logging.getLogger("ml.predictions")
    prediction_logger.setLevel(log_level)
    prediction_handler = logging.FileHandler(logs_dir / "predictions.log")
    prediction_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    prediction_logger.addHandler(prediction_handler)
    
    # Unknown products logger
    unknown_logger = logging.getLogger("ml.unknown_products")
    unknown_logger.setLevel(log_level)
    unknown_handler = logging.FileHandler(logs_dir / "unknown_products.log")
    unknown_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    unknown_logger.addHandler(unknown_handler)
    
    # Error logger
    error_logger = logging.getLogger("ml.errors")
    error_logger.setLevel(logging.ERROR)
    error_handler = logging.FileHandler(logs_dir / "errors.log")
    error_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    error_logger.addHandler(error_handler)


def get_training_logger() -> logging.Logger:
    """Get logger for training operations."""
    return logging.getLogger("ml.training")


def get_inference_logger() -> logging.Logger:
    """Get logger for inference operations."""
    return logging.getLogger("ml.inference")


def get_prediction_logger() -> logging.Logger:
    """Get logger for prediction results."""
    return logging.getLogger("ml.predictions")


def get_unknown_product_logger() -> logging.Logger:
    """Get logger for unknown product detections."""
    return logging.getLogger("ml.unknown_products")


def get_error_logger() -> logging.Logger:
    """Get logger for ML errors."""
    return logging.getLogger("ml.errors")


# Initialize and expose logger
logger = setup_logging()
