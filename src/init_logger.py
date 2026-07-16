import logging
import logging.handlers


def setup_logging(log_file='data/app.log', level=logging.INFO):
    """Configure logging for the entire application."""
    
    # Create a logger
    logger = logging.getLogger('myapp')
    logger.setLevel(level)
    
    # Do not add duplicate handlers if this is called more than once
    if logger.hasHandlers():
        return logger
    
    # File logs handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Console logs handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Set up logs format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Set identical format for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Attach both console and file logs' handlers to logger obj
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# setup at module level
logger = setup_logging()
