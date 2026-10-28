"""Adaptador OpenAI isolado da recuperação, com orçamento compartilhado e HTTP limitado."""

from __future__ import annotations

import copy
import json
import math
import time
from dataclasses import dataclass

import jsonschema
import requests

from src.cliente import _payload
from src.config import carregar, chave


class ErroServico(RuntimeError):
    """Diagnóstico técnico seguro: não incorpora corpo de erro nem credenciais."""


class LimiteOrcamento(ErroServico):
    pass


@dataclass
class Orcamento:
    max_chamadas: int = 12
    max_tokens: int = 60000
    chamadas: int = 0
    tokens_reservados: int = 0
    tokens_medidos: int = 0

    def reservar(self, tokens: int) -> None:
        if tokens < 0 or self.chamadas >= self.max_chamadas or self.tokens_reservados + tokens > self.max_tokens:
            raise LimiteOrcamento("Orçamento de chamadas/tokens esgotado; execução interrompida")
        self.chamadas += 1
        self.tokens_reservados += tokens

    def resumo(self) -> dict:
        return dict(self.__dict__)


class ClienteOpenAI:
    simulado = False

    def __init__(self, *, cfg=None, orcamento=None, modelo=None):
        self.cfg = copy.deepcopy(cfg or carregar())
        nova = self.cfg.get("desafio6", {})
        self.conf = {**self.cfg["llm"], **nova.get("geracao", {})}
        self.modelo = modelo or self.conf["modelo"]
        if self.conf.get("provider", "openai") != "openai":
            raise ErroServico("Desafio 6 usa o adaptador OpenAI; simulação exige seleção explícita")
        emb = nova.get("embeddings", {})
        self.modelo_embeddings = emb.get("modelo", "text-embedding-3-small")
        self.dimensao = int(emb.get("dimensao", 256))
        limites = nova.get("limites", {})
        self.orcamento = orcamento or Orcamento(
            int(limites.get("max_chamadas", 12)), int(limites.get("max_tokens", 60000))
        )
        self.chamadas: list[dict] = []
        self.metadados = self.chamadas
        self.saidas_estruturadas: list[dict] = []

    def _requisitar(self, endpoint: str, payload: dict, *, tokens: int, multipart=None) -> dict:
        token = chave(self.cfg, "openai")
        if not token:
            raise ErroServico("OPENAI_API_KEY ausente; configure o .env local")
        perfil = self.cfg["provedores"]["openai"]
        inicio = time.monotonic()
        for tentativa in range(2):  # Uma repetição transitória, contabilizada no mesmo orçamento.
            self.orcamento.reservar(tokens)
            registro = {"endpoint": endpoint, "modelo": payload.get("model"),
                        "tentativa": tentativa + 1, "simulada": False}
            self.chamadas.append(registro)
            envio = {"json": payload} if multipart is None else {"data": payload, "files": multipart}
            if multipart:
                for arquivo in multipart.values():
                    if hasattr(arquivo[-1], "seek"):
                        arquivo[-1].seek(0)
            try:
                resposta = requests.post(
                    perfil["base_url"].rstrip("/") + endpoint,
                    headers={"Authorization": "Bearer " + token}, **envio,
                    timeout=min(60, float(self.conf.get("timeout_s", 30))),
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                registro.update(status="falha", erro=type(exc).__name__)
                registro["latencia_s"] = round(time.monotonic() - inicio, 3)
                if tentativa == 0:
                    time.sleep(1)
                    continue
                raise ErroServico("Falha de transporte OpenAI após duas tentativas") from None
            except requests.RequestException:
                registro.update(status="falha", erro="transporte")
                raise ErroServico("Falha de transporte OpenAI") from None
            registro.update(http=resposta.status_code, latencia_s=round(time.monotonic() - inicio, 3))
            if resposta.status_code in (429, 500, 502, 503, 504) and tentativa == 0:
                registro.update(status="falha", erro="transitoria")
                time.sleep(1)
                continue
            if not resposta.ok:
                registro.update(status="falha", erro="http")
                raise ErroServico(f"OpenAI recusou a operação (HTTP {resposta.status_code})")
            try:
                dados = resposta.json()
                if not isinstance(dados, dict):
                    raise ValueError
            except ValueError:
                registro.update(status="falha", erro="json_invalido")
                raise ErroServico("OpenAI retornou JSON inválido") from None
            uso = dados.get("usage") or {}
            if not isinstance(uso, dict):
                uso = {}
            entrada = uso.get("prompt_tokens", uso.get("input_tokens"))
            saida = uso.get("completion_tokens", uso.get("output_tokens"))
            registro.update(status="sucesso", modelo=dados.get("model", payload.get("model")),
                            tokens_entrada=entrada, tokens_saida=saida, custo_usd=None)
            total = uso.get("total_tokens")
            if isinstance(total, int) and total >= 0:
                self.orcamento.tokens_medidos += total
                # A reserva conservadora não é devolvida, mesmo após falha transitória.
                if total > tokens:
                    self.orcamento.tokens_reservados += total - tokens
            return dados
        raise ErroServico("Operação OpenAI não concluída")

    def gerar_json(self, sistema: str, conteudo: str, esquema: dict, *, nome="resposta") -> dict:
        mensagens = [{"role": "system", "content": sistema}, {"role": "user", "content": conteudo}]
        payload = _payload(mensagens, self.modelo, self.conf, "openai")
        schema_api = copy.deepcopy(esquema)
        schema_api.pop("$schema", None)
        schema_api.pop("$id", None)
        payload["response_format"] = {"type": "json_schema", "json_schema": {
            "name": nome, "strict": True, "schema": schema_api,
        }}
        # Bytes de UTF-8 + margem de protocolo + teto de saída: reserva conservadora,
        # não tokenização medida nem estimativa de custo.
        reserva = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 512 + self.conf["max_tokens"]
        dados = self._requisitar("/chat/completions", payload, tokens=reserva)
        try:
            escolha = dados["choices"][0]
            if escolha.get("finish_reason") == "length" or escolha["message"].get("refusal"):
                raise ValueError
            objeto = json.loads(escolha["message"]["content"])
            from .guardrails import validar_saida
            serializado = json.dumps(objeto, ensure_ascii=False)
            token = chave(self.cfg, "openai")
            seguro = (not token or token not in serializado) and validar_saida(serializado)["decisao"] == "permitir"
            self.saidas_estruturadas.append({"etapa": nome, "objeto": objeto} if seguro else {"etapa": nome, "conteudo_omitido": "dado_indevido"})
            if not seguro:
                raise ErroServico("Saída estruturada contém dado indevido; conteúdo bloqueado")
            jsonschema.validate(objeto, esquema)
        except (KeyError, IndexError, TypeError, ValueError, jsonschema.ValidationError):
            raise ErroServico("Resposta estruturada recusada, truncada ou inválida; nenhuma minuta liberada") from None
        return objeto

    def embeddings(self, textos: list[str]) -> list[list[float]]:
        if not textos or any(not isinstance(t, str) or not t.strip() for t in textos):
            raise ValueError("Embeddings exigem lista não vazia de textos")
        payload = {"model": self.modelo_embeddings, "input": textos, "dimensions": self.dimensao,
                   "encoding_format": "float"}
        reserva = sum(len(t.encode("utf-8")) for t in textos) + 512
        dados = self._requisitar("/embeddings", payload, tokens=reserva)
        try:
            itens = sorted(dados["data"], key=lambda d: d["index"])
            if [x["index"] for x in itens] != list(range(len(textos))):
                raise ValueError
            vetores = [item["embedding"] for item in itens]
            if any(len(v) != self.dimensao or any(type(n) not in (float, int) or not math.isfinite(n) for n in v) for v in vetores):
                raise ValueError
            if any(not any(n != 0 for n in v) for v in vetores):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise ErroServico("OpenAI retornou embeddings incompatíveis") from None
        return vetores

    def transcrever(self, caminho):
        from src.seguranca import FORMATOS_AUDIO, validar_arquivo
        entrada = validar_arquivo(caminho, FORMATOS_AUDIO, 20)
        modelo = self.cfg["multimodal"]["stt_modelo"]
        idioma = {"languages[]": "pt"} if modelo == "gpt-transcribe" else {"language": "pt"}
        with entrada.open("rb") as arquivo:
            dados = self._requisitar("/audio/transcriptions", {"model": modelo, **idioma}, tokens=512,
                                     multipart={"file": (entrada.name, arquivo)})
        texto = dados.get("text")
        if not isinstance(texto, str) or not texto.strip():
            raise ErroServico("Transcrição vazia ou inválida")
        self.chamadas[-1]["reserva_nota"] = "Áudio: teto por chamadas e bytes; tokens de entrada não conhecidos antes da transcrição."
        return texto

    def ler_pagina(self, caminho):
        import base64
        import io
        from PIL import Image
        from src.visao import PROMPT_OCR
        with Image.open(caminho) as imagem:
            imagem = imagem.convert("RGB")
            imagem.thumbnail((1024, 1024))
            buffer = io.BytesIO()
            imagem.save(buffer, format="JPEG", quality=85)
        url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
        mensagens = [{"role": "system", "content": PROMPT_OCR},
                     {"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]}]
        payload = _payload(mensagens, self.cfg["multimodal"]["ocr_modelo"], self.conf, "openai")
        dados = self._requisitar("/chat/completions", payload, tokens=8192 + self.conf["max_tokens"] + 512)
        try:
            escolha = dados["choices"][0]
            texto = escolha["message"]["content"]
            if escolha.get("finish_reason") == "length" or not isinstance(texto, str) or not texto.strip():
                raise ValueError
        except (KeyError, IndexError, TypeError, ValueError):
            raise ErroServico("OCR vazio, truncado ou inválido") from None
        self.chamadas[-1]["reserva_nota"] = "Imagem limitada a 1024px; reserva de 8192 tokens para imagem, distinta do uso medido."
        return texto


class ClienteSimulado:
    """Somente demonstração local; vetores de hashing não são embeddings de modelo."""

    simulado = True
    modelo = "simulacao-local-identificada"
    modelo_embeddings = "simulacao-hashing-nao-modelo"
    dimensao = 256

    def __init__(self, *, orcamento=None):
        self.orcamento = orcamento or Orcamento()
        self.chamadas = []
        self.metadados = self.chamadas
        self.saidas_estruturadas = []

    def embeddings(self, textos):
        import hashlib
        import re
        self.orcamento.reservar(sum(len(t.encode("utf-8")) for t in textos) + 512)
        resultado = []
        for texto in textos:
            vetor = [0.0] * self.dimensao
            for palavra in re.findall(r"\w+", texto.casefold()):
                pos = int(hashlib.sha256(palavra.encode()).hexdigest()[:8], 16) % self.dimensao
                vetor[pos] += 1.0
            resultado.append(vetor)
        self.chamadas.append({"endpoint": "embeddings", "simulada": True, "modelo": self.modelo_embeddings})
        return resultado

    def gerar_json(self, sistema, conteudo, esquema, *, nome="resposta"):
        self.orcamento.reservar(len(conteudo.encode("utf-8")) + 512)
        self.chamadas.append({"endpoint": nome, "simulada": True, "modelo": self.modelo,
                              "tokens_entrada": None, "tokens_saida": None, "custo_usd": None})
        # Handlers específicos serão ligados aos contratos locais; nunca leem gabaritos.
        from .simulacao import gerar
        objeto = gerar(nome, conteudo, esquema)
        self.saidas_estruturadas.append({"etapa": nome, "objeto": objeto, "simulada": True})
        return objeto
