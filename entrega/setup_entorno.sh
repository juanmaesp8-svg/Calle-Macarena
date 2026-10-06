#!/usr/bin/env bash
set -euo pipefail
# Configuración local y repetible; no modifica Python ni Blender del sistema.
macarena_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
command -v blender >/dev/null || { printf '%s\n' 'Se requiere Blender4.3 o superior con Cycles.' >&2; exit 1; }
python -m venv "$macarena_root/.venv"
if [[ -f "$macarena_root/entrega/requirements.lock.txt" ]]; then
  "$macarena_root/.venv/bin/python" -m pip install -r "$macarena_root/entrega/requirements.lock.txt"
else
  "$macarena_root/.venv/bin/python" -m pip install PyMuPDF Shapely==2.1.2 Matplotlib Pillow ReportLab numpy
fi
macarena_tools="$macarena_root/herramientas"
mkdir -p "$macarena_tools"
macarena_archive="$macarena_tools/oidn-2.5.1.x86_64.linux.tar.gz"
if [[ ! -f "$macarena_archive" ]]; then
  curl --fail --location --proto '=https' --tlsv1.2 'https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz' -o "$macarena_archive"
fi
printf '%s  %s\n' '743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6' "$macarena_archive" | sha256sum -c -
tar -xzf "$macarena_archive" -C "$macarena_tools"
blender --version
"$macarena_root/.venv/bin/python" - "$macarena_tools" <<'PY'
from pathlib import Path
import tempfile,subprocess,struct,sys
tools=Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix='prueba_oidn_',dir=tools) as directory:
    p=Path(directory);size=64
    (p/'input.pfm').write_bytes(b'PF\n64 64\n-1.0\n'+struct.pack('<f',.1)*(size*size*3))
    subprocess.run([str(tools/'oidn-2.5.1.x86_64.linux/bin/oidnDenoise'),'--device','cpu','--hdr',str(p/'input.pfm'),'--threads','1','--affinity','0','-o',str(p/'output.pfm')],check=True)
    if not (p/'output.pfm').is_file():raise RuntimeError('Prueba OIDN sin archivo de salida')
PY
printf '%s\n' 'Entorno preparado: Python local, Blender disponible y OIDN verificado.'
