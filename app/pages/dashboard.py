import streamlit as st
import os
import pandas as pd

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Chat with Data", layout="wide")

# -------------------- HEADER --------------------
st.title("📊 Chat with Your Data")
st.markdown(
    "Analyze CSV/Excel files using AI-powered insights, charts, and natural language queries."
)

# -------------------- SIDEBAR --------------------
st.sidebar.header("⚙️ Controls")

# Placeholder for future upload
st.sidebar.subheader("📂 Upload Data")
UPLOAD_FOLDER = "data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

uploaded_file = st.sidebar.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

if uploaded_file:
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    # Save file to folder
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.sidebar.success(f"Saved to: {file_path}")

    # Load into dataframe
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    st.session_state.df = df

# Placeholder for filters
st.sidebar.subheader("🔍 Filters")
st.sidebar.info("Filters will appear after data upload")

# Reset button
if st.sidebar.button("🔄 Reset Session"):
    st.session_state.clear()
    st.rerun()
UPLOAD_FOLDER = "data/uploads"

st.sidebar.header("📂 Dataset Manager")

files = os.listdir(UPLOAD_FOLDER)

if files:
    selected_file = st.sidebar.selectbox("Select Dataset", files)

    if st.sidebar.button("Load Dataset"):
        file_path = os.path.join(UPLOAD_FOLDER, selected_file)

        if selected_file.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        st.session_state.df = df
        st.session_state.current_file = selected_file

    # Show active dataset
    if "current_file" in st.session_state:
        st.sidebar.success(f"Active: {st.session_state.current_file}")

    # Delete file
    file_to_delete = st.sidebar.selectbox("Delete Dataset", files, key="delete")

    if st.sidebar.button("Delete File"):
        os.remove(os.path.join(UPLOAD_FOLDER, file_to_delete))
        st.sidebar.warning("File deleted")
        st.rerun()

else:
    st.sidebar.info("No files uploaded yet")
st.sidebar.subheader("📁 Stored Files")

files = os.listdir(UPLOAD_FOLDER)
for file in files:
    st.sidebar.write(file)

file_to_delete = st.sidebar.selectbox("Delete file", files)

if st.sidebar.button("Delete"):
    os.remove(os.path.join(UPLOAD_FOLDER, file_to_delete))
    st.rerun()

# -------------------- MAIN LAYOUT --------------------
# Create sections using containers
kpi_section = st.container()
preview_section = st.container()
chart_section = st.container()
chat_section = st.container()
insight_section = st.container()

# -------------------- KPI SECTION --------------------
with kpi_section:
    st.subheader("📈 Overview")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Rows", "—")
    col2.metric("Columns", "—")
    col3.metric("Missing Values", "—")
    col4.metric("Data Types", "—")

# -------------------- DATA PREVIEW --------------------
with preview_section:
    st.subheader("👀 Data Preview")
    st.info("Upload a file to see preview")

# -------------------- CHART SECTION --------------------
with chart_section:
    st.subheader("📊 Visualizations")
    st.info("Charts will appear after data upload")

# -------------------- CHAT SECTION --------------------
with chat_section:
    st.subheader("💬 Chat with Data")
    user_query = st.text_input("Ask something about your data")

    if user_query:
        st.write(f"🧑 You: {user_query}")
        st.write("🤖 AI: (Response will appear here)")

# -------------------- INSIGHTS SECTION --------------------
with insight_section:
    st.subheader("🧠 AI Insights")
    if st.button("Generate Insights"):
        st.write("Insights will appear here...")
