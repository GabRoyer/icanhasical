import subprocess
import os

# Starts the development server
pserve_path = os.path.join("..", "..", "Scripts", "pserve")
subprocess.call([pserve_path, "..\development.ini"])
