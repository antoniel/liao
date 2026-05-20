"""Camada de linguagem (Claude Haiku) para explicar o score e recomendar gasto.

Honesta: a IA NAO calcula score (isso e o PCA/clustering/forecast). Ela so traduz
os numeros em texto e prioridade de investimento. Sem ANTHROPIC_API_KEY, cai num
gerador deterministico (mesma estrutura, custo zero) para a demo nunca quebrar.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import io

MODELO = "claude-haiku-4-5"
CACHE = io.DATA_PROCESSED / "ai_cache.json"
_ROTULO = {"seca": "seca", "enchente": "enchentes", "calor": "calor extremo"}


def _cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def _salvar_cache(c: dict) -> None:
    CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=0))


def _maior_risco(sub: dict[str, float]) -> tuple[str, float]:
    item = max(sub.items(), key=lambda kv: kv[1])
    return _ROTULO[item[0]], item[1]


def _fallback_explicacao(nome: str, sub: dict, arquetipo: str, tendencia: str) -> str:
    risco, val = _maior_risco(sub)
    return (
        f"{nome} se enquadra no perfil '{arquetipo}'. O maior fator de risco e {risco} "
        f"({val:.0%}). Tendencia historica: {tendencia.lower()}. Prioridade de investimento "
        f"orientada a mitigar {risco}."
    )


def _fallback_recomendacao(nome: str, valor: float, sub: dict) -> str:
    risco, _ = _maior_risco(sub)
    acao = {
        "seca": "infraestrutura hidrica (cisternas, poços, adutoras)",
        "enchentes": "drenagem urbana e contencao de cheias",
        "calor extremo": "arborizacao, sombreamento e alerta de calor",
    }[risco]
    return f"Alocar R$ {valor:,.0f} prioritariamente em {acao}, principal vetor de risco de {nome}."


def _cliente():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from anthropic import Anthropic

        return Anthropic()
    except Exception:
        return None


def _gerar(prompt: str, max_tokens: int) -> str | None:
    cliente = _cliente()
    if cliente is None:
        return None
    try:
        msg = cliente.messages.create(
            model=MODELO, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception:
        return None


def explicar_municipio(nome: str, sub: dict, arquetipo: str, tendencia: str) -> str:
    chave = f"exp::{nome}"
    cache = _cache()
    if chave in cache:
        return cache[chave]
    prompt = (
        f"Voce e especialista em resiliencia climatica no Brasil. Municipio: {nome} (Bahia).\n"
        f"Indices [0-1]: seca {sub['seca']:.2f}, enchente {sub['enchente']:.2f}, calor {sub['calor']:.2f}.\n"
        f"Perfil: {arquetipo}. Tendencia historica: {tendencia}.\n"
        "Em 2 frases, explique o perfil de risco citando so o(s) fator(es) dominante(s). "
        "Seja direto e honesto sobre incertezas. Portugues."
    )
    texto = _gerar(prompt, 160) or _fallback_explicacao(nome, sub, arquetipo, tendencia)
    cache[chave] = texto
    _salvar_cache(cache)
    return texto


def recomendar_gasto(nome: str, valor: float, sub: dict) -> str:
    prompt = (
        f"Planejador de resiliencia climatica. Municipio: {nome} (Bahia). "
        f"Orcamento: R$ {valor:,.0f}. Indices: seca {sub['seca']:.2f}, enchente {sub['enchente']:.2f}, "
        f"calor {sub['calor']:.2f}. Em no maximo 2 frases, recomende como alocar, priorizando o maior risco. Portugues."
    )
    return _gerar(prompt, 140) or _fallback_recomendacao(nome, valor, sub)
