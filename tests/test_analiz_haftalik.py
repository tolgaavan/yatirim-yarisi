import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from bot import analiz, haftalik, talimat
from bot.veri import ISTANBUL, NEW_YORK


class TestAnaliz(unittest.TestCase):
    def test_rsi_uclar(self):
        self.assertEqual(analiz.rsi(range(1, 30)), 100.0)          # hep yükselen
        self.assertLess(analiz.rsi(range(30, 1, -1)), 1)           # hep düşen
        self.assertIsNone(analiz.rsi([1, 2, 3]))                   # yetersiz veri

    def test_gunluk_teknik(self):
        k = [100 + i for i in range(60)]
        t = analiz.gunluk_teknik(k, 160)
        self.assertEqual(t["zirve_%"], 0.0)
        self.assertGreater(t["ort20_%"], 0)
        self.assertGreater(t["ort50_%"], t["ort20_%"])
        self.assertIn("oynaklik_%", t)
        self.assertEqual(analiz.gunluk_teknik([1, 2], 3), {})


class TestHaftalik(unittest.TestCase):
    def test_son_kapanis_cuma_sonrasi(self):
        # Cumartesi 00:40 İstanbul (kış) = Cuma 16:40 New York -> o cumanın kapanışı
        simdi = dt.datetime(2026, 11, 14, 0, 40, tzinfo=ISTANBUL)
        k = haftalik.son_kapanis(simdi).astimezone(NEW_YORK)
        self.assertEqual((k.date(), k.time()), (dt.date(2026, 11, 13), dt.time(16, 15)))
        # Cuma 20:00 İstanbul: ABD hâlâ açık -> bir önceki cuma
        simdi = dt.datetime(2026, 11, 13, 20, 0, tzinfo=ISTANBUL)
        self.assertEqual(haftalik.son_kapanis(simdi).astimezone(NEW_YORK).date(), dt.date(2026, 11, 6))

    def test_bekliyor_mu(self):
        with tempfile.TemporaryDirectory() as d:
            klasor = Path(d)
            simdi = dt.datetime(2026, 11, 14, 0, 40, tzinfo=ISTANBUL)
            portfoy = {"baslangic": "2026-11-12T17:00:00+00:00"}
            self.assertEqual(haftalik.bekliyor_mu(klasor, portfoy, simdi), "2026-11-13")
            # kapanıştan sonra başlayan portföy beklemez
            self.assertIsNone(haftalik.bekliyor_mu(klasor, {"baslangic": "2026-11-13T23:00:00+00:00"}, simdi))
            # yazıldıysa beklemez
            (klasor / "haftalik.jsonl").write_text(json.dumps({"hafta": "2026-11-13", "ozet": "x"}) + "\n", encoding="utf-8")
            self.assertIsNone(haftalik.bekliyor_mu(klasor, portfoy, simdi))

    def test_uc_hatadan_sonra_vazgecer(self):
        with tempfile.TemporaryDirectory() as d:
            klasor = Path(d)
            simdi = dt.datetime(2026, 11, 14, 0, 40, tzinfo=ISTANBUL)
            satir = json.dumps({"hafta": "2026-11-13", "hata": "x"}) + "\n"
            (klasor / "haftalik.jsonl").write_text(satir * 2, encoding="utf-8")
            self.assertEqual(haftalik.bekliyor_mu(klasor, {"baslangic": "2026-11-12T17:00:00+00:00"}, simdi), "2026-11-13")
            (klasor / "haftalik.jsonl").write_text(satir * 3, encoding="utf-8")
            self.assertIsNone(haftalik.bekliyor_mu(klasor, {"baslangic": "2026-11-12T17:00:00+00:00"}, simdi))


class TestMesaj(unittest.TestCase):
    def test_yeni_bolumler(self):
        fiyat = {"fiyat": 300.0, "fiyat_tl": 300.0, "para_birimi": "TRY", "piyasa_acik": True, "acik": True,
                 "gun_%": 1.0, "hafta_%": 2.0, "ay_%": 3.0, "3ay_%": 4.0, "islem": True,
                 "teknik": {"rsi14": 61.2, "ort20_%": 2.0, "zirve_%": -3.0, "dip_%": 20.0},
                 "gun_ici": {"seri": [299, 300], "acilis": 298, "yuksek": 301, "dusuk": 297, "rsi14": 55.0}}
        portfoy = {"nakit_tl": 5000.0, "odenen_komisyon_tl": 1.0, "pozisyonlar": {"THYAO.IS": {"adet": 1}}}
        haber = {"zaman": dt.datetime(2026, 11, 12, 10, tzinfo=dt.timezone.utc), "baslik": "THY yeni uçak aldı", "kaynak": "AA"}
        m = talimat.mesaj(simdi_tr="x", gecen_gun=0, portfoy=portfoy, toplam=10000.0, satirlar=[],
                          fiyatlar={"THYAO.IS": fiyat}, hafiza={}, son_islemler=[], son_degerler=[],
                          onceki_sonuclar=[], kisa=True, temel={"THYAO.IS": {"ad": "THY", "fk": 4.4, "fk_tur": "ileriye dönük"}},
                          haberler={"semboller": {"THYAO.IS": [haber]}, "genel": {"Borsa İstanbul": [haber]}})
        for parca in ("BAŞLANGIÇ KURGUN", "henüz yazmadın", "RSI14 61", "F/K 4.4", "15dk son 4 saat",
                      "THY yeni uçak aldı", "HABER BAŞLIKLARI"):
            self.assertIn(parca, m)
        # uzun/orta vadede 15 dakikalık veri gösterilmez
        m2 = talimat.mesaj(simdi_tr="x", gecen_gun=0, portfoy=portfoy, toplam=10000.0, satirlar=[],
                           fiyatlar={"THYAO.IS": fiyat}, hafiza={"kurgu": {"metin": "Kurgum"}}, son_islemler=[],
                           son_degerler=[], onceki_sonuclar=[])
        self.assertNotIn("15dk son 4 saat", m2)
        self.assertIn("Kurgum", m2)

    def test_sistem_yeni_kurallar(self):
        s = talimat.sistem("orta_riskli")
        self.assertIn("SIFIRDAN TESTİ", s)
        self.assertIn("baslangic_kurgusu", s)
        self.assertIn("15 dakikalık", talimat.sistem("kisa"))


if __name__ == "__main__":
    unittest.main()
