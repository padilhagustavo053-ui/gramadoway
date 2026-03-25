"""Inicia o sistema Gramadoway, usando porta livre (8501 ou 8502)."""
import os
import socket
import subprocess
import sys
from pathlib import Path

def porta_livre(p):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", p))
        return True
    except OSError:
        return False
    finally:
        s.close()

porta = 8501 if porta_livre(8501) else 8502
print(f"Usando porta {porta} -> http://localhost:{porta}")
os.chdir(Path(__file__).parent)
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(porta)])
