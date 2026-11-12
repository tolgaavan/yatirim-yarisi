"""Piyasa verisi (Yahoo Finance) ve piyasa saatleri."""

from __future__ import annotations

import datetime as dt
import json
from zoneinfo import ZoneInfo

from . import analiz, ayarlar

ISTANBUL = ZoneInfo("Europe/Istanbul")
NEW_YORK = ZoneInfo("America/New_York")

_PARA_BIRIMI_DOSYA = ayarlar.DURUM / "para_birimleri.json"


def _para_birimi_tahmini(sembol: str) -> str | None:
    if sembol.endswith(".IS") or sembol.endswith("TRY=X"):
        return "TRY"
    if sembol.endswith("-USD") or sembol.endswith("=F") or sembol.startswith("^"):
        return "USD"
    return None


def islem_yapilabilir(sembol: str) -> bool:
    """^ ile başlayan endeksler doğrudan alınamaz; yalnızca bilgi içindir."""
    return not (sembol.startswith("^") or sembol == "DX-Y.NYB")


def _abd_mi(sembol: str) -> bool:
    """ABD borsasında işlem gören hisse/fon/endeks mi (son eki olmayan semboller)."""
    if sembol in ("^GSPC", "^IXIC", "^DJI", "^VIX", "^TNX"):
        return True
    return not any(c in sembol for c in ".=-^")


def seans_acik(sembol: str, simdi: dt.datetime) -> bool | None:
    """Bilinen piyasalar için seans saatine göre açık mı. Bilinmiyorsa None (yalnızca fiyat tazeliğine bakılır).

    Tatiller burada bilinmez; tatil günü fiyat güncellenmediği için tazelik kontrolü onları yakalar."""
    if sembol.endswith(".IS") or sembol.endswith("TRY=X"):
        t = simdi.astimezone(ISTANBUL)
        return t.weekday() < 5 and dt.time(10, 0) <= t.time() < dt.time(18, 0)
    if _abd_mi(sembol):
        t = simdi.astimezone(NEW_YORK)
        return t.weekday() < 5 and dt.time(9, 30) <= t.time() < dt.time(16, 0)
    return None


def para_birimleri(semboller: list[str]) -> dict[str, str]:
    import yfinance as yf

    try:
        bilinen = json.loads(_PARA_BIRIMI_DOSYA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        bilinen = {}
    degisti = False
    for s in semboller:
        if s in bilinen:
            continue
        pb = None
        try:
            pb = yf.Ticker(s).fast_info["currency"]
        except Exception:
            pb = _para_birimi_tahmini(s)
        if pb:
            bilinen[s] = pb
            degisti = True
    if degisti:
        _PARA_BIRIMI_DOSYA.parent.mkdir(parents=True, exist_ok=True)
        _PARA_BIRIMI_DOSYA.write_text(json.dumps(bilinen, indent=1, sort_keys=True), encoding="utf-8")
    return {s: bilinen[s] for s in semboller if s in bilinen}


def _kur_sembolu(pb: str) -> tuple[str | None, float]:
    """Para biriminden TL'ye çeviren kur sembolü ve alt birim çarpanı."""
    if pb == "TRY":
        return None, 1.0
    if pb == "GBp":
        return "GBPTRY=X", 0.01
    if pb == "ILA":
        return "ILSTRY=X", 0.01
    if pb == "ZAc":
        return "ZARTRY=X", 0.01
    return f"{pb.upper()}TRY=X", 1.0


def _seri(tablo, sembol):
    """Sembolün tablosu (Open, High, Low, Close, Volume); kapanışı olmayan satırlar atılır."""
    try:
        if sembol in tablo.columns.get_level_values(0):
            return tablo[sembol].dropna(subset=["Close"])
    except Exception:
        pass
    return None


def _indir(semboller: list[str], *, period: str, interval: str, deneme: int = 3) -> dict:
    """Sembol -> fiyat tablosu (Close, Volume vb.). Yahoo toplu indirmede bazı sembolleri ara sıra boş döndürür;
    eksik kalanlar birkaç kez yeniden istenir."""
    import time

    import yfinance as yf

    sonuc = {}
    eksik = list(semboller)
    for i in range(deneme):
        if not eksik:
            break
        if i:
            time.sleep(2 * i)
        try:
            tablo = yf.download(eksik, period=period, interval=interval, group_by="ticker", progress=False,
                                threads=len(eksik) > 1, auto_adjust=False, multi_level_index=True)
        except Exception:
            continue
        for s in eksik:
            seri = _seri(tablo, s)
            if seri is not None and not seri.empty:
                sonuc[s] = seri
        eksik = [s for s in eksik if s not in sonuc]
    return sonuc


def fiyatlar(semboller: list[str], simdi: dt.datetime) -> dict[str, dict]:
    """Her sembol için güncel fiyat, değişimler, TL karşılığı, piyasanın açık olup olmadığı ve günlük kapanış serisi.

    acik: şu an işlem yapılabilir mi. piyasa_acik: piyasası açık mı (endeksler için de)."""
    import yfinance as yf

    semboller = sorted(set(semboller))
    if not semboller:
        return {}
    pb = para_birimleri(semboller)
    kurlar = {k for s in semboller if s in pb for k in [_kur_sembolu(pb[s])[0]] if k}
    tumu = sorted(set(semboller) | kurlar)

    gun_ici = _indir(tumu, period="5d", interval="15m")
    gunluk = _indir(tumu, period="6mo", interval="1d")

    ham: dict[str, dict] = {}
    for s in tumu:
        gi_tablo = gun_ici.get(s)
        gi = gi_tablo["Close"] if gi_tablo is not None else None
        gn = gunluk[s]["Close"] if s in gunluk else None
        if (gi is None or gi.empty) and (gn is None or gn.empty):
            continue
        if gi is not None and not gi.empty:
            fiyat = float(gi.iloc[-1])
            zaman = gi.index[-1].to_pydatetime()
        else:
            fiyat = float(gn.iloc[-1])
            zaman = gn.index[-1].to_pydatetime()
        if zaman.tzinfo is None:
            zaman = zaman.replace(tzinfo=dt.timezone.utc)
        yas_dk = (simdi - zaman).total_seconds() / 60

        def degisim(geri: int):
            if gn is None or len(gn) == 0:
                return None
            seri = gn
            # son günlük çubuk bugünse bir önceki kapanışla kıyasla
            if seri.index[-1].date() >= zaman.date():
                seri = seri.iloc[:-1]
            if len(seri) < geri:
                return None
            onceki = float(seri.iloc[-geri])
            return round((fiyat / onceki - 1) * 100, 2) if onceki else None

        seans = seans_acik(s, simdi)
        piyasa_acik = yas_dk <= ayarlar.TAZE_FIYAT_DAKIKA and seans is not False
        ham[s] = {
            "fiyat": fiyat,
            "zaman": zaman.astimezone(dt.timezone.utc).isoformat(timespec="minutes"),
            "piyasa_acik": piyasa_acik,
            "acik": piyasa_acik,
            "gun_%": degisim(1),
            "hafta_%": degisim(5),
            "ay_%": degisim(21),
            "3ay_%": degisim(63),
            "para_birimi": pb.get(s, _para_birimi_tahmini(s) or "?"),
            "seri": [[i.strftime("%Y-%m-%d"), round(float(v), 6)] for i, v in gn.tail(90).items()]
            if gn is not None else [],
            # Göstergeler: son günlük çubuk bugünse dışarıda bırakılır, fiyat ayrıca eklenir.
            "teknik": analiz.gunluk_teknik(
                [float(v) for i, v in gn.items() if i.date() < zaman.date()], fiyat) if gn is not None else {},
            "gun_ici": analiz.gun_ici(gi_tablo) if gi_tablo is not None else {},
        }

    sonuc = {}
    for s in semboller:
        if s not in ham:
            continue
        d = ham[s]
        kur_s, carpan = _kur_sembolu(d["para_birimi"]) if d["para_birimi"] != "?" else (None, None)
        if carpan is None:
            d["fiyat_tl"] = None
        elif kur_s is None:
            d["fiyat_tl"] = d["fiyat"] * carpan
        elif kur_s in ham:
            d["fiyat_tl"] = d["fiyat"] * carpan * ham[kur_s]["fiyat"]
        else:
            d["fiyat_tl"] = None
        d["islem"] = islem_yapilabilir(s)
        if d["fiyat_tl"] is None or not d["islem"]:
            d["acik"] = False
        sonuc[s] = d
    return sonuc
