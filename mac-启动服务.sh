#!/bin/bash
cd "$(dirname "$0")"
LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)"
if [ -z "$LAN_IP" ]; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
fi
if [ -z "$LAN_IP" ]; then
  LAN_IP="127.0.0.1"
fi
APP_URL="http://${LAN_IP}:3000/"

echo "Starting ComfyUI-API-Modelscope..."
echo "Visit: ${APP_URL}"
echo "Local: http://127.0.0.1:3000/"
echo "Press Ctrl+C to stop."
echo ""

# Open browser after 3 seconds
sleep 3 && open "${APP_URL}" &

if [ -x ".venv/bin/python" ]; then
  PYEXE=".venv/bin/python"
else
  PYEXE="$(command -v python3)"
fi

"${PYEXE}" - <<'PY' >/dev/null 2>&1
import fastapi, uvicorn, requests, pydantic, multipart, httpx
from PIL import Image
PY
if [ $? -ne 0 ]; then
  chmod +x mac-安装依赖.sh 2>/dev/null
  ./mac-安装依赖.sh
  PYEXE=".venv/bin/python"
fi

"${PYEXE}" main.py

echo ""
echo "Server stopped."
