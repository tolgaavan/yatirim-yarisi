import datetime as dt
import unittest

from bot import ayarlar, portfoy as pf, takvim, talimat, veri

IST = veri.ISTANBUL
B = ayarlar.BASLANGIC_NAKIT_TL


def fiyat(f, acik=True, islem=True):
    return {"fiyat_tl": f, "acik": acik, "islem": islem, "zaman": "x"}


class PortfoyTest(unittest.TestCase):
    def setUp(self):
        self.p = pf.yeni_portfoy("2026-01-01T00:00:00+00:00")

    def test_alis_komisyon_duser(self):
        pf.al(self.p, "AAA", 5000, fiyat(10))
        self.assertAlmostEqual(self.p["nakit_tl"], B - 5000 * (1 + ayarlar.KOMISYON_ORANI))
        self.assertAlmostEqual(self.p["pozisyonlar"]["AAA"]["adet"], 500)

    def test_nakitten_fazla_alis_kirpilir(self):
        pf.al(self.p, "AAA", 10 ** 9, fiyat(10))
        self.assertAlmostEqual(self.p["nakit_tl"], 0, places=6)
        toplam, _ = pf.degerle(self.p, {"AAA": fiyat(10)})
        self.assertAlmostEqual(toplam, B / (1 + ayarlar.KOMISYON_ORANI))

    def test_kapali_piyasa_ve_endeks_reddedilir(self):
        self.assertIn("REDDEDİLDİ", pf.al(self.p, "AAA", 100, fiyat(10, acik=False)))
        self.assertIn("REDDEDİLDİ", pf.al(self.p, "^GSPC", 100, fiyat(10, islem=False)))
        self.assertIn("REDDEDİLDİ", pf.al(self.p, "YOK", 100, None))
        self.assertEqual(self.p["nakit_tl"], B)

    def test_satis_tamami_ve_kar(self):
        pf.al(self.p, "AAA", 5000, fiyat(10))
        pf.sat(self.p, "AAA", 100, fiyat(12))
        self.assertNotIn("AAA", self.p["pozisyonlar"])
        self.assertAlmostEqual(self.p["nakit_tl"], B - 5000 * 1.002 + 6000 * (1 - 0.002))

    def test_kismi_satis(self):
        pf.al(self.p, "AAA", 5000, fiyat(10))
        pf.sat(self.p, "AAA", 40, fiyat(10))
        self.assertAlmostEqual(self.p["pozisyonlar"]["AAA"]["adet"], 300)

    def test_json_ayristirma(self):
        self.assertEqual(talimat.ayristir('```json\n{"a": 1}\n```')["a"], 1)
        self.assertEqual(talimat.ayristir('Düşündüm.\n{"a": {"b": 2}}\nbitti')["a"]["b"], 2)
        with self.assertRaises(Exception):
            talimat.ayristir("json yok")


def ist(y, a, g, s, d=0):
    return dt.datetime(y, a, g, s, d, tzinfo=IST)


class TakvimTest(unittest.TestCase):
    # 2026-11-10 Salı
    def test_uzun_cumaya_alinir_saat_korunur(self):
        z, _ = takvim.sonraki("uzun_riskli", "2026-11-11 15:00", ist(2026, 11, 10, 12), [])
        self.assertEqual(z, ist(2026, 11, 13, 15))

    def test_uzun_ayni_gun_tekrar_bakilmaz(self):
        z, _ = takvim.sonraki("uzun_risksiz", "2026-11-13 17:00", ist(2026, 11, 13, 11), [])
        self.assertEqual(z, ist(2026, 11, 20, 17))

    def test_orta_pzt_crs_cuma(self):
        z, _ = takvim.sonraki("orta_riskli", "2026-11-12 11:00", ist(2026, 11, 10, 12), [])
        self.assertEqual(z, ist(2026, 11, 13, 11))  # perşembe -> cuma
        z, not_ = takvim.sonraki("orta_risksiz", None, ist(2026, 11, 10, 12), [])
        self.assertEqual(z, ist(2026, 11, 11, 17, 40))
        self.assertTrue(not_)

    def test_kisa_en_az_30_dakika(self):
        z, _ = takvim.sonraki("kisa", "2026-11-10 12:05", ist(2026, 11, 10, 12), [])
        self.assertEqual(z, ist(2026, 11, 10, 12, 30))

    def test_kisa_gunluk_sinir(self):
        turlar = [ist(2026, 11, 10, s).isoformat() for s in (10, 11, 12, 13, 14)]
        z, not_ = takvim.sonraki("kisa", "2026-11-10 16:00", ist(2026, 11, 10, 14), turlar)
        self.assertEqual(z, ist(2026, 11, 11, 10))
        self.assertIn("sınır", not_)


class SeansTest(unittest.TestCase):
    def test_bist_ve_tl_kuru(self):
        self.assertTrue(veri.seans_acik("THYAO.IS", ist(2026, 11, 10, 11)))
        self.assertFalse(veri.seans_acik("THYAO.IS", ist(2026, 11, 10, 22)))
        self.assertFalse(veri.seans_acik("USDTRY=X", ist(2026, 11, 10, 22)))
        self.assertFalse(veri.seans_acik("THYAO.IS", ist(2026, 11, 14, 11)))  # cumartesi

    def test_abd(self):
        self.assertFalse(veri.seans_acik("AAPL", ist(2026, 11, 10, 17)))   # kışın 17:30'da açılır
        self.assertTrue(veri.seans_acik("AAPL", ist(2026, 11, 10, 18)))
        self.assertTrue(veri.seans_acik("^GSPC", ist(2026, 11, 10, 23, 30)))

    def test_bilinmeyen_tazelige_birakilir(self):
        self.assertIsNone(veri.seans_acik("BTC-USD", ist(2026, 11, 10, 3)))
        self.assertIsNone(veri.seans_acik("GC=F", ist(2026, 11, 10, 3)))


if __name__ == "__main__":
    unittest.main()
