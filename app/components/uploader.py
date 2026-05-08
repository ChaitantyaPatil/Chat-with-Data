# ============================================================
#  File Uploader Component
#  Streamlit widget for CSV/Excel file upload with validation
#  feedback and automatic data pipeline triggering.
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from backend.data_cleaner import CleaningReport, clean_dataframe
from backend.data_loader import DataLoadError, load_dataframe, save_uploaded_file
from backend.schema_detector import SchemaInfo, detect_schema
from utils.logger import get_logger
from utils.validators import validate_dataframe

logger = get_logger(__name__)


def render_uploader() -> Optional[Tuple[pd.DataFrame, pd.DataFrame, SchemaInfo, CleaningReport]]:
    """
    Render the file upload widget and run the data pipeline.

    Returns:
        Tuple of (raw_df, cleaned_df, schema, cleaning_report) if a file
        is uploaded and processed successfully, or None.
    """
    uploaded_file = st.file_uploader(
        "📂 Upload your data file",
        type=["csv", "xlsx", "xls"],
        help="Supported formats: CSV, Excel (.xlsx, .xls). Max 200 MB.",
        key="file_uploader",
    )

    if uploaded_file is None:
        return None

    # Show file info
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            border: 1px solid #4338ca;
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">📄</span>
                <div>
                    <div style="font-weight: 600; color: #e0e7ff; font-size: 15px;">
                        {uploaded_file.name}
                    </div>
                    <div style="color: #a5b4fc; font-size: 13px;">
                        {file_size_mb:.2f} MB • {Path(uploaded_file.name).suffix.upper()} file
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Process the file
    try:
        with st.spinner("🔄 Loading and processing data…"):
            # Save to uploads
            save_uploaded_file(uploaded_file)

            # Load into DataFrame
            raw_df = load_dataframe(
                uploaded_file.name,
                file_bytes=uploaded_file.getbuffer().tobytes(),
            )

            # Validate
            warnings = validate_dataframe(raw_df)
            if warnings:
                for w in warnings:
                    st.warning(w, icon="⚠️")

            # Clean
            cleaned_df, cleaning_report = clean_dataframe(raw_df)

            # Detect schema
            schema = detect_schema(cleaned_df)

            logger.info("Upload pipeline complete: %s", uploaded_file.name)

        # Show success
        st.success(
            f"✅ Loaded **{len(cleaned_df):,}** rows × **{len(cleaned_df.columns)}** columns",
            icon="🎉",
        )

        return raw_df, cleaned_df, schema, cleaning_report

    except DataLoadError as exc:
        st.error(f"❌ {exc}", icon="🚫")
        logger.error("Upload failed: %s", exc)
        return None
    except Exception as exc:
        st.error(f"❌ Unexpected error: {exc}", icon="🚫")
        logger.exception("Unexpected error during upload processing.")
        return None
