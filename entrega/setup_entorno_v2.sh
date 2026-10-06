#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TASK_ROOT"
command -v blender >/dev/null || { echo 'Instalar Blender 4.3.2 o compatible y añadir blender al PATH.' >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install -r entrega/requirements.lock.txt
mkdir -p /tmp/macarena-mpl /tmp/macarena-cache
export MPLCONFIGDIR=/tmp/macarena-mpl
export XDG_CACHE_HOME=/tmp/macarena-cache
.venv/bin/python -c 'import fitz,numpy,PIL,matplotlib,reportlab,shapely; print("Dependencias V2 disponibles")'
blender --version
echo 'Entorno listo. Reconstrucción: consultar entrega/LEEME_V2.md.'
