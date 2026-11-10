"""Üç modele aynı soruyu sorar: DeepSeek, ChatGPT (OpenAI) ve Claude Opus (Anthropic)."""

from __future__ import annotations

import os

from . import ayarlar


def anahtar_var(kod: str) -> bool:
    return bool(os.environ.get(ayarlar.MODELLER[kod]["anahtar"]))


def model_adi(kod: str) -> str:
    m = ayarlar.MODELLER[kod]
    return os.environ.get(m["model_degiskeni"]) or m["varsayilan_model"]


def _openai_uyumlu(kod: str, sistem: str, mesaj: str) -> tuple[str, dict]:
    from openai import OpenAI

    m = ayarlar.MODELLER[kod]
    adres = ayarlar.DEEPSEEK_ADRES if kod == "deepseek" else None
    istemci = OpenAI(api_key=os.environ[m["anahtar"]], base_url=adres, timeout=900)
    cevap = istemci.chat.completions.create(
        model=model_adi(kod),
        messages=[{"role": "system", "content": sistem}, {"role": "user", "content": mesaj}],
    )
    k = cevap.usage
    kullanim = {"girdi": getattr(k, "prompt_tokens", None), "cikti": getattr(k, "completion_tokens", None)} if k else {}
    return cevap.choices[0].message.content or "", kullanim


def _claude(sistem: str, mesaj: str) -> tuple[str, dict]:
    import anthropic

    istemci = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=900)
    # Uzun düşünme süresinde zaman aşımı olmasın diye akışla alınır.
    # Yedek modele geçiş (fallbacks) bilerek kullanılmaz: yarışta cevabı başka bir modelin vermesi kıyası bozar.
    with istemci.messages.stream(
        model=model_adi("claude"),
        max_tokens=32000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=sistem,
        messages=[{"role": "user", "content": mesaj}],
    ) as akis:
        cevap = akis.get_final_message()
    if cevap.stop_reason == "refusal":
        raise RuntimeError(f"Claude cevap vermeyi reddetti: {getattr(cevap, 'stop_details', None)}")
    metin = "".join(b.text for b in cevap.content if b.type == "text")
    return metin, {"girdi": cevap.usage.input_tokens, "cikti": cevap.usage.output_tokens}


def sor(kod: str, sistem: str, mesaj: str) -> tuple[str, dict]:
    """(cevap metni, token kullanımı)"""
    if kod == "claude":
        return _claude(sistem, mesaj)
    return _openai_uyumlu(kod, sistem, mesaj)
