import logging
import logging.handlers


class DiscordAlertHandler(logging.Handler):
    def emit(self, record):
        # Only send alerts for ERROR level and above
        if record.levelno >= logging.CRITICAL:
            critical_message = self.format(record)
            try:
                # Lazy import send_to_private_channel function from read_send_msgs.py
                from read_send_msgs import send_to_private_channel
                import asyncio
                loop = asyncio.get_running_loop()
                loop.create_task(send_to_private_channel(
                    title=f"🚨 CRITICAL ERROR:", 
                    author=None, 
                    content=record.getMessage(), 
                    score=None, 
                    reasoning=None, 
                    thread_url=None, 
                    is_error=True
                ))
                # This action is logged inside the send_to_private_channel function
                            
            except Exception as e:
                logger.error(f"Failed to send critical alert: {e}")


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

    # Discord alert handler
    discord_handler = DiscordAlertHandler()
    discord_handler.setLevel(level)
    
    # Set up logs format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Set identical format for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    discord_handler.setFormatter(formatter)
    
    # Attach both console and file logs' handlers to logger obj
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(discord_handler)
    
    return logger


# setup at module level
logger = setup_logging()
