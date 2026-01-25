from langchain_ollama import ChatOllama
from typing import Optional
import logging

log = logging.getLogger("model_manager")

CHAT_MODEL = "mistral:7b"
AUTO_MODEL = "qwen2.5-coder:1.5b"

# Global state - models are None until enabled
_chat_model: Optional[ChatOllama] = None
_auto_model: Optional[ChatOllama] = None

# Feature enable flags
_chat_enabled = False
_auto_enabled = False


def is_chat_enabled() -> bool:
    """Check if chat model is enabled."""
    return _chat_enabled


def is_autocomplete_enabled() -> bool:
    """Check if autocomplete model is enabled."""
    return _auto_enabled


def get_chat_model() -> Optional[ChatOllama]:
    """
    Get the chat model instance.
    Returns None if chat is disabled.
    """
    global _chat_model

    if not _chat_enabled:
        return None

    # Lazy initialization - only create when needed
    if _chat_model is None:
        log.info(f"Initializing chat model: {CHAT_MODEL}")
        _chat_model = ChatOllama(model=CHAT_MODEL, temperature=0)

    return _chat_model


def get_autocomplete_model() -> Optional[ChatOllama]:
    """
    Get the autocomplete model instance.
    Returns None if autocomplete is disabled.
    """
    global _auto_model

    if not _auto_enabled:
        return None

    # Lazy initialization
    if _auto_model is None:
        log.info(f"Initializing autocomplete model: {AUTO_MODEL}")
        _auto_model = ChatOllama(model=AUTO_MODEL, temperature=0.1)

    return _auto_model


def set_chat_enabled(enabled: bool):
    """
    Enable or disable the chat model.
    If disabling, clears the model instance.
    """
    global _chat_enabled, _chat_model

    _chat_enabled = enabled

    if not enabled:
        log.info("Disabling chat model - clearing instance")
        _chat_model = None
    else:
        log.info("Enabling chat model")
        # Model will be lazily loaded on next get_chat_model() call


def set_autocomplete_enabled(enabled: bool):
    """
    Enable or disable the autocomplete model.
    If disabling, clears the model instance.
    """
    global _auto_enabled, _auto_model

    _auto_enabled = enabled

    if not enabled:
        log.info("Disabling autocomplete model - clearing instance")
        _auto_model = None
    else:
        log.info("Enabling autocomplete model")
        # Model will be lazily loaded on next get_autocomplete_model() call


def initialize_models(chat_enabled: bool = True, auto_enabled: bool = True):
    """
    Initialize model states on startup.
    """
    set_chat_enabled(chat_enabled)
    set_autocomplete_enabled(auto_enabled)

    log.info(f"Model manager initialized - Chat: {chat_enabled}, Auto: {auto_enabled}")
