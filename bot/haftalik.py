"""Haftalık değerlendirme: her cuma gecesi, ABD borsası kapandıktan sonra, her portföy için modeline o haftanın
kayıtlarını verip kısa bir değerlendirme yazdırır. Rakamları program hesaplar; model yalnızca anlatır.

Model her cuma yalnızca o haftanın kayıtlarını okur; geçmiş haftalar kendi özetleriyle temsil edilir.
Böylece soru büyüklüğü zamanla artmaz."""

from __future__ import annotations

import datetime as dt
import json

from . import ayarlar, talimat
from .veri import ISTANBUL, NEW_YORK

KAPANIS_SONRASI = dt.time(16, 15)    # New York saati; cuma bundan sonra hafta kapanmış sayılır
EN_FAZLA_DENEME = 3


def _satirlar(yol):
    try:
        return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]
    except OSError:
        return []


def son_kapanis(simdi: dt.datetime) -> dt.datetime:
    """Şu andan önceki en son 'cuma ABD kapanışı sonrası' anı (UTC)."""
    ny = simdi.astimezone(NEW_YORK)
    gun = ny.date() - dt.timedelta(days=(ny.weekday() - 4) % 7)
    an = dt.datetime.combine(gun, KAPANIS_SONRASI, tzinfo=NEW_YORK)
    if an > ny:
        an -= dt.timedelta(days=7)
    return an.astimezone(dt.timezone.utc)


def kayitlar(klasor) -> list[dict]:
    return _satirlar(klasor / "haftalik.jsonl")


def son_ozet(klasor) -> dict | None:
    for k in reversed(kayitlar(klasor)):
        if k.get("ozet") and not k.get("hata"):
            return k
    return None


def bekliyor_mu(klasor, portfoy: dict | None, simdi: dt.datetime) -> str | None:
    """Bu portföyün yazılmamış haftalık değerlendirmesi varsa haftanın kimliği (cuma tarihi), yoksa None."""
    if not portfoy:
        return None
    kapanis = son_kapanis(simdi)
    if dt.datetime.fromisoformat(portfoy["baslangic"]) >= kapanis:
        return None   # portföy bu kapanıştan sonra başladı
    hafta = kapanis.astimezone(NEW_YORK).date().isoformat()
    bu_hafta = [k for k in kayitlar(klasor) if k.get("hafta") == hafta]
    if any(not k.get("hata") for k in bu_hafta) or len(bu_hafta) >= EN_FAZLA_DENEME:
        return None
    return hafta


def _tr(iso):
    return dt.datetime.fromisoformat(iso).astimezone(ISTANBUL).strftime("%d.%m %H:%M")


def _kiyas_degisimi(degerler, bas_iso, son_kiyas):
    onceki = {}
    for d in degerler:
        if d["zaman"] <= bas_iso:
            onceki = d.get("kiyaslar") or onceki
    if not onceki:
        onceki = {ad: ayarlar.BASLANGIC_NAKIT_TL for ad in son_kiyas}
    return {ad: round((v / onceki[ad] - 1) * 100, 2) for ad, v in son_kiyas.items() if onceki.get(ad)}


def hazirla(klasor, portfoy_kodu, portfoy, hafiza, deger_son, son_kiyas, degerler, simdi, hafta):
    """(sistem, mesaj, kayıt taslağı)"""
    tanim = ayarlar.PORTFOYLER[portfoy_kodu]
    onceki = son_ozet(klasor)
    bas = onceki["son"] if onceki else portfoy["baslangic"]
    son = simdi.isoformat()
    # Dönem başı: önceki değerlendirmenin bitiş değeri; ilk haftada başlangıç sermayesi.
    deger_bas = onceki["deger_son"] if onceki else ayarlar.BASLANGIC_NAKIT_TL
    degisim = deger_son - deger_bas
    kiyas = _kiyas_degisimi(degerler, bas, son_kiyas)

    # İlk haftada portföyün ilk turu (zamanı başlangıçla aynı) da dahil edilir.
    alt = bas if onceki else ""
    islemler = {}
    for i in _satirlar(klasor / "islemler.jsonl"):
        if alt < i["zaman"] <= son:
            islemler.setdefault(i["zaman"], []).append(i)
    turlar = []
    for k in _satirlar(klasor / "kararlar.jsonl"):
        if not (alt < k["zaman"] <= son) or k.get("hata"):
            continue
        satir = [f"{_tr(k['zaman'])} — {k.get('ozet') or '(özet yok)'}"]
        for i in islemler.get(k["zaman"], []):
            satir.append(f"    {i['sonuc'][:160]}" + (f" | neden: {i['neden'][:220]}" if i.get("neden") else ""))
        turlar.append("\n".join(satir))

    pozisyonlar = ", ".join(sorted(portfoy["pozisyonlar"])) or "yok (tamamı nakit)"
    sistem = f"""{talimat.ROL}

Şimdi haftalık değerlendirme zamanı. Yatırımcı telefonundaki uygulamada portföyüne baktığında en üstte bu
değerlendirmeyi okuyacak. Ona kısa bir brifing veriyormuş gibi, birinci tekil şahısla yaz: bu hafta ne düşündün,
ne yaptın, sonuç ne oldu, neyi doğru neyi yanlış yaptın, gelecek hafta neye dikkat edeceksin.
Kurallar:
- Rakam olarak YALNIZCA mesajda verilen gerçek rakamları kullan; başka kâr/zarar rakamı uydurma.
- Sonuç kötüyse dürüstçe söyle; olduğundan iyi gösterme.
- En fazla {ayarlar.HAFTALIK_SINIRI} karakter, tek paragraf, sade Türkçe.
Cevabını SADECE şu biçimde, geçerli tek bir JSON nesnesi olarak ver:
{{"haftalik_ozet": "değerlendirme metni"}}"""
    kiyas_metni = ", ".join(f"{ad} {talimat._yuzde(v)}%" for ad, v in kiyas.items()) or "veri yok"
    kurgu = (hafiza.get("kurgu") or {}).get("metin") or "(yazılmamış)"
    mesaj = f"""PORTFÖY: {tanim['ad']}
DÖNEM: {_tr(bas)} - {_tr(son)} (İstanbul saati)

=== GERÇEK SONUÇ (program hesapladı) ===
Dönem başı değer: {deger_bas:,.2f} TL
Dönem sonu değer: {deger_son:,.2f} TL
Değişim: {degisim:+,.2f} TL ({talimat._yuzde((deger_son / deger_bas - 1) * 100 if deger_bas else 0)}%)
Başlangıçtan bu yana: {talimat._yuzde((deger_son / ayarlar.BASLANGIC_NAKIT_TL - 1) * 100)}%
Aynı dönemde kıyaslar (al ve bekle): {kiyas_metni}
Şu anki varlıklar: {pozisyonlar}

=== BAŞLANGIÇ KURGUN ===
{kurgu}

=== GEÇEN HAFTAKİ DEĞERLENDİRMEN ===
{onceki['ozet'] if onceki else '(ilk hafta)'}

=== BU DÖNEMDEKİ TURLARIN ({len(turlar)} tur) ===
{chr(10).join(turlar) if turlar else '(bu dönemde tur yok)'}

Haftalık değerlendirmeni JSON olarak ver."""
    kayit = {"hafta": hafta, "bas": bas, "son": son, "deger_bas": round(deger_bas, 2), "deger_son": round(deger_son, 2),
             "degisim_tl": round(degisim, 2),
             "degisim_yuzde": round((deger_son / deger_bas - 1) * 100, 2) if deger_bas else 0.0,
             "kiyaslar": kiyas, "tur_sayisi": len(turlar)}
    return sistem, mesaj, kayit


def ozeti_ayikla(cevap: str) -> str:
    v = talimat.ayristir(cevap)
    metin = str(v.get("haftalik_ozet") or "").strip()
    if not metin:
        raise ValueError("haftalik_ozet boş")
    return metin[: ayarlar.HAFTALIK_SINIRI + 200]
