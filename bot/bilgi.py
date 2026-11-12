"""Temel veriler (F/K, PD/DD, piyasa değeri, temettü) ve haber başlıkları.

Üç modele de aynı bilgi verilir; modellerin kendi internet araması kullanılmaz (adil kıyas ve sabit maliyet için).
Her şey hata toleranslıdır: bir kaynak cevap vermezse o bölüm boş kalır, tur yine çalışır."""

from __future__ import annotations

import datetime as dt
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime

from . import ayarlar
from .veri import ISTANBUL

_TEMEL_DOSYA = ayarlar.DURUM / "temel.json"
HABER_SAAT = 72                 # bundan eski haber gösterilmez
SEMBOL_BASINA_HABER = 2
GENEL_HABER = 4                 # her genel kaynaktan


def temel_uygun(sembol: str) -> bool:
    """Hisse ve fonlar için; döviz, kripto, vadeli ve endeks için temel veri yoktur."""
    s = sembol.upper()
    return not (s.endswith("=X") or s.endswith("=F") or s.startswith("^") or s.endswith("-USD"))


def _temel_cek(sembol: str) -> dict | None:
    import yfinance as yf

    try:
        i = yf.Ticker(sembol).info or {}
    except Exception:
        return None
    if not i:
        return None
    fk, fk_tur = i.get("trailingPE"), "son 12 ay"
    if not fk:
        fk, fk_tur = i.get("forwardPE"), "ileriye dönük"
    return {"ad": i.get("shortName") or i.get("longName"), "sektor": i.get("sector"), "tur": i.get("quoteType"),
            "fk": round(fk, 1) if isinstance(fk, (int, float)) else None, "fk_tur": fk_tur,
            "pddd": round(i["priceToBook"], 2) if isinstance(i.get("priceToBook"), (int, float)) else None,
            "piyasa_degeri": i.get("marketCap") or i.get("totalAssets"), "para_birimi": i.get("currency"),
            "temettu_%": i.get("dividendYield")}


def temel(semboller) -> dict[str, dict]:
    """Günde bir kez çekilir ve durum/temel.json'da saklanır."""
    try:
        kayit = json.loads(_TEMEL_DOSYA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        kayit = {}
    bugun = dt.datetime.now(ISTANBUL).date().isoformat()
    gerekli = [s for s in dict.fromkeys(semboller) if temel_uygun(s) and kayit.get(s, {}).get("tarih") != bugun]
    if gerekli:
        with ThreadPoolExecutor(max_workers=8) as havuz:
            for s, v in zip(gerekli, havuz.map(_temel_cek, gerekli)):
                if v:
                    kayit[s] = {"tarih": bugun, "v": v}
        _TEMEL_DOSYA.parent.mkdir(parents=True, exist_ok=True)
        _TEMEL_DOSYA.write_text(json.dumps(kayit, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    return {s: kayit[s]["v"] for s in semboller if s in kayit}


# ---------- haberler ----------

def _yeni_mi(zaman: dt.datetime | None, simdi: dt.datetime) -> bool:
    return zaman is not None and (simdi - zaman).total_seconds() <= HABER_SAAT * 3600


def _yahoo(sembol: str, simdi: dt.datetime, adet: int, ilgili: bool = True) -> list[dict]:
    import yfinance as yf

    try:
        haberler = yf.Ticker(sembol).news or []
    except Exception:
        return []
    sonuc = []
    for h in haberler:
        c = h.get("content", h)
        baslik = (c.get("title") or "").strip()
        try:
            zaman = dt.datetime.fromisoformat(str(c.get("pubDate")).replace("Z", "+00:00"))
        except ValueError:
            zaman = None
        if not baslik or not _yeni_mi(zaman, simdi):
            continue
        # Hisse haberlerinde Yahoo bazen ilgisiz haber döndürür: sembolün etiketlendiği haberler alınır.
        etiketler = [t.get("symbol") for t in ((c.get("finance") or {}).get("stockTickers") or [])]
        if ilgili and etiketler and sembol not in etiketler:
            continue
        kaynak = (c.get("provider") or {}).get("displayName", "") if isinstance(c.get("provider"), dict) else ""
        sonuc.append({"zaman": zaman, "baslik": baslik, "kaynak": kaynak})
        if len(sonuc) >= adet:
            break
    return sonuc


def _google(sorgu: str, simdi: dt.datetime, adet: int) -> list[dict]:
    """Google Haberler RSS (Türkçe). Türk hisseleri ve Türkiye ekonomisi için."""
    adres = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(sorgu + " when:3d") +
             "&hl=tr&gl=TR&ceid=TR:tr")
    try:
        istek = urllib.request.Request(adres, headers={"User-Agent": "Mozilla/5.0 (yatirim-yarisi)"})
        kok = ET.fromstring(urllib.request.urlopen(istek, timeout=15).read())
    except Exception:
        return []
    sonuc = []
    for it in kok.findall(".//item"):
        baslik = (it.findtext("title") or "").strip()
        kaynak = (it.findtext("source") or "").strip()
        if kaynak and baslik.endswith(" - " + kaynak):
            baslik = baslik[: -len(kaynak) - 3]
        try:
            zaman = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            zaman = None
        if baslik and _yeni_mi(zaman, simdi):
            sonuc.append({"zaman": zaman, "baslik": baslik, "kaynak": kaynak})
    sonuc.sort(key=lambda h: h["zaman"], reverse=True)
    return sonuc[:adet]


def _sembol_haberi(sembol: str, simdi: dt.datetime) -> list[dict]:
    if sembol.endswith(".IS"):
        return _google(f'"{sembol[:-3]}" hisse', simdi, SEMBOL_BASINA_HABER)
    if sembol.startswith("^"):
        return []
    # Fon, kripto, döviz ve emtiada Yahoo etiketi tutarsız: etiket süzgeci yalnızca hisselerde.
    hisse = not (sembol.endswith("=X") or sembol.endswith("=F") or sembol.endswith("-USD"))
    return _yahoo(sembol, simdi, SEMBOL_BASINA_HABER, ilgili=hisse)


GENEL_KAYNAKLAR = [
    ("ABD ve dünya piyasaları", lambda simdi: _yahoo("^GSPC", simdi, GENEL_HABER, ilgili=False)),
    ("Borsa İstanbul", lambda simdi: _google("Borsa İstanbul BIST", simdi, GENEL_HABER)),
    ("Türkiye ekonomisi", lambda simdi: _google("Merkez Bankası faiz enflasyon dolar TL", simdi, GENEL_HABER)),
]


def haberler(semboller, simdi: dt.datetime) -> dict:
    """{'genel': {başlık: [haber]}, 'semboller': {sembol: [haber]}} — tek turda tüm portföyler için bir kez."""
    semboller = list(dict.fromkeys(semboller))
    with ThreadPoolExecutor(max_workers=8) as havuz:
        genel = list(havuz.map(lambda k: (k[0], k[1](simdi)), GENEL_KAYNAKLAR))
        ozel = list(havuz.map(lambda s: _sembol_haberi(s, simdi), semboller))
    return {"genel": {ad: h for ad, h in genel if h}, "semboller": {s: h for s, h in zip(semboller, ozel) if h}}


def haber_satiri(h: dict) -> str:
    z = h["zaman"].astimezone(ISTANBUL).strftime("%d.%m %H:%M") if h.get("zaman") else ""
    return f"[{z}] {h['baslik'][:160]}" + (f" ({h['kaynak']})" if h.get("kaynak") else "")
