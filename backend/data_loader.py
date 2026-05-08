# ============================================================
#  Data Loader
#  Handles CSV and Excel file loading with encoding detection,
#  chunked reading for large files, and robust error handling.
# ============================================================

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from utils.config import get_settings
from utils.logger import get_logger
from utils.validators import validate_file_extension, validate_file_size

logger = get_logger(__name__)


class DataLoadError(Exception):
    """Raised when a file cannot be loaded into a DataFrame."""
    pass


def save_uploaded_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> Path:
    """
    Save a Streamlit UploadedFile to the uploads directory.

    Args:
        uploaded_file: The file object from ``st.file_uploader``.

    Returns:
        Path to the saved file on disk.

    Raises:
        DataLoadError: If validation fails.
    """
    settings = get_settings()

    if not validate_file_extension(uploaded_file.name):
        raise DataLoadError(
            f"Unsupported file type: '{uploaded_file.name}'. "
            "Please upload a CSV or Excel file."
        )

    if not validate_file_size(uploaded_file.size):
        raise DataLoadError(
            f"File too large ({uploaded_file.size / 1024 / 1024:.1f} MB). "
            f"Maximum allowed size is {settings.max_upload_size_mb} MB."
        )

    dest = settings.upload_dir / uploaded_file.name
    dest.write_bytes(uploaded_file.getbuffer())
    logger.info("Saved uploaded file: %s (%d bytes)", dest.name, uploaded_file.size)
    return dest


@st.cache_data(show_spinner=False)
def load_dataframe(
    file_path: str,
    file_bytes: Optional[bytes] = None,
) -> pd.DataFrame:
    """
    Load a CSV or Excel file into a pandas DataFrame.

    Supports:
      - Multiple CSV encodings (utf-8, latin-1, cp1252)
      - Chunked reading for large files
      - Excel sheets (first sheet by default)

    Args:
        file_path: Path string (used for extension detection & caching key).
        file_bytes: Raw bytes of the file (for Streamlit uploaded files).

    Returns:
        Loaded :class:`pd.DataFrame`.

    Raises:
        DataLoadError: If the file is empty, corrupted, or unreadable.
    """
    settings = get_settings()
    path = Path(file_path)
    ext = path.suffix.lower()

    logger.info("Loading file: %s (ext=%s)", path.name, ext)

    try:
        if ext == ".csv":
            return _load_csv(path, file_bytes, settings.chunk_size)
        elif ext in (".xlsx", ".xls"):
            return _load_excel(path, file_bytes)
        else:
            raise DataLoadError(f"Unsupported file extension: {ext}")
    except DataLoadError:
        raise
    except Exception as exc:
        logger.error("Failed to load %s: %s", path.name, exc)
        raise DataLoadError(f"Could not read file '{path.name}': {exc}") from exc


def _load_csv(
    path: Path,
    file_bytes: Optional[bytes],
    chunk_size: int,
) -> pd.DataFrame:
    """Load a CSV with encoding fallback and optional chunked reading."""
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    source = io.BytesIO(file_bytes) if file_bytes else path

    for encoding in encodings:
        try:
            if isinstance(source, io.BytesIO):
                source.seek(0)

            # Check file size for chunked reading
            size = len(file_bytes) if file_bytes else path.stat().st_size
            if size > 50 * 1024 * 1024:  # > 50 MB → chunked
                logger.info("Large file detected (%d MB), using chunked reading.", size // (1024 * 1024))
                chunks = pd.read_csv(
                    source,
                    encoding=encoding,
                    chunksize=chunk_size,
                    low_memory=False,
                )
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(source, encoding=encoding, low_memory=False)

            if df.empty:
                raise DataLoadError("The CSV file is empty — no data rows found.")

            logger.info(
                "CSV loaded successfully: %d rows × %d cols (encoding=%s)",
                len(df), len(df.columns), encoding,
            )
            return df

        except UnicodeDecodeError:
            logger.debug("Encoding %s failed, trying next…", encoding)
            continue

    raise DataLoadError(
        "Could not decode the CSV file. Tried encodings: " + ", ".join(encodings)
    )


def _load_excel(path: Path, file_bytes: Optional[bytes]) -> pd.DataFrame:
    """Load an Excel file (first sheet)."""
    source = io.BytesIO(file_bytes) if file_bytes else path

    df = pd.read_excel(source, engine="openpyxl")

    if df.empty:
        raise DataLoadError("The Excel file is empty — no data rows found.")

    logger.info("Excel loaded: %d rows × %d cols", len(df), len(df.columns))
    return df
