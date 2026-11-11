"""Yarışın sabit ayarları. Dengeleme gerekirse buradan değiştirilir."""

import os
from pathlib import Path

# Durum, rapor ve uygulama verisinin yazıldığı kök. Denemelerde YATIRIM_CIKTI ile başka klasöre yönlendirilir.
KOK = Path(os.environ.get("YATIRIM_CIKTI") or Path(__file__).resolve().parent.parent)
DURUM = KOK / "durum"
UYGULAMA_VERI = KOK / "docs" / "veri"

BASLANGIC_NAKIT_TL = 10_000.0
KOMISYON_ORANI = 0.002          # her alış ve satışta %0,2
MIN_ISLEM_TL = 10.0             # bundan küçük işlemler yapılmaz
TAZE_FIYAT_DAKIKA = 50          # fiyat bundan eskiyse piyasa kapalı sayılır
DEGERLEME_ARALIGI_SAAT = 3      # tur olmasa da tüm portföylerin değeri bu aralıkla kaydedilir (grafik için)
ERKEN_CALISMA_DAKIKA = 10       # zamanı bu kadar yaklaşan portföy de çalıştırılır (zamanlayıcı 30 dakikada bir uyanır)

# Modelin kendi hafızası, portföy başına toplam ~2.000 karakter
NOT_SINIRI = 1000
PLAN_SINIRI = 600
MESAJ_SINIRI = 400
IZLEME_SINIRI = 15

# Yarışan modeller. Anahtarı tanımlı olmayan model atlanır (portföyleri anahtar gelince başlar).
# Model adı GitHub değişkeniyle (ör. OPENAI_MODEL) değiştirilebilir.
MODELLER = {
    "deepseek": {"ad": "DeepSeek", "anahtar": "DEEPSEEK_API_KEY", "model_degiskeni": "DEEPSEEK_MODEL",
                 "varsayilan_model": "deepseek-v4-pro"},
    "chatgpt": {"ad": "ChatGPT", "anahtar": "OPENAI_API_KEY", "model_degiskeni": "OPENAI_MODEL",
                "varsayilan_model": "gpt-5.5"},
    "claude": {"ad": "Claude Opus", "anahtar": "ANTHROPIC_API_KEY", "model_degiskeni": "CLAUDE_MODEL",
               "varsayilan_model": "claude-opus-5-5"},
}
DEEPSEEK_ADRES = "https://api.deepseek.com"

# Her modelin 5 portföyü. gunler: kontrol edilebilecek haftanın günleri (0=Pazartesi ... 6=Pazar).
PORTFOYLER = {
    "uzun_riskli": {"ad": "Uzun vade · riskli", "tip": "uzun", "vade_gun": 91, "riskli": True,
                    "gunler": [4], "kontrol": "her cuma"},
    "uzun_risksiz": {"ad": "Uzun vade · risksiz", "tip": "uzun", "vade_gun": 91, "riskli": False,
                     "gunler": [4], "kontrol": "her cuma"},
    "orta_riskli": {"ad": "Orta vade · riskli", "tip": "orta", "vade_gun": 30, "riskli": True,
                    "gunler": [0, 2, 4], "kontrol": "pazartesi, çarşamba ve cuma"},
    "orta_risksiz": {"ad": "Orta vade · risksiz", "tip": "orta", "vade_gun": 30, "riskli": False,
                     "gunler": [0, 2, 4], "kontrol": "pazartesi, çarşamba ve cuma"},
    "kisa": {"ad": "Kısa vade · al-sat", "tip": "kisa", "vade_gun": None, "riskli": True,
             "gunler": [0, 1, 2, 3, 4, 5, 6], "kontrol": "günde en fazla 5 kez, saatleri sen seçersin"},
}
KISA_GUNLUK_SINIR = 5
VARSAYILAN_SAAT = "17:40"       # model saat vermezse (TR saati; kışın BIST ve ABD birlikte açık)

# Her turda gösterilen genel piyasa tablosu (yalnızca piyasası o an açık olanlar gösterilir)
GENEL_SEMBOLLER = {
    "Endeksler": ["XU100.IS", "XU030.IS", "^GSPC", "^IXIC", "^DJI", "^VIX", "^TNX"],
    "Emtia": ["GC=F", "SI=F", "CL=F", "HG=F"],
    "Döviz": ["USDTRY=X", "EURTRY=X", "EURUSD=X"],
    "Kripto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"],
}

# Kıyas: 10.000 TL ilk günden bunlara yatırılıp hiç dokunulmasaydı
KIYASLAR = {
    "BIST 100": "XU100.IS",
    "S&P 500": "^GSPC",
    "Altın": "GC=F",
    "Bitcoin": "BTC-USD",
    "Dolar": "USDTRY=X",
}
