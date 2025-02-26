
# Simple launcher to avoid circular imports
import subprocess
import sys
import os

streamlit_file = os.path.abspath(sys.argv[1])
print(f"Launching Streamlit for {streamlit_file}")

subprocess.run([
    "streamlit", "run", streamlit_file, "--server.headless", "true"
])
