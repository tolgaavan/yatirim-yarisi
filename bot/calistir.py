"""Zamanı gelen portföyleri çalıştırır: veriyi al, modellere sor, emirleri uygula, kaydet, uygulama verisini yaz.

GitHub zamanlayıcısı bunu 30 dakikada bir çağırır. Her portföyün bir sonraki kontrol zamanını model kendisi seçer;
zamanı gelmemiş portföye dokunulmaz. Tur olmasa da birkaç saatte bir tüm portföylerin değeri kaydedilir.

Kullanım:
  python -m bot.calistir                         zamanı gelenleri çalıştır
  python -m bot.calistir --zorla                 zamanı gelmemiş olsa da çalıştır (aşağıdaki süzgeçlerle)
  python -m bot.calistir --model claude          yalnızca bu model (deepseek, chatgpt, claude, hepsi)
  python -m bot.calistir --portfoy kisa          yalnızca bu portföy (ör. uzun_riskli, hepsi)
  python -m bot.calistir --deneme                modeller yerine sahte karar (anahtar gerekmez)
  python -m bot.calistir --haftalik              haftalık değerlendirmeyi şimdi yazdır (süzgeçlerle; deneme için)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

from . import ayarlar, bilgi, haftalik, modeller, portfoy as pf, rapor, takvim, talimat, veri

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


# ---------- dosya yardımcıları ----------

def _yol(*parcalar):
    return ayarlar.DURUM.joinpath(*parcalar)


def oku(yol, varsayilan):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return varsayilan


def yaz(yol, icerik):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(icerik, ensure_ascii=False, indent=1), encoding="utf-8")


def satirlar(yol):
    try:
        return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]
    except OSError:
        return []


def ekle(yol, kayit):
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def anahtar(model, portfoy_kodu):
    return f"{model}/{portfoy_kodu}"


# ---------- yardımcılar ----------

def _sinirla(metin, sinir):
    metin = str(metin or "").strip()
    return (metin[:sinir], True) if len(metin) > sinir else (metin, False)


def _sahte_karar(simdi, portfoy, hafiza):
    islemler = []
    if "BTC-USD" in portfoy["pozisyonlar"]:
        islemler.append({"islem": "sat", "sembol": "BTC-USD", "yuzde": 50, "neden": "deneme satışı"})
    islemler += [{"islem": "al", "sembol": "BTC-USD", "tutar_tl": 3000, "neden": "deneme alışı"},
                 {"islem": "al", "sembol": "THYAO.IS", "tutar_tl": 2000, "neden": "deneme (kapalıysa reddedilir)"},
                 {"islem": "al", "sembol": "OLMAYAN-SEMBOL", "tutar_tl": 500, "neden": "reddedilmeli"}]
    sonraki = (simdi.astimezone(veri.ISTANBUL) + dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    islemler += [{"islem": "al", "sembol": "USDTRY=X", "tutar_tl": 300, "neden": "deneme döviz"},
                 {"islem": "al", "sembol": "AAPL", "tutar_tl": 300, "neden": "deneme ABD hissesi"}]
    kurgu = "" if hafiza.get("kurgu") else "Deneme kurgusu: dolar, Türk ve ABD hissesiyle dengeli başladım."
    return json.dumps({"tur_ozeti": "deneme turu özeti", "baslangic_kurgusu": kurgu, "piyasa_yorumu": "deneme turu", "islemler": islemler, "notlar": "deneme notu " * 200,
                       "plan": "deneme planı", "izleme_listesi": ["AAPL", "ASELS.IS"],
                       "sonraki_tura_mesaj": "deneme mesajı", "sonraki_kontrol": sonraki,
                       "sonraki_kontrol_nedeni": "deneme"}), {}


def _degerleme_gerekli(simdi):
    son = satirlar(_yol("degerler.jsonl"))
    if not son:
        return True
    return (simdi - dt.datetime.fromisoformat(son[-1]["zaman"])).total_seconds() >= ayarlar.DEGERLEME_ARALIGI_SAAT * 3600


def zamani_gelenler(simdi, aktif_modeller, zorla, model_suzgeci, portfoy_suzgeci):
    plan = oku(_yol("takvim.json"), {})
    sonuc = []
    for m in aktif_modeller:
        if model_suzgeci not in (None, "hepsi", m):
            continue
        for p in ayarlar.PORTFOYLER:
            if portfoy_suzgeci not in (None, "hepsi", p):
                continue
            kayit = plan.get(anahtar(m, p))
            if zorla or not kayit:
                sonuc.append((m, p))
                continue
            zaman = dt.datetime.fromisoformat(kayit["sonraki"])
            if zaman <= simdi + dt.timedelta(minutes=ayarlar.ERKEN_CALISMA_DAKIKA):
                sonuc.append((m, p))
    return sonuc


# ---------- ana akış ----------

def haftalik_bekleyenler(simdi, aktif_modeller, zorla_haftalik=False, model_suzgeci=None, portfoy_suzgeci=None):
    """[(model, portföy, hafta)]: haftalık değerlendirmesi yazılacak portföyler."""
    sonuc = []
    for m in aktif_modeller:
        for p in ayarlar.PORTFOYLER:
            portfoy = oku(_yol(m, p, "portfoy.json"), None)
            if not portfoy:
                continue
            if zorla_haftalik:
                if model_suzgeci in (None, "hepsi", m) and portfoy_suzgeci in (None, "hepsi", p):
                    sonuc.append((m, p, "zorla-" + simdi.astimezone(veri.ISTANBUL).date().isoformat()))
                continue
            hafta = haftalik.bekliyor_mu(_yol(m, p), portfoy, simdi)
            if hafta:
                sonuc.append((m, p, hafta))
    return sonuc


def haftalik_yaz(simdi, bekleyenler, deneme):
    """Cuma gecesi değerlendirmeleri: her portföy için modeline o haftanın kayıtlarını verip özet yazdırır."""
    if not bekleyenler:
        return
    degerler = satirlar(_yol("degerler.jsonl"))
    son = degerler[-1] if degerler else {}
    kiyaslar, son_degerler = son.get("kiyaslar", {}), son.get("portfoyler", {})
    isler = []
    for m, p, hafta in bekleyenler:
        k = anahtar(m, p)
        if k not in son_degerler:
            continue
        sistem, mesaj_, kayit = haftalik.hazirla(
            _yol(m, p), p, oku(_yol(m, p, "portfoy.json"), {}), oku(_yol(m, p, "hafiza.json"), {}),
            son_degerler[k], kiyaslar, degerler, simdi, hafta)
        isler.append((m, p, sistem, mesaj_, kayit))

    def sor(is_):
        m = is_[0]
        try:
            if deneme:
                return is_, (json.dumps({"haftalik_ozet": "Deneme haftalık değerlendirmesi."}), {}), None
            return is_, modeller.sor(m, is_[2], is_[3]), None
        except Exception as e:
            return is_, None, f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=8) as havuz:
        for (m, p, sistem, mesaj_, kayit), cevap, hata in havuz.map(sor, isler):
            kayit.update({"zaman": simdi.isoformat(), "model": "deneme" if deneme else modeller.model_adi(m)})
            if not hata:
                try:
                    kayit["ozet"] = haftalik.ozeti_ayikla(cevap[0])
                    kayit["kullanim"] = cevap[1]
                except Exception as e:
                    hata = f"cevap okunamadı: {e}"
            if hata:
                kayit = {"hafta": kayit["hafta"], "zaman": simdi.isoformat(), "hata": hata}
            ekle(_yol(m, p, "haftalik.jsonl"), kayit)
            _yol(m, p, "son_haftalik_soru.txt").write_text(sistem + "\n\n-----\n\n" + mesaj_, encoding="utf-8")
            durum = ("HATA " + hata) if hata else kayit["ozet"][:100]
            print(f"{anahtar(m, p)} haftalık: {durum}")


def calistir(deneme=False, zorla=False, model_suzgeci=None, portfoy_suzgeci=None, zorla_haftalik=False) -> int:
    simdi = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    aktif = [m for m in ayarlar.MODELLER if deneme or modeller.anahtar_var(m)]
    eksik_anahtar = [m for m in ayarlar.MODELLER if m not in aktif]
    if eksik_anahtar:
        print("Anahtarı olmadığı için atlanan modeller:", ", ".join(eksik_anahtar))

    gorevler = [] if zorla_haftalik else zamani_gelenler(simdi, aktif, zorla, model_suzgeci, portfoy_suzgeci)
    haftaliklar = haftalik_bekleyenler(simdi, aktif, zorla_haftalik, model_suzgeci, portfoy_suzgeci)
    if not gorevler and not haftaliklar and not _degerleme_gerekli(simdi):
        print("Zamanı gelen portföy yok.")
        return 0

    # Var olan tüm portföyler (değerleme için) ve çalışacak olanların hafızası
    portfoyler, hafizalar = {}, {}
    for m in ayarlar.MODELLER:
        for p in ayarlar.PORTFOYLER:
            k = anahtar(m, p)
            kayitli = oku(_yol(m, p, "portfoy.json"), None)
            if kayitli:
                portfoyler[k] = kayitli
            elif (m, p) in gorevler:
                portfoyler[k] = pf.yeni_portfoy(simdi.isoformat())
            if (m, p) in gorevler:
                hafizalar[k] = oku(_yol(m, p, "hafiza.json"), {})

    istenen = [s for v in ayarlar.GENEL_SEMBOLLER.values() for s in v] + list(ayarlar.KIYASLAR.values())
    if gorevler:
        istenen += [s for v in ayarlar.FIRSAT_EVRENI.values() for s in v]
    for k, p in portfoyler.items():
        istenen += list(p["pozisyonlar"])
    for h in hafizalar.values():
        istenen += h.get("izleme_listesi", [])
    fiyatlar = veri.fiyatlar(istenen, simdi)
    if not fiyatlar:
        print("Hiç piyasa verisi alınamadı; çalışma atlandı.")
        return 1

    # Temel veriler ve haberler: yalnızca soru sorulacak portföylerin varlıkları ve izleme listeleri için
    kendi_semboller = []
    for m, p in gorevler:
        k = anahtar(m, p)
        kendi_semboller += list(portfoyler[k]["pozisyonlar"]) + hafizalar[k].get("izleme_listesi", [])
    kendi_semboller = list(dict.fromkeys(kendi_semboller))
    temel_veri, haber_veri = {}, {}
    if gorevler:
        try:
            temel_veri = bilgi.temel(kendi_semboller)
        except Exception as e:
            print("Temel veri alınamadı:", e)
        try:
            haber_veri = bilgi.haberler([s for s in kendi_semboller if fiyatlar.get(s, {}).get("piyasa_acik")], simdi)
        except Exception as e:
            print("Haberler alınamadı:", e)

    simdi_tr = simdi.astimezone(veri.ISTANBUL)
    zaman_metni = f"{simdi_tr:%d.%m.%Y} {GUNLER[simdi_tr.weekday()]} {simdi_tr:%H:%M}"

    # 1) Soruları hazırla
    sorular = {}
    for m, p in gorevler:
        k = anahtar(m, p)
        portfoy = portfoyler[k]
        hafiza = hafizalar[k]
        toplam, satir = pf.degerle(portfoy, fiyatlar)
        gecmis = satirlar(_yol(m, p, "gecmis.jsonl"))
        gecen = (simdi - dt.datetime.fromisoformat(portfoy["baslangic"])).days
        sorular[k] = (talimat.sistem(p), talimat.mesaj(
            simdi_tr=zaman_metni, gecen_gun=gecen, portfoy=portfoy, toplam=toplam, satirlar=satir,
            fiyatlar=fiyatlar, hafiza=hafiza, son_islemler=satirlar(_yol(m, p, "islemler.jsonl"))[-8:],
            son_degerler=gecmis[-12:], onceki_sonuclar=hafiza.get("son_tur_sonuclari", []),
            zorunlu=talimat.zorunlu_mu(p), kisa=ayarlar.PORTFOYLER[p]["tip"] == "kisa",
            son_hafta=haftalik.son_ozet(_yol(m, p)), temel=temel_veri, haberler=haber_veri))

    # 2) Modellere aynı anda sor
    def sor(gorev):
        m, p = gorev
        k = anahtar(m, p)
        try:
            if deneme:
                return k, _sahte_karar(simdi, portfoyler[k], hafizalar[k]), None
            return k, modeller.sor(m, *sorular[k]), None
        except Exception as e:
            return k, None, f"{type(e).__name__}: {e}"

    cevaplar = {}
    if gorevler:
        with ThreadPoolExecutor(max_workers=8) as havuz:
            for k, cevap, hata in havuz.map(sor, gorevler):
                cevaplar[k] = (cevap, hata)

    # 3) Emirler için eksik fiyatları tek seferde al
    kararlar = {}
    for k, (cevap, hata) in cevaplar.items():
        if cevap:
            try:
                kararlar[k] = talimat.ayristir(cevap[0])
            except Exception as e:
                kararlar[k] = e
    eksik = set()
    for karar in kararlar.values():
        if isinstance(karar, dict) and isinstance(karar.get("islemler"), list):
            for e in karar["islemler"]:
                if isinstance(e, dict):
                    s = str(e.get("sembol", "")).strip().upper()
                    if s and s not in fiyatlar:
                        eksik.add(s)
    if eksik:
        fiyatlar.update(veri.fiyatlar(sorted(eksik), simdi))

    # 4) Uygula ve kaydet
    takvim_kaydi = oku(_yol("takvim.json"), {})
    for m, p in gorevler:
        k = anahtar(m, p)
        cevap, hata = cevaplar[k]
        portfoy, hafiza = portfoyler[k], hafizalar[k]
        model_adi = "deneme" if deneme else modeller.model_adi(m)
        if hata:
            # Hafıza ve portföy değişmez; 30 dakika sonra yeniden denenir.
            print(f"{k}: HATA {hata}")
            ekle(_yol(m, p, "kararlar.jsonl"), {"zaman": simdi.isoformat(), "model": model_adi, "hata": hata})
            takvim_kaydi[k] = {"sonraki": (simdi + dt.timedelta(minutes=30)).isoformat(),
                               "neden": "hata, yeniden denenecek"}
            continue

        ham, kullanim = cevap
        karar = kararlar.get(k)
        sonuclar = []
        if not isinstance(karar, dict):
            sonuclar.append(f"HATA: Cevabın JSON olarak okunamadı ({karar}). Hiçbir işlem yapılmadı, hafızan değişmedi.")
            karar = {}

        emirler = [e for e in (karar.get("islemler") or []) if isinstance(e, dict)] if isinstance(
            karar.get("islemler"), list) else []
        emirler.sort(key=lambda e: 0 if str(e.get("islem", "")).lower() == "sat" else 1)
        for e in emirler:
            sembol = str(e.get("sembol", "")).strip().upper()
            tip = str(e.get("islem", "")).lower()
            if tip == "al":
                sonuc = pf.al(portfoy, sembol, e.get("tutar_tl"), fiyatlar.get(sembol))
            elif tip == "sat":
                sonuc = pf.sat(portfoy, sembol, e.get("yuzde", 100), fiyatlar.get(sembol))
            else:
                sonuc = f"REDDEDİLDİ: bilinmeyen işlem türü '{tip}'."
            sonuclar.append(sonuc)
            ekle(_yol(m, p, "islemler.jsonl"), {"zaman": simdi.isoformat(), "emir": e, "sonuc": sonuc,
                                                "neden": e.get("neden", "")})

        if karar:
            for alan, sinir in (("notlar", ayarlar.NOT_SINIRI), ("plan", ayarlar.PLAN_SINIRI),
                                ("sonraki_tura_mesaj", ayarlar.MESAJ_SINIRI)):
                metin, kesildi = _sinirla(karar.get(alan), sinir)
                hafiza[alan] = metin
                if kesildi:
                    sonuclar.append(f"UYARI: '{alan}' {sinir} karakteri aştığı için sondan kesildi; daha kısa yaz.")
            izleme = karar.get("izleme_listesi") or []
            if isinstance(izleme, list):
                hafiza["izleme_listesi"] = list(dict.fromkeys(
                    str(s).strip().upper() for s in izleme if str(s).strip()))[: ayarlar.IZLEME_SINIRI]
            hafiza["son_yorum"] = str(karar.get("piyasa_yorumu") or "")[:600]
            kurgu, kesildi = _sinirla(karar.get("baslangic_kurgusu"), ayarlar.KURGU_SINIRI)
            eski = hafiza.get("kurgu")
            if kurgu and (not eski or eski.get("metin") != kurgu):
                if eski:
                    hafiza["kurgu_gecmisi"] = (hafiza.get("kurgu_gecmisi", []) + [eski])[-5:]
                hafiza["kurgu"] = {"metin": kurgu, "zaman": simdi.isoformat(),
                                   "neden": str(karar.get("kurgu_degisim_nedeni") or "")[:300] if eski else ""}
                if kesildi:
                    sonuclar.append(f"UYARI: başlangıç kurgusu {ayarlar.KURGU_SINIRI} karakteri aştığı için kesildi.")

        if talimat.zorunlu_mu(p):
            eksik_grup = talimat.eksik_gruplar(portfoy["pozisyonlar"])
            if eksik_grup:
                sonuclar.append("UYARI: zorunlu çeşitlilik eksik: " + ", ".join(eksik_grup) +
                                ". Piyasası açık olduğu ilk turda tamamla.")

        gecmis = satirlar(_yol(m, p, "gecmis.jsonl"))
        sonraki, duzeltme = takvim.sonraki(p, karar.get("sonraki_kontrol"), simdi,
                                           [g["zaman"] for g in gecmis] + [simdi.isoformat()])
        istek = karar.get("sonraki_kontrol") or "-"
        sonuclar.append(f"Sonraki kontrol: {sonraki:%Y-%m-%d %H:%M}" +
                        (f" (istediğin: {istek}; {duzeltme})" if duzeltme else ""))
        hafiza["son_tur_sonuclari"] = sonuclar
        takvim_kaydi[k] = {"sonraki": sonraki.isoformat(), "neden": str(karar.get("sonraki_kontrol_nedeni") or "")[:300]}

        toplam, _ = pf.degerle(portfoy, fiyatlar)
        ekle(_yol(m, p, "gecmis.jsonl"), {"zaman": simdi.isoformat(), "deger_tl": round(toplam, 2),
                                          "nakit_tl": round(portfoy["nakit_tl"], 2)})
        ekle(_yol(m, p, "kararlar.jsonl"), {"zaman": simdi.isoformat(), "model": model_adi, "kullanim": kullanim,
                                            "ozet": str(karar.get("tur_ozeti") or "")[:500],
                                            "soru_uzunlugu": len(sorular[k][1]), "cevap": ham, "sonuclar": sonuclar})
        yaz(_yol(m, p, "portfoy.json"), portfoy)
        yaz(_yol(m, p, "hafiza.json"), hafiza)
        (_yol(m, p, "son_soru.txt")).write_text(sorular[k][0] + "\n\n-----\n\n" + sorular[k][1], encoding="utf-8")
        print(f"{k}: değer {toplam:,.2f} TL")
        for s in sonuclar:
            print("   ", s)
    yaz(_yol("takvim.json"), takvim_kaydi)

    # 5) Değer kaydı (grafik için) ve uygulama verisi
    kiyas_bas = oku(_yol("kiyas_baslangic.json"), {})
    kiyaslar = {}
    for ad, s in ayarlar.KIYASLAR.items():
        f = fiyatlar.get(s, {}).get("fiyat_tl")
        if f and ad not in kiyas_bas:
            kiyas_bas[ad] = f
        if f and kiyas_bas.get(ad):
            kiyaslar[ad] = round(ayarlar.BASLANGIC_NAKIT_TL * f / kiyas_bas[ad], 2)
    yaz(_yol("kiyas_baslangic.json"), kiyas_bas)
    degerler = {}
    for k, p in portfoyler.items():
        yol = _yol(*k.split("/"), "portfoy.json")
        if yol.exists():  # henüz ilk turu başarıyla yapılmamış portföy sayılmaz
            degerler[k] = round(pf.degerle(p, fiyatlar)[0], 2)
            yaz(yol, p)  # degerle son fiyatı güncelledi
    ekle(_yol("degerler.jsonl"), {"zaman": simdi.isoformat(), "portfoyler": degerler, "kiyaslar": kiyaslar})

    haftalik_yaz(simdi, haftaliklar, deneme)

    rapor.yaz(simdi=simdi, fiyatlar=fiyatlar, aktif_modeller=aktif, deneme=deneme)
    return 0


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--deneme", action="store_true")
    a.add_argument("--zorla", action="store_true")
    a.add_argument("--model", default=None)
    a.add_argument("--portfoy", default=None)
    a.add_argument("--haftalik", action="store_true")
    g = a.parse_args(argv)
    for ad, deger, gecerli in (("model", g.model, ayarlar.MODELLER), ("portfoy", g.portfoy, ayarlar.PORTFOYLER)):
        if deger not in (None, "", "hepsi") and deger not in gecerli:
            print(f"Bilinmeyen {ad}: {deger}")
            return 2
    return calistir(deneme=g.deneme, zorla=g.zorla, model_suzgeci=g.model or None, portfoy_suzgeci=g.portfoy or None,
                     zorla_haftalik=g.haftalik)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
