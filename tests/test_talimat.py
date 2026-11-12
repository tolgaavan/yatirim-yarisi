import unittest

from bot import talimat


class ZorunluCesitlilikTesti(unittest.TestCase):
    def test_gruplar(self):
        self.assertEqual(talimat.varlik_grubu("USDTRY=X"), "doviz")
        self.assertEqual(talimat.varlik_grubu("EURUSD=X"), "doviz")
        self.assertEqual(talimat.varlik_grubu("THYAO.IS"), "turk")
        self.assertEqual(talimat.varlik_grubu("AAPL"), "abd")
        self.assertEqual(talimat.varlik_grubu("SPY"), "abd")
        self.assertIsNone(talimat.varlik_grubu("GLD"))
        self.assertIsNone(talimat.varlik_grubu("GC=F"))
        self.assertIsNone(talimat.varlik_grubu("BTC-USD"))
        self.assertIsNone(talimat.varlik_grubu("^GSPC"))

    def test_eksik(self):
        poz = {"USDTRY=X": {"adet": 1}, "AAPL": {"adet": 0.01}, "BTC-USD": {"adet": 1}}
        self.assertEqual(talimat.eksik_gruplar(poz), ["Türk hissesi/fonu"])
        self.assertEqual(len(talimat.eksik_gruplar({})), 3)

    def test_hangi_portfoyler(self):
        self.assertTrue(talimat.zorunlu_mu("uzun_riskli"))
        self.assertTrue(talimat.zorunlu_mu("orta_riskli"))
        self.assertFalse(talimat.zorunlu_mu("uzun_risksiz"))
        self.assertFalse(talimat.zorunlu_mu("kisa"))

    def test_talimat_icerigi(self):
        self.assertIn("ZORUNLU ÇEŞİTLİLİK", talimat.sistem("orta_riskli"))
        self.assertNotIn("ZORUNLU ÇEŞİTLİLİK", talimat.sistem("orta_risksiz"))
        self.assertIn("KISA VADE YAKLAŞIMI", talimat.sistem("kisa"))
        self.assertIn("tur_ozeti", talimat.sistem("kisa"))


if __name__ == "__main__":
    unittest.main()
