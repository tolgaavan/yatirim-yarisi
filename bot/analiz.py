"""Fiyat serilerinden teknik göstergeler: program hesaplar, model yalnızca sonucu görür.

Ek veri indirmez; veri.fiyatlar'ın zaten indirdiği 6 aylık günlük ve 5 günlük 15 dakikalık seriler kullanılır."""

from __future__ import annotations

import math


def _yuvarla(x, basamak=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), basamak)


def rsi(kapanislar, n: int = 14):
    """Wilder RSI. Yeterli veri yoksa None."""
    k = [float(x) for x in kapanislar]
    if len(k) <= n:
        return None
    farklar = [b - a for a, b in zip(k, k[1:])]
    kazanc = sum(max(f, 0) for f in farklar[:n]) / n
    kayip = sum(max(-f, 0) for f in farklar[:n]) / n
    for f in farklar[n:]:
        kazanc = (kazanc * (n - 1) + max(f, 0)) / n
        kayip = (kayip * (n - 1) + max(-f, 0)) / n
    if kayip == 0:
        return 100.0 if kazanc > 0 else 50.0
    return 100 - 100 / (1 + kazanc / kayip)


def _uzaklik(fiyat, deger):
    return (fiyat / deger - 1) * 100 if deger else None


def gunluk_teknik(kapanislar, fiyat: float) -> dict:
    """Günlük kapanışlardan (en eski -> en yeni) göstergeler; yüzdeler fiyatın o seviyeye uzaklığıdır."""
    k = [float(x) for x in kapanislar]
    if len(k) < 15:
        return {}
    sonuc = {"rsi14": _yuvarla(rsi(k + [fiyat]))}
    if len(k) >= 20:
        sonuc["ort20_%"] = _yuvarla(_uzaklik(fiyat, sum(k[-20:]) / 20))
    if len(k) >= 50:
        sonuc["ort50_%"] = _yuvarla(_uzaklik(fiyat, sum(k[-50:]) / 50))
    sonuc["zirve_%"] = _yuvarla(_uzaklik(fiyat, max(k + [fiyat])))
    sonuc["dip_%"] = _yuvarla(_uzaklik(fiyat, min(k + [fiyat])))
    getiriler = [b / a - 1 for a, b in zip(k[-21:], k[-20:]) if a]
    if len(getiriler) >= 10:
        ort = sum(getiriler) / len(getiriler)
        std = math.sqrt(sum((g - ort) ** 2 for g in getiriler) / (len(getiriler) - 1))
        sonuc["oynaklik_%"] = _yuvarla(std * math.sqrt(252) * 100, 0)
    return sonuc


def _kisalt(x):
    """Fiyatı 5 anlamlı basamağa indirir (token tasarrufu)."""
    x = float(x)
    if x == 0:
        return 0
    basamak = max(0, 4 - int(math.floor(math.log10(abs(x)))))
    return round(x, basamak)


def gun_ici(tablo, cubuk: int = 16) -> dict:
    """15 dakikalık tablodan (Close, Volume) kısa vade özeti. tablo: pandas DataFrame, zaman sıralı."""
    try:
        tablo = tablo.dropna(subset=["Close"])
    except Exception:
        return {}
    if tablo is None or len(tablo) < 5:
        return {}
    kapanis = [float(x) for x in tablo["Close"]]
    son_gun = tablo.index[-1].date()
    bugun = tablo[[i.date() == son_gun for i in tablo.index]]
    sonuc = {
        "seri": [_kisalt(x) for x in kapanis[-cubuk:]],
        "acilis": _kisalt(bugun["Close"].iloc[0]) if "Open" not in bugun else _kisalt(bugun["Open"].iloc[0]),
        "yuksek": _kisalt(bugun["High"].max() if "High" in bugun else bugun["Close"].max()),
        "dusuk": _kisalt(bugun["Low"].min() if "Low" in bugun else bugun["Close"].min()),
        "rsi14": _yuvarla(rsi(kapanis)),
    }
    if len(kapanis) >= 20:
        sonuc["ort20_%"] = _yuvarla(_uzaklik(kapanis[-1], sum(kapanis[-20:]) / 20), 2)
    if "Volume" in tablo:
        hacim = [float(v) for v in tablo["Volume"].fillna(0)]
        dolu = [v for v in hacim[:-4] if v > 0]
        son = [v for v in hacim[-4:]]
        if dolu and sum(son) > 0:
            sonuc["hacim_kat"] = _yuvarla((sum(son) / 4) / (sum(dolu) / len(dolu)), 1)
    return sonuc
