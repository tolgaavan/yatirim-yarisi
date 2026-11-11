"""Modellere giden talimat (sistem metni) ve her turun mesajı; cevabın ayrıştırılması."""

from __future__ import annotations

import datetime as dt
import json
import re

from . import ayarlar
from .veri import ISTANBUL

_RISK = {
    True: "RİSKLİ: daha yüksek getiri için daha yüksek oynaklığı ve geçici kayıpları kabul edebilirsin.",
    False: "RİSKSİZ (düşük risk): önceliğin sermayeyi korumak ve istikrarlı getiri; büyük kayıp riski taşıyan, "
           "çok oynak varlıklardan kaçın.",
}
_TIP = {
    "uzun": "UZUN VADE (3 ay): 3 aylık sonuca göre değerlendirileceksin.",
    "orta": "ORTA VADE (1 ay): 1 aylık sonuca göre değerlendirileceksin.",
    "kisa": "KISA VADE (al-sat): kısa vadeli fiyat hareketlerinden kazanç ararsın; risk ayrımı yoktur.",
}


def sistem(portfoy_kodu: str) -> str:
    t = ayarlar.PORTFOYLER[portfoy_kodu]
    risk = "" if t["tip"] == "kisa" else "\n" + _RISK[t["riskli"]]
    if t["tip"] == "kisa":
        kontrol = (f"Bu portföye günde en fazla {ayarlar.KISA_GUNLUK_SINIR} kez bakılır; ne zaman bakılacağını sen "
                   "seçersin (en erken 30 dakika sonra). Sınır dolarsa kontrol ertesi sabaha kayar.")
    else:
        kontrol = (f"Bu portföye yalnızca {t['kontrol']} bakılır (günde bir kez). Saatini sen seçersin; "
                   "uygun olmayan bir gün yazarsan ilk uygun güne alınır.")
    return f"""Sen yapay zekâ modellerinin yarıştığı hayali bir yatırım deneyinde bir portföy yöneten yatırımcısın.
Gerçek para yoktur ama işlemlerin gerçek, güncel piyasa fiyatlarından yapılmış sayılır. Amacın portföyün TL
değerini olabildiğince artırmaktır. Sonucun başka yapay zekâ modelleriyle ve BIST 100, S&P 500, altın, Bitcoin
ve dolar tutmakla kıyaslanacak.

BU PORTFÖY: {t['ad']}
{_TIP[t['tip']]}{risk}

Kurallar:
- Başlangıç sermayesi {ayarlar.BASLANGIC_NAKIT_TL:,.0f} TL. Her alış ve satışta %{ayarlar.KOMISYON_ORANI*100:.1f} komisyon düşülür.
- Yahoo Finance sembolü olan her şeyi alabilirsin: Türk hisseleri (THYAO.IS), ABD hisseleri (AAPL), fonlar
  (SPY, QQQ, GLD, TLT), emtia vadelileri (GC=F, SI=F), kripto (BTC-USD, ETH-USD vb.), döviz (USDTRY=X; bunu
  almak dolar tutmak demektir). ^ ile başlayan endeksler yalnızca bilgi içindir, alınamaz; XU100.IS ve XU030.IS
  endeks fonu gibi alınabilir. Kesirli adet serbesttir. Açığa satış ve kaldıraç yoktur. Nakit faiz getirmez.
- Yalnızca piyasası şu an açık olan varlıklarla işlem yapılabilir. Mesajda yalnızca açık piyasaların verisi
  gösterilir; kapalı olanlar hakkında bu turda karar verme. Yaklaşık piyasa saatleri (İstanbul saati):
  Borsa İstanbul ve TL kurları hafta içi 10:00-18:00; ABD borsaları hafta içi New York saatiyle 09:30-16:00
  (İstanbul'da kışın 17:30-24:00, yazın 16:30-23:00); kripto 7/24; emtia vadelileri ve diğer kurlar hafta içi
  neredeyse gün boyu. Tatil günleri kapalıdır.
- {kontrol}
- Önceki konuşmaları hatırlamazsın; geçmişte ne düşündüğünü yalnızca kendi yazdığın NOTLAR, PLAN ve SONRAKİ
  TURA MESAJ alanlarından bilirsin. Bunları her turda yeniden yaz: önemli olanı koru, eskiyeni at, kısa tut.
  Sınırlar: notlar {ayarlar.NOT_SINIRI}, plan {ayarlar.PLAN_SINIRI}, mesaj {ayarlar.MESAJ_SINIRI} karakter. Aşarsan sondan kesilir.
- Bir sembolün verisini sonraki turlarda görmek istersen izleme_listesi'ne ekle (en fazla {ayarlar.IZLEME_SINIRI}).
- İşlem yapmamak da bir karardır. Komisyonu unutma.

Cevabını SADECE aşağıdaki biçimde, geçerli tek bir JSON nesnesi olarak ver, başka metin yazma:
{{
  "piyasa_yorumu": "şu anki duruma kısa bakışın (en fazla 400 karakter)",
  "islemler": [
    {{"islem": "sat", "sembol": "XXX", "yuzde": 50, "neden": "kısa gerekçe"}},
    {{"islem": "al", "sembol": "YYY", "tutar_tl": 2000, "neden": "kısa gerekçe"}}
  ],
  "notlar": "kendine kalıcı notların: stratejin, öğrendiklerin, pozisyonları neden aldığın",
  "plan": "önümüzdeki dönem için planın: hangi koşulda ne yapacaksın",
  "izleme_listesi": ["SEMBOL1", "SEMBOL2"],
  "sonraki_tura_mesaj": "bir sonraki turda kendine ilk okuman gereken mesaj",
  "sonraki_kontrol": "YYYY-AA-GG SS:DD (İstanbul saati; bana ne zaman tekrar sorulsun)",
  "sonraki_kontrol_nedeni": "neden o zaman"
}}
Satışlar alışlardan önce yapılır. Türkçe yaz."""


def _tr(iso: str) -> str:
    return dt.datetime.fromisoformat(iso).astimezone(ISTANBUL).strftime("%d.%m %H:%M")


def _yuzde(x):
    return "-" if x is None else f"{x:+.2f}"


def _satir(s, d):
    tl = f" (= {d['fiyat_tl']:.4f} TL)" if d.get("fiyat_tl") and d["para_birimi"] != "TRY" and d.get("islem", True) else ""
    bilgi = " | yalnızca bilgi, alınamaz" if not d.get("islem", True) else ""
    # Endeks değerinin birimi yoktur; ^TNX ve ^VIX birer orandır.
    birim = {"^TNX": "% (ABD 10 yıllık tahvil faizi)", "^VIX": "puan (oynaklık endeksi)"}.get(
        s, "puan" if s.startswith("^") else d['para_birimi'])
    return (f"{s}: {d['fiyat']:.4f} {birim}{tl} | gün {_yuzde(d['gun_%'])}% hafta {_yuzde(d['hafta_%'])}% "
            f"ay {_yuzde(d['ay_%'])}% 3ay {_yuzde(d['3ay_%'])}%{bilgi}")


def mesaj(*, simdi_tr, gecen_gun, portfoy, toplam, satirlar, fiyatlar, hafiza, son_islemler, son_degerler,
          onceki_sonuclar) -> str:
    b = [f"ŞU AN: {simdi_tr} (İstanbul saati). Portföyün başlangıcından bu yana {gecen_gun} gün geçti."]
    b.append(f"\n=== GEÇEN TURDAN KENDİNE MESAJ ===\n{hafiza.get('sonraki_tura_mesaj') or '(ilk tur)'}")
    b.append(f"\n=== NOTLARIN ===\n{hafiza.get('notlar') or '(henüz not yok)'}")
    b.append(f"\n=== PLANIN ===\n{hafiza.get('plan') or '(henüz plan yok)'}")
    if onceki_sonuclar:
        b.append("\n=== GEÇEN TURUN SONUÇLARI ===\n" + "\n".join(onceki_sonuclar))
    b.append(f"\n=== PORTFÖY ===\nToplam değer: {toplam:,.2f} TL (başlangıç {ayarlar.BASLANGIC_NAKIT_TL:,.0f} TL, "
             f"{_yuzde((toplam / ayarlar.BASLANGIC_NAKIT_TL - 1) * 100)}%)\n"
             f"Nakit: {portfoy['nakit_tl']:,.2f} TL | Ödenen toplam komisyon: {portfoy['odenen_komisyon_tl']:,.2f} TL")
    for r in satirlar:
        d = fiyatlar.get(r["sembol"]) or {}
        durum = "piyasası AÇIK" if d.get("acik") else "piyasası kapalı, bu turda işlem yapılamaz"
        b.append(f"- {r['sembol']}: {r['adet']:.6g} adet, değer {r['deger_tl']:,.2f} TL, maliyet {r['maliyet_tl']:,.2f} TL, "
                 f"kâr/zarar {r['deger_tl'] - r['maliyet_tl']:+,.2f} TL ({_yuzde(r['kar_%'])}%) | {durum}")
    if son_degerler:
        b.append("\n=== PORTFÖY DEĞERİ GEÇMİŞİ ===\n" +
                 ", ".join(f"{_tr(g['zaman'])}={g['deger_tl']:,.0f}" for g in son_degerler))
    if son_islemler:
        b.append("\n=== SON İŞLEMLERİN ===\n" + "\n".join(
            f"{_tr(i['zaman'])} {i['sonuc']}" for i in son_islemler))

    gosterilen, kapali = set(), []
    for grup, semboller in ayarlar.GENEL_SEMBOLLER.items():
        acik = [s for s in semboller if fiyatlar.get(s, {}).get("piyasa_acik")]
        gosterilen.update(semboller)
        if acik:
            b.append(f"\n=== {grup.upper()} (açık piyasalar) ===\n" + "\n".join(_satir(s, fiyatlar[s]) for s in acik))
    ozel = [s for s in dict.fromkeys(list(portfoy["pozisyonlar"]) + hafiza.get("izleme_listesi", []))
            if s not in gosterilen]
    acik_ozel = []
    for s in ozel:
        if fiyatlar.get(s, {}).get("piyasa_acik"):
            acik_ozel.append(s)
        else:
            kapali.append(s)
    if acik_ozel:
        b.append("\n=== PORTFÖYÜN VE İZLEME LİSTEN (açık piyasalar) ===\n" +
                 "\n".join(_satir(s, fiyatlar[s]) for s in acik_ozel))
    if kapali:
        b.append("\nŞu an piyasası kapalı veya verisi olmadığı için gösterilmeyenler: " + ", ".join(kapali))
    b.append("\nKararını JSON olarak ver.")
    return "\n".join(b)


def ayristir(metin: str) -> dict:
    metin = metin.strip()
    kod = re.search(r"```(?:json)?\s*(\{.*\})\s*```", metin, re.S)
    if kod:
        metin = kod.group(1)
    else:
        bas, son = metin.find("{"), metin.rfind("}")
        if bas != -1 and son != -1:
            metin = metin[bas:son + 1]
    veri = json.loads(metin)
    if not isinstance(veri, dict):
        raise ValueError("JSON nesnesi değil")
    return veri
