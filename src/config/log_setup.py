import sys

import streamlit as st
from loguru import logger


# PINNED : use if wan to use decorator stye for session @run_once("logging_setup")
def setup_logging() -> None:
    """Setup Loguru logging configuration.

    This function configures the logging settings for the application using Loguru.
    """
    if "logging_configured" in st.session_state and st.session_state.logging_configured:
        return

    logger.remove()  # Remove default handler

    # Colorful format for terminal with rich colors
    colorful_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | "
        "<cyan>{name}</cyan>:<blue>{function}</blue>:<yellow>{line}</yellow> | "
        "<level>{message}</level>"
    )

    # Clean format for file logging (no color codes)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}"
    )

    # Terminal/stderr with colorful format
    logger.add(
        sys.stderr,
        format=colorful_format,
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        colorize=True,
        enqueue=True,
        catch=True,
    )

    # File logging with clean format
    logger.add(
        "logs/app.log",
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
    )

    # File error logging untuk memahami error lebih baik

    # Mark logging as configured in session state
    st.session_state.logging_configured = True
    logger.info(f"log is configure :{st.session_state.logging_configured}")
