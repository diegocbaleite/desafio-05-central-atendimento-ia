"""Gera os PDFs textuais do acervo fictício a partir de dados/acervo/fontes_pdf/*.txt.

Uso: python scripts/gerar_acervo_pdf.py   (requer reportlab; ver requirements-dev.txt)
A linha "=== PÁGINA ===" força quebra de página; linhas "Seção N — ..." viram títulos.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
FONTES = ROOT / "dados" / "acervo" / "fontes_pdf"
DESTINO = ROOT / "dados" / "acervo"


def gerar(fonte: Path) -> Path:
    estilos = getSampleStyleSheet()
    elementos = []
    for linha in fonte.read_text(encoding="utf-8").splitlines():
        if linha.strip() == "=== PÁGINA ===":
            elementos.append(PageBreak())
        elif not linha.strip():
            elementos.append(Spacer(1, 6))
        elif linha.startswith("Seção "):
            elementos.append(Paragraph(linha, estilos["Heading3"]))
        else:
            elementos.append(Paragraph(linha, estilos["BodyText"]))
    destino = DESTINO / (fonte.stem + ".pdf")
    # invariant=True remove data/ID aleatórios: o mesmo texto gera o mesmo hash.
    SimpleDocTemplate(
        str(destino), pagesize=A4, title=fonte.stem, invariant=True
    ).build(elementos)
    return destino


if __name__ == "__main__":
    for fonte in sorted(FONTES.glob("*.txt")):
        print(gerar(fonte).relative_to(ROOT))
