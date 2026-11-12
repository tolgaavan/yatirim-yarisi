"""Modellere giden talimat (sistem metni) ve her turun mesajı; cevabın ayrıştırılması."""

from __future__ import annotations

import datetime as dt
import json
import re

from . import ayarlar, bilgi
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
seans saatlerinde de al-sat yapabilirsin. Kontrol saatlerini işlem yapmak istediğin piyasanın açık olduğu saatlere göre seç.
Portföyündeki ve izleme listendeki varlıklar için son 4 saatin 15 dakikalık fiyat seyrini, günün açılış/en yüksek/en düşük
seviyesini, 15 dakikalık RSI'ı ve son bir saatin hacminin normale oranını da görürsün (Borsa İstanbul verisi yaklaşık
15 dakika gecikmelidir)."""


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
- SIFIRDAN TESTİ: Her turda kendine sor: "Bugün elimde yalnızca nakit olsaydı bu portföyü yine böyle mi kurardım?"
  Cevabın hayırsa, komisyonu da hesaba katarak daha iyi fırsata geç; bir varlığı sırf daha önce aldın diye tutma.
  Cevabın evetse bekle; her küçük hareketin peşinden koşma.
- Sana verilen bilgiler: fiyatlar ve değişimleri; portföyündeki ve izleme listendeki varlıklar için teknik göstergeler
  (RSI, 20 ve 50 günlük ortalamaya uzaklık, 6 aylık zirve ve dibe uzaklık, yıllık oynaklık), temel veriler (F/K, PD/DD,
  piyasa değeri, temettü verimi; Yahoo verisidir, özellikle Borsa İstanbul'da hatalı olabilir, mantıksız görünen
  değere güvenme), son haber başlıkları (yalnızca başlık; tek bir başlığa dayanarak büyük karar verme) ve fırsat
  tablosu (geniş bir listeden günün en iyi ve en kötü gidenleri). Fırsat tablosunda ilgini çekeni izleme listene
  ekleyebilir veya doğrudan alabilirsin. Haber ve temel veri kaynağı bazen cevap vermez; o zaman o bölüm görünmez.
- BAŞLANGIÇ KURGUSU: Mesajda BAŞLANGIÇ KURGUN bölümü "(henüz yazmadın)" diyorsa, "baslangic_kurgusu" alanına bu
  portföyü nasıl kurduğunu ve hangi stratejiyi izlediğini yatırımcıya anlatır gibi, birinci tekil şahısla 2-4 cümle
  yaz. Sonraki turlarda bu alanı boş bırak; yalnızca stratejini köklü biçimde değiştirirsen yeniden yaz ve
  "kurgu_degisim_nedeni" alanına nedenini ekle. En fazla {ayarlar.KURGU_SINIRI} karakter.
- Her cuma gecesi bu haftanın kayıtlarından sana haftalık bir değerlendirme yazdırılır; son haftalık
  değerlendirmen mesajında görünür.
- Kararların, yatırımcının telefonundaki geçmiş ekranında gösterilir. Her işlemin "neden" alanına TEK CÜMLE yaz:
  bu varlığı neden seçtiğini ve en yakın alternatifini (adını vererek) neden seçmediğini söyle. "tur_ozeti" alanına
  da bu turdaki kararının tek cümlelik özetini yaz; işlem yapmadıysan neden beklediğini söyle.

Cevabını SADECE aşağıdaki biçimde, geçerli tek bir JSON nesnesi olarak ver, başka metin yazma:
{{
  "tur_ozeti": "bu turdaki kararının tek cümlelik özeti",
  "baslangic_kurgusu": "yalnızca ilk turda veya strateji köklü biçimde değişince; yoksa boş",
  "kurgu_degisim_nedeni": "kurguyu yeniden yazdıysan nedeni; yoksa boş",
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


def _sayi(x):
    """Büyük sayıları okunur kısalt: 437.8 mlr, 5.2 trn."""
    if not isinstance(x, (int, float)):
        return "-"
    for bolen, ek in ((1e12, " trn"), (1e9, " mlr"), (1e6, " mn")):
        if abs(x) >= bolen:
            return f"{x / bolen:.1f}{ek}"
    return f"{x:,.0f}"


def _teknik_metni(t):
    if not t:
        return ""
    p = []
    if t.get("rsi14") is not None:
        p.append(f"RSI14 {t['rsi14']:.0f}")
    for alan, ad in (("ort20_%", "20 günlük ortalamaya"), ("ort50_%", "50 günlük ortalamaya")):
        if t.get(alan) is not None:
            p.append(f"{ad} göre {_yuzde(t[alan])}%")
    if t.get("zirve_%") is not None:
        p.append(f"6 ay zirvesine {_yuzde(t['zirve_%'])}%, dibine {_yuzde(t['dip_%'])}%")
    if t.get("oynaklik_%") is not None:
        p.append(f"yıllık oynaklık %{t['oynaklik_%']:.0f}")
    return "teknik: " + " | ".join(p)


def _temel_metni(v):
    if not v:
        return ""
    p = []
    if v.get("fk"):
        p.append(f"F/K {v['fk']} ({v['fk_tur']})")
    if v.get("pddd"):
        p.append(f"PD/DD {v['pddd']}")
    if v.get("piyasa_degeri"):
        ad = "fon büyüklüğü" if v.get("tur") == "ETF" else "piyasa değeri"
        p.append(f"{ad} {_sayi(v['piyasa_degeri'])} {v.get('para_birimi') or ''}".rstrip())
    if v.get("temettu_%"):
        p.append(f"temettü verimi %{v['temettu_%']}")
    return ("temel: " + " | ".join(p)) if p else ""


def _gun_ici_metni(g):
    if not g or not g.get("seri"):
        return ""
    p = ["15dk son 4 saat: " + " ".join(str(x) for x in g["seri"]),
         f"bugün açılış {g['acilis']}, yüksek {g['yuksek']}, düşük {g['dusuk']}"]
    if g.get("rsi14") is not None:
        p.append(f"RSI(15dk) {g['rsi14']:.0f}")
    if g.get("ort20_%") is not None:
        p.append(f"15dk 20 çubuk ortalamasına göre {_yuzde(g['ort20_%'])}%")
    if g.get("hacim_kat") is not None:
        p.append(f"son 1 saat hacmi normalin {g['hacim_kat']} katı")
    return " | ".join(p)


def _firsat_kisa(s, d):
    r = (d.get("teknik") or {}).get("rsi14")
    return (f"{s} gün {_yuzde(d['gun_%'])}% hafta {_yuzde(d['hafta_%'])}% ay {_yuzde(d['ay_%'])}%"
            + (f" RSI {r:.0f}" if r is not None else ""))


def firsat_tablosu(fiyatlar, adet=None) -> list[str]:
    """Fırsat evreninden, piyasası açık olanların günün en çok yükselen ve düşenleri."""
    adet = adet or ayarlar.FIRSAT_SAYISI
    b = []
    for grup, semboller in ayarlar.FIRSAT_EVRENI.items():
        acik = [(s, fiyatlar[s]) for s in semboller
                if fiyatlar.get(s, {}).get("piyasa_acik") and fiyatlar[s].get("gun_%") is not None]
        if len(acik) < 2:
            continue
        acik.sort(key=lambda x: x[1]["gun_%"], reverse=True)
        yukselen = acik[:adet]
        dusen = [x for x in reversed(acik[-adet:]) if x not in yukselen]
        metin = f"{grup}:\n  günün en iyileri: " + "; ".join(_firsat_kisa(s, d) for s, d in yukselen)
        if dusen:
            metin += "\n  günün en kötüleri: " + "; ".join(_firsat_kisa(s, d) for s, d in dusen)
        b.append(metin)
    return b


def mesaj(*, simdi_tr, gecen_gun, portfoy, toplam, satirlar, fiyatlar, hafiza, son_islemler, son_degerler,
          onceki_sonuclar, zorunlu=False, kisa=False, son_hafta=None, temel=None, haberler=None) -> str:
    temel = temel or {}
    haberler = haberler or {}
    b = [f"ŞU AN: {simdi_tr} (İstanbul saati). Portföyün başlangıcından bu yana {gecen_gun} gün geçti."]
    b.append(f"\n=== GEÇEN TURDAN KENDİNE MESAJ ===\n{hafiza.get('sonraki_tura_mesaj') or '(ilk tur)'}")
    kurgu = (hafiza.get("kurgu") or {}).get("metin")
    b.append("\n=== BAŞLANGIÇ KURGUN ===\n" + (kurgu or "(henüz yazmadın; bu turda baslangic_kurgusu alanına yaz)"))
    if son_hafta:
        b.append(f"\n=== GEÇEN HAFTAKİ DEĞERLENDİRMEN ({_tr(son_hafta['bas'])} - {_tr(son_hafta['son'])}) ===\n"
                 f"Portföy {son_hafta['deger_bas']:,.0f} TL -> {son_hafta['deger_son']:,.0f} TL "
                 f"({_yuzde(son_hafta['degisim_yuzde'])}%).\n{son_hafta['ozet']}")
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

    gosterilen = set()
    for grup, semboller in ayarlar.GENEL_SEMBOLLER.items():
        acik = [s for s in semboller if fiyatlar.get(s, {}).get("piyasa_acik")]
        gosterilen.update(semboller)
        if acik:
            b.append(f"\n=== {grup.upper()} (açık piyasalar) ===\n" + "\n".join(_satir(s, fiyatlar[s]) for s in acik))
    kendi = list(dict.fromkeys(list(portfoy["pozisyonlar"]) + hafiza.get("izleme_listesi", [])))
    acik_kendi = [s for s in kendi if fiyatlar.get(s, {}).get("piyasa_acik")]
    kapali = [s for s in kendi if s not in acik_kendi]
    acik_ozel = [s for s in acik_kendi if s not in gosterilen]
    if acik_ozel:
        b.append("\n=== PORTFÖYÜN VE İZLEME LİSTEN (açık piyasalar) ===\n" +
                 "\n".join(_satir(s, fiyatlar[s]) for s in acik_ozel))
    if acik_kendi:
        analiz = []
        for s in acik_kendi:
            d = fiyatlar[s]
            v = temel.get(s) or {}
            baslik = s
            if v.get("ad"):
                baslik += f" ({v['ad']}" + (f", {v['sektor']}" if v.get("sektor") else "") + ")"
            satir = [baslik]
            for metin in (_teknik_metni(d.get("teknik")), _temel_metni(v),
                          _gun_ici_metni(d.get("gun_ici")) if kisa else ""):
                if metin:
                    satir.append("  " + metin)
            for h in (haberler.get("semboller") or {}).get(s, []):
                satir.append("  haber: " + bilgi.haber_satiri(h))
            analiz.append("\n".join(satir))
        b.append("\n=== ANALİZ: PORTFÖYÜN VE İZLEME LİSTEN ===\n" + "\n".join(analiz))
    if kapali:
        b.append("\nŞu an piyasası kapalı veya verisi olmadığı için gösterilmeyenler: " + ", ".join(kapali))
    firsat = firsat_tablosu(fiyatlar)
    if firsat:
        b.append("\n=== FIRSAT TABLOSU: günün öne çıkanları (açık piyasalar) ===\n" + "\n".join(firsat))
    genel = haberler.get("genel") or {}
    if genel:
        b.append("\n=== HABER BAŞLIKLARI ===\n" + "\n".join(
            f"{ad}:\n" + "\n".join("  " + bilgi.haber_satiri(h) for h in liste) for ad, liste in genel.items()))
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
