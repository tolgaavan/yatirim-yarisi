"""Telefon uygulamasının okuduğu docs/veri/ozet.json dosyasını ve kısa README.md raporunu üretir."""

from __future__ import annotations

import datetime as dt
import json
import os

from . import ayarlar, modeller, portfoy as pf, talimat
from .veri import ISTANBUL


def _oku(yol, varsayilan):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return varsayilan


def _satirlar(yol):
    try:
        return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]
    except OSError:
        return []


def _tr(iso):
    return dt.datetime.fromisoformat(iso).astimezone(ISTANBUL).strftime("%d.%m.%Y %H:%M") if iso else "-"


GECMIS_TUR_SAYISI = 40


def gecmis(klasor):
    """Telefondaki Geçmiş bölümü: en yeni tur başta; her turda tek cümlelik özet ve işlemler gerekçeleriyle."""
    islemler = {}
    for i in _satirlar(klasor / "islemler.jsonl"):
        islemler.setdefault(i["zaman"], []).append({"sonuc": i["sonuc"], "neden": i.get("neden", "")})
    turlar = []
    for k in _satirlar(klasor / "kararlar.jsonl")[-GECMIS_TUR_SAYISI:]:
        if k.get("hata"):
            turlar.append({"zaman": k["zaman"], "ozet": "Model bu turda cevap veremedi; 30 dakika sonra yeniden sorulacak.",
                           "hata": True, "islemler": []})
            continue
        uyarilar = [s for s in k.get("sonuclar", []) if s.startswith(("UYARI", "HATA"))]
        turlar.append({"zaman": k["zaman"], "ozet": k.get("ozet", ""), "islemler": islemler.get(k["zaman"], []),
                       "uyarilar": uyarilar})
    return list(reversed(turlar))


def ozet(simdi, fiyatlar, aktif_modeller, deneme):
    durum = ayarlar.DURUM
    takvim = _oku(durum / "takvim.json", {})
    seriler = {}
    portfoyler = {}
    for m in ayarlar.MODELLER:
        for p, tanim in ayarlar.PORTFOYLER.items():
            k = f"{m}/{p}"
            kayit = _oku(durum / m / p / "portfoy.json", None)
            if not kayit:
                portfoyler[k] = {"model": m, "portfoy": p, "basladi": False}
                continue
            hafiza = _oku(durum / m / p / "hafiza.json", {})
            toplam, satir = pf.degerle(kayit, fiyatlar)
            pozisyonlar = []
            for r in sorted(satir, key=lambda r: -r["deger_tl"]):
                d = fiyatlar.get(r["sembol"], {})
                if d.get("seri"):
                    seriler[r["sembol"]] = {"para_birimi": d.get("para_birimi"), "seri": d["seri"]}
                pozisyonlar.append({"sembol": r["sembol"], "adet": r["adet"], "deger": round(r["deger_tl"], 2),
                                    "maliyet": round(r["maliyet_tl"], 2), "kar_yuzde": round(r["kar_%"], 2),
                                    "acik": bool(d.get("acik"))})
            turlar = _satirlar(durum / m / p / "gecmis.jsonl")
            plan = takvim.get(k, {})
            portfoyler[k] = {
                "model": m, "portfoy": p, "basladi": True, "baslangic": kayit["baslangic"],
                "deger": round(toplam, 2), "nakit": round(kayit["nakit_tl"], 2),
                "komisyon": round(kayit["odenen_komisyon_tl"], 2),
                "getiri": round((toplam / ayarlar.BASLANGIC_NAKIT_TL - 1) * 100, 2),
                "pozisyonlar": pozisyonlar, "tur_sayisi": len(turlar),
                "son_tur": turlar[-1]["zaman"] if turlar else None,
                "sonraki_kontrol": plan.get("sonraki"), "sonraki_neden": plan.get("neden", ""),
                "yorum": hafiza.get("son_yorum", ""), "plan": hafiza.get("plan", ""),
                "notlar": hafiza.get("notlar", ""), "mesaj": hafiza.get("sonraki_tura_mesaj", ""),
                "son_sonuclar": hafiza.get("son_tur_sonuclari", []),
                "gecmis": gecmis(durum / m / p),
                "zorunlu": talimat.zorunlu_mu(p),
                "eksik": talimat.eksik_gruplar(kayit["pozisyonlar"]) if talimat.zorunlu_mu(p) else [],
            }
    degerler = [[d["zaman"], d["portfoyler"], d.get("kiyaslar", {})] for d in _satirlar(durum / "degerler.jsonl")]
    return {
        "guncelleme": simdi.isoformat(), "deneme": deneme, "baslangic_tl": ayarlar.BASLANGIC_NAKIT_TL,
        "komisyon_orani": ayarlar.KOMISYON_ORANI, "depo": os.environ.get("GITHUB_REPOSITORY") or ayarlar.DEPO,
        "modeller": [{"kod": m, "ad": t["ad"], "model_adi": "deneme" if deneme else modeller.model_adi(m),
                      "aktif": m in aktif_modeller} for m, t in ayarlar.MODELLER.items()],
        "portfoy_tanimlari": [{"kod": p, "ad": t["ad"], "kontrol": t["kontrol"]} for p, t in ayarlar.PORTFOYLER.items()],
        "portfoyler": portfoyler, "degerler": degerler, "seriler": seriler,
        "kiyaslar": list(ayarlar.KIYASLAR),
    }


def yaz(*, simdi, fiyatlar, aktif_modeller, deneme):
    o = ozet(simdi, fiyatlar, aktif_modeller, deneme)
    ayarlar.UYGULAMA_VERI.mkdir(parents=True, exist_ok=True)
    (ayarlar.UYGULAMA_VERI / "ozet.json").write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")),
                                                     encoding="utf-8")

    bas = ayarlar.BASLANGIC_NAKIT_TL
    m = ["# Yapay Zekâ Yatırım Yarışı\n",
         "DeepSeek, ChatGPT ve Claude Opus hayali parayla yarışıyor. Her modelin 5 portföyü var, her biri "
         f"{bas:,.0f} TL ile başladı. İşlemler gerçek piyasa fiyatlarından, %{ayarlar.KOMISYON_ORANI*100:.1f} komisyonla "
         "yapılmış sayılır. Gerçek para yoktur.\n",
         f"Son güncelleme: {_tr(simdi.isoformat())} · Ayrıntılar ve grafikler telefon uygulamasında (`docs/`).\n",
         "| Model | " + " | ".join(t["ad"] for t in ayarlar.PORTFOYLER.values()) + " | Toplam |",
         "|---|" + "---:|" * (len(ayarlar.PORTFOYLER) + 1)]
    for kod, t in ayarlar.MODELLER.items():
        hucreler, toplam, sayi = [], 0.0, 0
        for p in ayarlar.PORTFOYLER:
            d = o["portfoyler"][f"{kod}/{p}"]
            if d["basladi"]:
                hucreler.append(f"{d['getiri']:+.2f}%")
                toplam += d["deger"]
                sayi += 1
            else:
                hucreler.append("başlamadı")
        genel = f"{(toplam / (bas * sayi) - 1) * 100:+.2f}%" if sayi else "-"
        m.append(f"| {t['ad']} | " + " | ".join(hucreler) + f" | {genel} |")
    if o["degerler"] and o["degerler"][-1][2]:
        m.append("\n**Kıyas (al ve bekle):** " + ", ".join(
            f"{ad} {(v / bas - 1) * 100:+.2f}%" for ad, v in o["degerler"][-1][2].items()))
    m.append("\nModellerin tüm cevapları `durum/<model>/<portföy>/kararlar.jsonl` dosyalarındadır.")
    (ayarlar.KOK / "README.md").write_text("\n".join(m) + "\n", encoding="utf-8")
