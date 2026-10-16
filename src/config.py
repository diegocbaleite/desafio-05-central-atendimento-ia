"""Configuração sem segredos no repositório."""
import os
from pathlib import Path
import yaml
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass
ROOT = Path(__file__).resolve().parents[1]
def carregar():
    cfg = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    if cfg["seguranca"]["envio_automatico"] or not cfg["seguranca"]["revisao_obrigatoria"]:
        raise ValueError("É proibido enviar automaticamente ou ignorar revisão humana")
    return cfg
def chave(cfg, provider):
    item = cfg["provedores"].get(provider, {})
    return os.getenv(item.get("env_chave", ""), "")
