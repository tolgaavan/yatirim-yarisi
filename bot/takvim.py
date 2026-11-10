"""Her portföyün bir sonraki kontrol zamanı. Saati model seçer; program portföy türünün kurallarına uydurur.

Tüm zamanlar İstanbul saatiyle hesaplanır, ISO metni olarak saklanır."""

from __future__ import annotations

import datetime as dt
import re

from . import ayarlar
from .veri import ISTANBUL

EN_AZ_ARA = dt.timedelta(minutes=30)
KISA_VARSAYILAN_ARA = dt.timedelta(hours=3)
KISA_EN_UZAK = dt.timedelta(days=7)
UZUN_EN_UZAK = {"uzun": dt.timedelta(days=35), "orta": dt.timedelta(days=14)}
KISA_SABAH = dt.time(10, 0)


def ayristir(metin) -> dt.datetime | None:
    """'2026-11-14 16:30' gibi metni İstanbul saatli zamana çevirir. Okunamazsa None."""
    if not metin:
        return None
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})[ T](\d{1,2})[:.](\d{2})", str(metin))
    if not m:
        return None
    try:
        y, a, g, s, d = (int(x) for x in m.groups())
        return dt.datetime(y, a, g, s, d, tzinfo=ISTANBUL)
    except ValueError:
        return None


def _saat(metin: str) -> dt.time:
    s, d = metin.split(":")
    return dt.time(int(s), int(d))


def sonraki(portfoy_kodu: str, istenen, simdi: dt.datetime, tur_zamanlari: list[str]) -> tuple[dt.datetime, str]:
    """(kontrol zamanı, varsa düzeltme açıklaması). tur_zamanlari: bu portföyün geçmiş tur zamanları (ISO)."""
    tanim = ayarlar.PORTFOYLER[portfoy_kodu]
    simdi = simdi.astimezone(ISTANBUL)
    hedef = ayristir(istenen)
    not_ = ""

    if tanim["tip"] == "kisa":
        if hedef is None:
            hedef, not_ = simdi + KISA_VARSAYILAN_ARA, "zaman okunamadı, 3 saat sonrası seçildi"
        if hedef < simdi + EN_AZ_ARA:
            hedef, not_ = simdi + EN_AZ_ARA, "en az 30 dakika sonrası olmalı"
        if hedef > simdi + KISA_EN_UZAK:
            hedef, not_ = simdi + KISA_EN_UZAK, "en fazla 7 gün sonrası seçilebilir"
        gunluk = {}
        for z in tur_zamanlari:
            g = dt.datetime.fromisoformat(z).astimezone(ISTANBUL).date()
            gunluk[g] = gunluk.get(g, 0) + 1
        while gunluk.get(hedef.date(), 0) >= ayarlar.KISA_GUNLUK_SINIR:
            hedef = dt.datetime.combine(hedef.date() + dt.timedelta(days=1), KISA_SABAH, tzinfo=ISTANBUL)
            not_ = f"o gün için {ayarlar.KISA_GUNLUK_SINIR} kontrol sınırı doldu, ertesi gün sabaha alındı"
        return hedef, not_

    gunler = tanim["gunler"]
    if hedef is None:
        hedef = dt.datetime.combine(simdi.date(), _saat(ayarlar.VARSAYILAN_SAAT), tzinfo=ISTANBUL)
        not_ = f"zaman okunamadı, saat {ayarlar.VARSAYILAN_SAAT} seçildi"
    # Aynı gün ikinci kez bakılmaz: en erken ertesi gün.
    if hedef.date() <= simdi.date():
        hedef = dt.datetime.combine(simdi.date() + dt.timedelta(days=1), hedef.timetz())
    duzeltildi = False
    while hedef.weekday() not in gunler:
        hedef += dt.timedelta(days=1)
        duzeltildi = True
    if duzeltildi and not not_:
        not_ = f"bu portföy yalnızca {tanim['kontrol']} kontrol edilir; ilk uygun güne alındı"
    sinir = simdi + UZUN_EN_UZAK[tanim["tip"]]
    while hedef > sinir:
        hedef -= dt.timedelta(days=7)
        not_ = "çok uzak bir tarih seçildi, öne alındı"
    return hedef, not_
