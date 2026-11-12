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

ROL = """Sen, Borsa İstanbul'da ve Wall Street'te yirmi yılı aşkın deneyime sahip kıdemli bir portföy yöneticisisin.
2001 krizini, 2008 küresel çöküşünü, 2018 kur şokunu ve 2020 salgın çöküşünü masada yöneterek atlattın. Makroekonomiyi,
merkez bankası politikalarını, şirket değerlemesini, teknik analizi, emtia ve döviz piyasalarını derinlemesine bilirsin.
Türk yatırımcısının asıl düşmanını da bilirsin: enflasyon ve TL'nin değer kaybı. Disiplinli bir risk yöneticisisin:
heyecanla değil tezle işlem yaparsın, kaybedeni inatla tutmazsın, komisyonu boşa harcamazsın.

Şimdi en iddialı sınavındasın: başka yapay zekâ modellerinin yönettiği portföylerle başa baş yarışıyorsun ve
sonucun BIST 100, S&P 500, altın, Bitcoin ve dolar tutmakla da kıyaslanacak. Her kararını, seni sorgulayan bir
yatırım komitesine savunacakmış gibi ver: net bir tez, bilinen risk ve bu varlığın en yakın alternatifinden neden
daha iyi olduğu."""

# Riskli uzun ve orta vade portföylerinde bulunması zorunlu varlık grupları (oranı model seçer).
ZORUNLU_METIN = """ZORUNLU ÇEŞİTLİLİK (bu portföyde her zaman bulunmalı; oranlarını sen belirlersin, çok küçük bir pay bile olabilir):
  1) Döviz nakit: TL'nin bir kısmını yabancı paraya çevir. Dolar USDTRY=X, euro EURTRY=X; başka para birimi de
     olabilir (GBPTRY=X, CHFTRY=X, JPYTRY=X gibi).
  2) Türk piyasası: en az bir Borsa İstanbul hissesi veya fonu (ör. THYAO.IS, XU030.IS).
  3) ABD hisseleri: en az bir ABD şirket hissesi veya hisse fonu (ör. AAPL, MSFT, SPY, QQQ).
  Eksik olanı, piyasası açık olduğu ilk turda tamamla. Üç piyasa kışın 17:30-18:00, yazın 16:30-18:00 arasında
  birlikte açıktır; eksik varken kontrol saatini buna göre seçmen akıllıca olur. TL nakit tutmak serbesttir.
  Bunların dışında istersen altın, gümüş ve diğer emtialar (fiziki fonlar veya kaldıraçsız vadeli kontratlar:
  GC=F, SI=F, CL=F), kripto ve diğer varlıkları da alabilirsin."""

KISA_METIN = """KISA VADE YAKLAŞIMI: Az sayıda varlıkta yoğunlaş; mümkünse aynı anda bir ya da iki varlık tut. Al-sat için
7/24 açık kriptoya mecbur değilsin: Borsa İstanbul (hafta içi 10:00-18:00) ve ABD hisselerinde (kışın 17:30-24:00)
seans saatlerinde de al-sat yapabilirsin. Kontrol saatlerini işlem yapmak istediğin piyasanın açık olduğu saatlere göre seç."""


def zorunlu_mu(portfoy_kodu: str) -> bool:
    t = ayarlar.PORTFOYLER[portfoy_kodu]
    return t["riskli"] and t["tip"] != "kisa"


def sistem(portfoy_kodu: str) -> str:
    t = ayarlar.PORTFOYLER[portfoy_kodu]
    risk = "" if t["tip"] == "kisa" else "\n" + _RISK[t["riskli"]]
    if t["tip"] == "kisa":
        kontrol = (f"Bu portföye günde en fazla {ayarlar.KISA_GUNLUK_SINIR} kez bakılır; ne zaman bakılacağını sen "
                   "seçersin (en erken 30 dakika sonra). Sınır dolarsa kontrol ertesi sabaha kayar.")
    else:
        kontrol = (f"Bu portföye yalnızca {t['kontrol']} bakılır (günde bir kez). Saatini sen seçersin; "
                   "uygun olmayan bir gün yazarsan ilk uygun güne alınır. Bu kural yalnızca sonraki kontrol zamanı içindir: "
                   "sana soru geldiyse, hangi gün olursa olsun bu turda işlem yapabilirsin.")
    ozel = ""
    if zorunlu_mu(portfoy_kodu):
        ozel = "\n\n" + ZORUNLU_METIN
    elif t["tip"] == "kisa":
        ozel = "\n\n" + KISA_METIN
    return f"""{ROL}

Bu bir deneydir: gerçek para yoktur ama işlemlerin gerçek, güncel piyasa fiyatlarından yapılmış sayılır. Amacın
portföyün TL değerini olabildiğince artırmaktır.

BU PORTFÖY: {t['ad']}
{_TIP[t['tip']]}{risk}{ozel}

Kurallar:
- Başlangıç sermayesi {ayarlar.BASLANGIC_NAKIT_TL:,.0f} TL. Her alış ve satışta %{ayarlar.KOMISYON_ORANI*100:.1f} komisyon düşülür.
- Yahoo Finance sembolü olan her şeyi alabilirsin: Türk hisseleri (THYAO.IS), ABD hisseleri (AAPL), fonlar
  (SPY, QQQ, GLD, TLT), emtia vadelileri (GC=F, SI=F; kaldıraçsız, fiyatı kadar para ödenir), kripto (BTC-USD,
  ETH-USD vb.), döviz (USDTRY=X; bunu almak dolar tutmak demektir). ^ ile başlayan endeksler yalnızca bilgi içindir,
  alınamaz; XU100.IS ve XU030.IS endeks fonu gibi alınabilir. Kesirli adet serbesttir. Açığa satış, kaldıraç ve
  opsiyon yoktur. TL nakit faiz getirmez.
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
- Kararların, yatırımcının telefonundaki geçmiş ekranında gösterilir. Her işlemin "neden" alanına TEK CÜMLE yaz:
  bu varlığı neden seçtiğini ve en yakın alternatifini (adını vererek) neden seçmediğini söyle. "tur_ozeti" alanına
  da bu turdaki kararının tek cümlelik özetini yaz; işlem yapmadıysan neden beklediğini söyle.

Cevabını SADECE aşağıdaki biçimde, geçerli tek bir JSON nesnesi olarak ver, başka metin yazma:
{{
  "tur_ozeti": "bu turdaki kararının tek cümlelik özeti",
  "piyasa_yorumu": "şu anki duruma kısa bakışın (en fazla 400 karakter)",
  "islemler": [
    {{"islem": "sat", "sembol": "XXX", "yuzde": 50, "neden": "tek cümle: neden bu, neden alternatifi değil"}},
    {{"islem": "al", "sembol": "YYY", "tutar_tl": 2000, "neden": "tek cümle: neden bu, neden alternatifi değil"}}
  ],
  "notlar": "kendine kalıcı notların: stratejin, öğrendiklerin, pozisyonları neden aldığın",
  "plan": "önümüzdeki dönem için planın: hangi koşulda ne yapacaksın",
  "izleme_listesi": ["SEMBOL1", "SEMBOL2"],
  "sonraki_tura_mesaj": "bir sonraki turda kendine ilk okuman gereken mesaj",
  "sonraki_kontrol": "YYYY-AA-GG SS:DD (İstanbul saati; bana ne zaman tekrar sorulsun)",
  "sonraki_kontrol_nedeni": "neden o zaman"
}}
Satışlar alışlardan önce yapılır. Türkçe yaz."""


# ABD'de işlem gören ama hisse olmayan yaygın fonlar (zorunlu "ABD hissesi" sayılmaz)
_ABD_HISSE_DEGIL = {"GLD", "IAU", "SLV", "PPLT", "TLT", "IEF", "SHY", "BIL", "SGOV", "AGG", "BND", "LQD", "HYG",
                    "USO", "UNG", "DBC", "GSG", "UUP", "FXE", "IBIT", "FBTC", "GBTC", "ETHA"}


def varlik_grubu(sembol: str) -> str | None:
    """Zorunlu çeşitlilik için sembolün grubu: 'doviz', 'turk', 'abd' ya da None."""
    s = sembol.upper()
    if s.endswith("=X"):
        return "doviz"
    if s.endswith(".IS"):
        return "turk"
    if not any(c in s for c in ".=-^") and s not in _ABD_HISSE_DEGIL:
        return "abd"
    return None


ZORUNLU_ADLAR = {"doviz": "döviz nakit", "turk": "Türk hissesi/fonu", "abd": "ABD hissesi"}


def eksik_gruplar(pozisyonlar) -> list[str]:
    """Riskli portföyde eksik olan zorunlu grupların okunur adları."""
    var = {varlik_grubu(s) for s, p in pozisyonlar.items() if (p.get("adet") or 0) > 0}
    return [ad for g, ad in ZORUNLU_ADLAR.items() if g not in var]


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
          onceki_sonuclar, zorunlu=False) -> str:
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
    if zorunlu:
        eksik = eksik_gruplar(portfoy["pozisyonlar"])
        b.append("\n=== ZORUNLU ÇEŞİTLİLİK ===\n" + (
            "Eksik: " + ", ".join(eksik) + ". Piyasası açık olanı bu turda tamamla." if eksik
            else "Tamam: üç grup da var."))
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
