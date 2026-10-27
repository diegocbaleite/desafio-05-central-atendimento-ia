"""Gera o ZIP de entrega a partir dos arquivos VERSIONADOS (git archive).

Uso: python scripts/gerar_zip_entrega.py   ->  entrega/desafio-06-central-atendimento-ia.zip

Como só entram arquivos rastreados pelo Git, ficam de fora .env, .venv, indice/, banco de
revisões, logs locais e documentos enviados pela interface. O script ainda confere o ZIP
contra nomes proibidos e padrões de credencial antes de concluir.
"""

import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "entrega" / "desafio-06-central-atendimento-ia.zip"
PROIBIDOS = re.compile(r"(^|/)(\.env$|\.env\.(?!example)|\.venv/|venv/|indice/|__pycache__/)|\.sqlite3$")
CREDENCIAIS = re.compile(rb"AIza[0-9A-Za-z_\-]{20,}|\bsk-[A-Za-z0-9_\-]{16,}|\bgsk_[A-Za-z0-9]{16,}|CANARIO-[0-9a-f]{8,}")


def main() -> int:
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        print("Atenção: há alterações não commitadas; o ZIP contém apenas o último commit.")
    DESTINO.parent.mkdir(exist_ok=True)
    subprocess.run(["git", "archive", "--format=zip", "--prefix=desafio-06-central-atendimento-ia/", "-o", str(DESTINO), "HEAD"],
                   cwd=ROOT, check=True)
    problemas = []
    with zipfile.ZipFile(DESTINO) as z:
        for nome in z.namelist():
            relativo = nome.split("/", 1)[-1]
            if PROIBIDOS.search(relativo):
                problemas.append(f"arquivo proibido: {relativo}")
            elif not nome.endswith("/") and CREDENCIAIS.search(z.read(nome)):
                problemas.append(f"possível credencial: {relativo}")
        total = len(z.namelist())
    if problemas:
        DESTINO.unlink()
        print("ZIP removido. Problemas:\n- " + "\n- ".join(problemas))
        return 1
    print(f"{DESTINO.relative_to(ROOT)}: {total} entradas, {DESTINO.stat().st_size / 1024:.0f} KiB, sem .env/índice/credenciais")
    return 0


if __name__ == "__main__":
    sys.exit(main())
