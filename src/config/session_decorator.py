import functools
from collections.abc import Callable
from typing import Any

import streamlit as st
from loguru import logger


def run_once(
    session_key: str | None = None,
) -> Callable[..., Callable[..., Any]]:
    """Decorator untuk function yang hanya boleh run sekali per session.

    Usage:
    @run_once("database_setup")
    def setup_database():
        # logic here
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate key dari function name jika tidak ada
            key = session_key or f"{func.__module__}.{func.__name__}_executed"

            if key in st.session_state and st.session_state[key]:
                logger.debug(f"⏭️ Skipping {func.__name__} - already executed")
                return st.session_state.get(f"{key}_result")

            logger.debug(f"🚀 Executing {func.__name__} for first time")
            result = func(*args, **kwargs)

            # Mark as executed dan simpan result jika ada
            st.session_state[key] = True
            if result is not None:
                st.session_state[f"{key}_result"] = result

            return result

        return wrapper

    return decorator


def run_once_per_param(param_key: str) -> Callable[..., Callable[..., Any]]:
    """Decorator untuk function yang run sekali per parameter value.

    Usage:
    @run_once_per_param("file_path")
    def load_data(file_path: str):
        # akan run sekali per file_path
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate unique key berdasarkan parameter
            param_value = kwargs.get(param_key) or (args[0] if args else None)
            key = f"{func.__module__}.{func.__name__}_{param_key}_{hash(str(param_value))}"

            if key in st.session_state:
                logger.debug(
                    f"⏭️ Returning cached result for {func.__name__}({param_value})"
                )
                return st.session_state[key]

            logger.debug(f"🚀 Executing {func.__name__}({param_value}) for first time")
            result = func(*args, **kwargs)
            st.session_state[key] = result
            return result

        return wrapper

    return decorator
