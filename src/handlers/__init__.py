from .general import custom_command_handler
from .medical import medical_callback_handler

# Определяем явный экспорт для внешних модулей (main.py, network.py)
__all__ = [
    "custom_command_handler",
    "medical_callback_handler",
]