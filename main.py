# ============================================================
#  Chat with Data — Launcher
#  Run with: python main.py
# ============================================================

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Launch the Streamlit application."""
    app_path = Path(__file__).parent / "app" / "main.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.headless", "true"],
        cwd=str(Path(__file__).parent),
    )


if __name__ == "__main__":
    main()
