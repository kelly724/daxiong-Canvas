#!/bin/bash
set -u

cd "$(dirname "$0")"

echo "============================================"
echo "   Infinite Canvas - macOS dependency setup"
echo "============================================"
echo ""

find_python() {
    if [ -x /opt/homebrew/bin/python3 ]; then
        echo "/opt/homebrew/bin/python3"
    elif [ -x /usr/local/bin/python3 ]; then
        echo "/usr/local/bin/python3"
    elif command -v python3 >/dev/null 2>&1; then
        command -v python3
    else
        echo ""
    fi
}

SYSTEM_PY="$(find_python)"
if [ -z "$SYSTEM_PY" ]; then
    echo "[ERROR] Python 3 not found. Please install Python 3.10+ first:"
    echo "https://www.python.org/downloads/"
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo "[Python] $("$SYSTEM_PY" --version 2>&1)"

"$SYSTEM_PY" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10+ is required. Current: " + sys.version.split()[0])
PY
if [ $? -ne 0 ]; then
    read -r -p "Press Enter to exit..."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo ""
    echo "[1/5] Creating project virtual environment: .venv"
    "$SYSTEM_PY" -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create .venv."
        read -r -p "Press Enter to exit..."
        exit 1
    fi
else
    echo ""
    echo "[1/5] Using existing project virtual environment: .venv"
fi

PYEXE=".venv/bin/python"
if [ ! -x "$PYEXE" ]; then
    echo "[ERROR] .venv/bin/python not found."
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo "[2/5] Checking pip..."
"$PYEXE" -m ensurepip --upgrade >/dev/null 2>&1 || true
"$PYEXE" -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to upgrade pip."
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "[3/5] Trying offline install from packages/"
echo "      Note: the bundled wheels are mostly for Windows, so macOS may fall back online."
"$PYEXE" -m pip install --no-index --find-links=packages -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "[INFO] Offline install failed or was incomplete. Trying online install..."
    "$PYEXE" -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Dependency install failed. Check network connection and pip output above."
        read -r -p "Press Enter to exit..."
        exit 1
    fi
fi

echo ""
echo "[4/5] Installing Uvicorn WebSocket extras..."
"$PYEXE" -m pip install "uvicorn[standard]"
if [ $? -ne 0 ]; then
    echo "[WARN] Failed to install uvicorn[standard]. The basic server may still run."
fi

echo ""
echo "[5/5] Verifying imports..."
"$PYEXE" - <<'PY'
import fastapi
import uvicorn
import requests
import pydantic
import multipart
import httpx
from PIL import Image
print("Dependency check passed.")
PY
if [ $? -ne 0 ]; then
    echo "[ERROR] Dependency verification failed."
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "============================================"
echo "   Done"
echo "============================================"
echo "Start the app with:"
echo "  ./mac-启动服务.command"
echo "or:"
echo "  source .venv/bin/activate && python main.py"
echo ""
read -r -p "Press Enter to exit..."
