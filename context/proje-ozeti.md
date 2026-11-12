# Proje Özeti

Bu dosya projenin ne olduğunu, neden var olduğunu, kapsamını ve mevcut durumunu açıklar.

## Projenin adı

Yapay Zekâ Yatırım Yarışı (GitHub deposu: `tolgaavan/yatirim-yarisi`)

## Kısa tanım

DeepSeek, ChatGPT ve Claude Opus hayali parayla yarışır. Her modelin 5 portföyü vardır, her biri 10.000 TL ile başlar:
uzun vade (3 ay) riskli ve risksiz, orta vade (1 ay) riskli ve risksiz, kısa vade (al-sat). Program GitHub'da 30
dakikada bir uyanır, kontrol zamanı gelen portföy için modele gerçek piyasa verisini ve portföyünü gösterip sorar,
verdiği alım-satım kararlarını o anki gerçek fiyatlardan, komisyonla hayali olarak uygular. Gerçek para yoktur.

## Ana amaç

Hangi modelin yatırımda daha başarılı olduğunu kıyaslamak. Sonuçlar ayrıca BIST 100, S&P 500, altın, Bitcoin ve
dolar "al ve bekle" kıyaslarıyla karşılaştırılır.

## Kapsama dahil olanlar

- Yahoo Finance sembolü olan her şey: ABD ve Türk hisseleri, fonlar, emtialar, döviz, kripto
- Modelin portföy başına kendi tuttuğu hafıza (notlar, plan, sonraki tura mesaj, izleme listesi) ve kendi seçtiği sonraki kontrol zamanı
- Telefon uygulaması (yalnızca sonuç gösterir, bir de "Şimdi tekrar sor" düğmesi)

## Kapsam dışında kalanlar

- Gerçek para, gerçek aracı kurum bağlantısı, açığa satış, kaldıraç, haberler

## Mevcut durum

2026-11-10: Kod üç model × 5 portföy yapısına çevrildi, telefon uygulaması yazıldı; birim testleri ve sahte kararla
(`--deneme`) gerçek piyasa verisi üzerinde deneme geçti.

2026-11-11: Üç API anahtarı geldi ve ücretsiz model listesi sorgusuyla doğrulandı. Modeller: DeepSeek
`deepseek-v4-pro`, ChatGPT `gpt-5.5`, Claude `claude-opus-5-5`. Yahoo'nun ara sıra boş döndürdüğü semboller artık
yeniden isteniyor. Depo (`tolgaavan/yatirim-yarisi`, herkese açık) açıldı, anahtarlar GitHub gizli ayarlarında,
telefon sayfası GitHub Pages'te. Mini test (her modele yalnızca kısa vade, 3 soru) yerelde geçti: soru başına
~1.800-2.800 girdi ve ~600-1.700 çıktı token. Zamanlayıcı açıldı, yarış başladı: diğer 4 portföyün ilk turu
2026-11-11 gece GitHub'da hatasız çalıştı (bir GitHub Actions/Pages kesintisi bitince). 15 portföyün hepsi başladı;
telefon sayfası https://tolgaavan.github.io/yatirim-yarisi/ yayında.

2026-11-12: Kullanıcının isteğiyle modellere kıdemli portföy yöneticisi rolü verildi, telefona Geçmiş bölümü (tur
özeti ve işlem gerekçeleri) eklendi, riskli uzun/orta portföylerine zorunlu çeşitlilik (döviz nakit, Türk ve ABD
hissesi) ve kısa vadeye 1-2 varlık yönergesi getirildi. 3 soruluk gerçek testten sonra önceki turlar test sayılıp
tüm portföyler sıfırlandı ve yarış 2026-11-12 akşamı baştan başladı.

## Kullanıcıya bildirilenler ve açık kalan noktalar

- ChatGPT Plus ve Claude abonelikleri API'yi kapsamaz; platform.openai.com ve console.anthropic.com'da ayrı API kredisi gerekir. DeepSeek API ucuzdur ama ücretlidir.
- API anahtarları sohbete yazılmamalı; 2026-11-11'de kullanıcı üç anahtarı sohbete yazdı, Claude yenilenmelerini önerdi (henüz yenilenmedi; yenilenince GitHub gizli ayarları da güncellenmeli).
- Anahtarlar `gh secret set DEEPSEEK_API_KEY` (ve `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) ile GitHub gizli ayarlarına kaydedilir.
- Para karşılığı masraf doğrulanmadı (token sayıları mini testte ölçüldü); ilk haftanın gerçek token kullanımıyla (`kararlar.jsonl` içindeki `kullanim`) kontrol edilecek. Hafıza sınırı da ilk haftaya bakılıp ayarlanabilir.
- Vade bitince (3 ay / 1 ay) ne olacağı belirlenmedi; şimdilik portföyler çalışmaya devam eder.
- Risksiz portföylerde TL nakit faiz getirmez (Türkiye'de mevduat/para piyasası fonu Yahoo'da yok).

## Önemli konumlar

- `bot/ayarlar.py`: tüm sabit ayarlar (modeller, 5 portföy tanımı, başlangıç parası, komisyon, hafıza sınırları, semboller, kıyaslar)
- `bot/veri.py`: Yahoo Finance fiyatları ve piyasa seans saatleri
- `bot/takvim.py`: sonraki kontrol zamanının portföy kurallarına uydurulması
- `bot/talimat.py`: modellere giden talimat ve mesaj, cevabın okunması
- `bot/modeller.py`: DeepSeek / OpenAI / Anthropic çağrıları
- `bot/portfoy.py`: hayali portföy, alış/satış, değerleme
- `bot/calistir.py`: bir çalışma (`python -m bot.calistir`, `--deneme`, `--zorla`, `--model`, `--portfoy`)
- `bot/rapor.py`: `README.md` ve uygulama verisi `docs/veri/ozet.json`
- `docs/`: telefon uygulaması (GitHub Pages: https://tolgaavan.github.io/yatirim-yarisi/)
- `durum/`: `takvim.json`, `degerler.jsonl` (grafik), ve her `durum/<model>/<portföy>/` altında portföy, hafıza, işlemler, modelin tam cevapları, son gönderilen soru
- `.github/workflows/tur.yml`: 30 dakikada bir çalışan zamanlayıcı ve elle çalıştırma (model/portföy seçilebilir)
- `tests/`: birim testleri (`python -m unittest discover -s tests -t .`)
