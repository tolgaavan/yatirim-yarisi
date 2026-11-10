# Kaynak Sistemi

Bu klasör, proje bağlamının dayandığı kullanıcı veya proje tarafından sağlanan ham kaynakları saklar. Ajanın ürettiği çıktılar ham kaynak olarak değerlendirilmez.

## Klasörler

| Konum | İçeriği |
|---|---|
| `belgeler/` | PDF, Word, sunum ve metin belgeleri |
| `veriler/` | Excel, CSV, JSON ve diğer yapılandırılmış veriler |
| `gorseller/` | Ekran görüntüleri, grafikler, fotoğraflar ve çizimler |
| `ses-ve-video/` | Ses kayıtları, toplantı kayıtları ve videolar |
| `baglantilar.md` | İnternet sayfaları ve çevrim içi kaynaklar |
| `kaynak-indeksi.md` | Bütün gerçek kaynakların kayıt ve açıklama listesi |

Bu kategorilere uymayan bir kaynak ortaya çıkarsa yeni bir klasör oluşturulabilir. Yeni klasör bu dosyaya tanıtılmalıdır.

## Kaynak ekleme süreci

1. Kaynağın orijinal dosyasını uygun klasöre yerleştir.
2. Açıklayıcı ve tarih içeren bir dosya adı kullan.
3. Kaynağı `kaynak-indeksi.md` dosyasına kaydet.
4. Kaynağın nereden geldiğini, hangi döneme ait olduğunu ve ne için kullanılacağını belirt.
5. Kaynak taranmış veya doğrudan okunması zorsa metin tanıma uygulanmış sürüm ya da ayrı bir özet hazırlanabilir.
6. Kaynaktan çıkarılan kalıcı sonuçları, kullanıcı doğruladıktan sonra ilgili üst bağlam dosyasına işle.

## Biçim önerileri

- Yazılı ve düzenlenebilir bilgiler için Markdown veya düz metin tercih edilebilir.
- Tablolar için özgün Excel dosyası korunur; taşınabilirlik gerektiğinde ilgili sayfalar ayrıca CSV olarak dışa aktarılabilir.
- PDF veya Word belgesinin özgün kopyası korunur; sık kullanılacak sonuçlar ayrı bir Markdown özetine dönüştürülebilir.
- Taranmış PDF'ler için metin tanıma veya okunabilir özet gerekebilir.
- Görsel, ses ve video dosyalarının adı içerik ve tarihi açıklamalıdır.
- İnternet bağlantılarında erişim tarihi ve önemli sonuç kaydedilmelidir.

## Değişiklik kuralları

- Orijinal kaynak açıkça istenmedikçe değiştirilmez veya üzerine yazılmaz.
- Kaynak eklenir, taşınır, yeniden adlandırılır veya silinirse `kaynak-indeksi.md` aynı işlemde güncellenir.
- Kaynak içeriğinden üretilen yorum, analiz ve özet ham kaynak sayılmaz.
- Boş klasörlerin dağıtım paketinde korunmasını sağlayan `.gitkeep` dosyaları kaynak sayılmaz ve indekse eklenmez.
- Büyük veya hassas dosyaları eklemeden önce gizlilik, paylaşım ve depolama sınırlarını kontrol edin.
- Parola, erişim anahtarı ve gereksiz kişisel veri kaynak klasörüne eklenmemelidir.

## Örnek dosya adları

```text
pazar-arastirmasi-2026.pdf
instagram-verileri-2026-07_2026-09.xlsx
musteri-gorusmesi-2026-09-20.mp4
instagram-profil-istatistikleri-2026-09-20.png
```
