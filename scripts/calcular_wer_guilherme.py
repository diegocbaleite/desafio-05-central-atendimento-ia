from pathlib import Path
from src.guilherme_multimodal import metricas

base = Path("resultados/guilherme")

arquivo_referencia = base / "referencia_audio_conferida.txt"

arquivo_whisper = (
    base
    / "stt_20261017T165955Z_e88296"
    / "transcricao_bruta.txt"
)

referencia = arquivo_referencia.read_text(
    encoding="utf-8"
).strip()

transcricao = arquivo_whisper.read_text(
    encoding="utf-8"
).strip()

if not referencia:
    raise ValueError("A referência está vazia!")

if "from pathlib import Path" in referencia or "python - <<'PY'" in referencia:
    raise ValueError("A referência contém código Python. Corrija o TXT.")

resultado = metricas(referencia, transcricao)

print("\n=== AVALIAÇÃO WHISPER SMALL ===")
print("Modelo: Whisper Small")
print("Provedor: Local")
print(f"Palavras na referência: {resultado['palavras_referencia']}")
print(f"Erros de palavras: {resultado['erros_palavras']}")
print(f"WER: {resultado['wer'] * 100:.2f}%")
print(f"CER: {resultado['cer'] * 100:.2f}%")

if len(referencia.split()) < len(transcricao.split()) * 0.7:
    print("\nATENÇÃO: A referência parece incompleta.")
    print("Confira os 89 segundos do áudio antes de validar as métricas.")
