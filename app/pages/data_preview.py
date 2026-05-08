# ============================================================
#  Data Preview Page
#  Interactive DataFrame explorer with filtering,
#  column selection, search, and pagination.
# ============================================================

from __future__ import annotations
import pandas as pd
import streamlit as st
from backend.schema_detector import SchemaInfo
from backend.export_engine import export_dataframe_csv, export_dataframe_excel


def render_data_preview(df: pd.DataFrame, schema: SchemaInfo) -> None:
    """Render the data preview / explorer page."""

    st.markdown(
        '<h1 style="font-size:28px;font-weight:800;color:#e2e8f0;margin-bottom:4px;">'
        '🔍 Data Preview</h1>'
        '<p style="color:#94a3b8;font-size:14px;margin-bottom:24px;">'
        'Explore, filter, and search your dataset</p>',
        unsafe_allow_html=True,
    )

    # ── Controls Row ─────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        selected_cols = st.multiselect(
            "Select Columns",
            options=list(df.columns),
            default=list(df.columns),
            key="preview_cols",
        )

    with col2:
        search_term = st.text_input(
            "🔎 Search",
            placeholder="Search across all columns…",
            key="preview_search",
        )

    with col3:
        page_size = st.selectbox(
            "Rows per page",
            options=[25, 50, 100, 250, 500],
            index=1,
            key="preview_page_size",
        )

    # Apply column selection
    display_df = df[selected_cols] if selected_cols else df

    # Apply search filter
    if search_term:
        mask = display_df.astype(str).apply(
            lambda col: col.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        display_df = display_df[mask]
        st.info(f"Found **{len(display_df):,}** rows matching '{search_term}'", icon="🔎")

    # ── Pagination ───────────────────────────────────────
    total_rows = len(display_df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)

    if "preview_page" not in st.session_state:
        st.session_state.preview_page = 1

    # Clamp page
    st.session_state.preview_page = min(st.session_state.preview_page, total_pages)

    page = st.session_state.preview_page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    page_df = display_df.iloc[start_idx:end_idx]

    # ── Display Table ────────────────────────────────────
    st.dataframe(
        page_df,
        use_container_width=True,
        height=min(600, 35 * len(page_df) + 38),
    )

    # ── Pagination Controls ──────────────────────────────
    pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns([1, 1, 2, 1, 1])

    with pcol1:
        if st.button("⏮ First", key="pg_first", disabled=page <= 1):
            st.session_state.preview_page = 1
            st.rerun()
    with pcol2:
        if st.button("◀ Prev", key="pg_prev", disabled=page <= 1):
            st.session_state.preview_page = page - 1
            st.rerun()
    with pcol3:
        st.markdown(
            f'<div style="text-align:center;color:#94a3b8;padding:8px 0;">'
            f'Page {page} of {total_pages} &nbsp;•&nbsp; '
            f'Rows {start_idx+1}–{end_idx} of {total_rows:,}</div>',
            unsafe_allow_html=True,
        )
    with pcol4:
        if st.button("Next ▶", key="pg_next", disabled=page >= total_pages):
            st.session_state.preview_page = page + 1
            st.rerun()
    with pcol5:
        if st.button("Last ⏭", key="pg_last", disabled=page >= total_pages):
            st.session_state.preview_page = total_pages
            st.rerun()

    st.markdown("---")

    # ── Schema & Dtypes ──────────────────────────────────
    with st.expander("📐 Column Schema & Data Types", expanded=False):
        schema_data = {
            "Column": [c.name for c in schema.columns],
            "Type": [c.dtype for c in schema.columns],
            "Category": [c.category for c in schema.columns],
            "Unique": [c.unique_count for c in schema.columns],
            "Nulls": [c.null_count for c in schema.columns],
        }
        st.dataframe(pd.DataFrame(schema_data), use_container_width=True, hide_index=True)

    # ── Export ────────────────────────────────────────────
    exp1, exp2 = st.columns(2)
    with exp1:
        csv_bytes = export_dataframe_csv(display_df)
        st.download_button("📥 Download CSV", data=csv_bytes,
            file_name="data_preview.csv", mime="text/csv", key="preview_csv_dl")
    with exp2:
        xlsx_bytes = export_dataframe_excel(display_df)
        st.download_button("📥 Download Excel", data=xlsx_bytes,
            file_name="data_preview.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="preview_xlsx_dl")
