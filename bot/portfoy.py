"""Hayali portföy: nakit, pozisyonlar, alış/satış ve değerleme. Kesirli adet serbesttir."""

from __future__ import annotations

from . import ayarlar


def yeni_portfoy(zaman: str) -> dict:
    return {"baslangic": zaman, "nakit_tl": ayarlar.BASLANGIC_NAKIT_TL, "pozisyonlar": {},
            "odenen_komisyon_tl": 0.0}


def degerle(portfoy: dict, fiyatlar: dict) -> tuple[float, list[dict]]:
    toplam = portfoy["nakit_tl"]
    satirlar = []
    for s, p in portfoy["pozisyonlar"].items():
        f = fiyatlar.get(s, {}).get("fiyat_tl")
        if f is None:
            f = p.get("son_fiyat_tl", p["maliyet_tl"] / p["adet"])
        else:
            p["son_fiyat_tl"] = f
        deger = p["adet"] * f
        toplam += deger
        satirlar.append({"sembol": s, "adet": p["adet"], "deger_tl": deger, "maliyet_tl": p["maliyet_tl"],
                         "kar_%": (deger / p["maliyet_tl"] - 1) * 100 if p["maliyet_tl"] else 0.0})
    return toplam, satirlar


def al(portfoy: dict, sembol: str, tutar_tl: float, veri: dict | None) -> str:
    if not veri or veri.get("fiyat_tl") is None:
        return f"REDDEDİLDİ: {sembol} için fiyat bulunamadı (sembol yanlış olabilir)."
    if not veri.get("islem", True):
        return f"REDDEDİLDİ: {sembol} bir endekstir, doğrudan alınamaz (ör. SPY, QQQ gibi fon kullan)."
    if not veri["acik"]:
        return f"REDDEDİLDİ: {sembol} piyasası şu an kapalı (son fiyat {veri['zaman']})."
    try:
        tutar_tl = float(tutar_tl)
    except (TypeError, ValueError):
        return f"REDDEDİLDİ: {sembol} alış tutarı geçersiz."
    azami = portfoy["nakit_tl"] / (1 + ayarlar.KOMISYON_ORANI)
    tutar_tl = min(tutar_tl, azami)
    if tutar_tl < ayarlar.MIN_ISLEM_TL:
        return f"REDDEDİLDİ: {sembol} alışı için yeterli nakit yok veya tutar çok küçük."
    komisyon = tutar_tl * ayarlar.KOMISYON_ORANI
    adet = tutar_tl / veri["fiyat_tl"]
    portfoy["nakit_tl"] -= tutar_tl + komisyon
    portfoy["odenen_komisyon_tl"] += komisyon
    p = portfoy["pozisyonlar"].setdefault(sembol, {"adet": 0.0, "maliyet_tl": 0.0})
    p["adet"] += adet
    p["maliyet_tl"] += tutar_tl + komisyon
    p["son_fiyat_tl"] = veri["fiyat_tl"]
    return (f"ALINDI: {sembol} {adet:.6g} adet, birim {veri['fiyat_tl']:.4f} TL, "
            f"tutar {tutar_tl:.2f} TL + komisyon {komisyon:.2f} TL")


def sat(portfoy: dict, sembol: str, yuzde: float, veri: dict | None) -> str:
    p = portfoy["pozisyonlar"].get(sembol)
    if not p:
        return f"REDDEDİLDİ: {sembol} portföyde yok."
    if not veri or veri.get("fiyat_tl") is None:
        return f"REDDEDİLDİ: {sembol} için fiyat bulunamadı."
    if not veri["acik"]:
        return f"REDDEDİLDİ: {sembol} piyasası şu an kapalı (son fiyat {veri['zaman']})."
    try:
        oran = max(0.0, min(float(yuzde), 100.0)) / 100
    except (TypeError, ValueError):
        return f"REDDEDİLDİ: {sembol} satış yüzdesi geçersiz."
    if oran <= 0:
        return f"REDDEDİLDİ: {sembol} satış yüzdesi 0."
    adet = p["adet"] * oran
    brut = adet * veri["fiyat_tl"]
    if brut < ayarlar.MIN_ISLEM_TL and oran < 1:
        return f"REDDEDİLDİ: {sembol} satışı çok küçük."
    komisyon = brut * ayarlar.KOMISYON_ORANI
    maliyet_payi = p["maliyet_tl"] * oran
    kar = brut - komisyon - maliyet_payi
    portfoy["nakit_tl"] += brut - komisyon
    portfoy["odenen_komisyon_tl"] += komisyon
    if oran >= 0.9999:
        del portfoy["pozisyonlar"][sembol]
    else:
        p["adet"] -= adet
        p["maliyet_tl"] -= maliyet_payi
    return (f"SATILDI: {sembol} {adet:.6g} adet (%{oran*100:.0f}), birim {veri['fiyat_tl']:.4f} TL, "
            f"eline geçen {brut - komisyon:.2f} TL, kâr/zarar {kar:+.2f} TL")
