---
name: proje-hafizasi
description: Kullanıcı “hafızayı güncelle”, “bağlamı denetle”, “kaynakları denetle” veya aynı anlama gelen bir ifade kullandığında proje bağlamını ve kaynak kayıtlarını güvenli biçimde güncellemek ya da denetlemek için kullan.
---

# Proje Hafızası

Bu beceri üç çalışma biçimine sahiptir:

1. Hafızayı güncelleme
2. Bağlamı denetleme
3. Kaynakları denetleme

Kullanıcının ifadesine en yakın çalışma biçimini seç. İstek belirsizse hangi işlemin istendiğini sor.

## Ortak ilkeler

- Önce proje kökündeki `CLAUDE.md` ve `context/README.md` dosyalarını oku.
- Yalnızca kesinleşmiş, gelecekte tekrar kullanılacak proje bilgisini kalıcı bağlama işle.
- Geçici fikirleri, reddedilmiş seçenekleri ve doğrulanmamış varsayımları kalıcı bağlama ekleme.
- Kullanıcının açıkça kesinleştirmediği hedef, kural, karar veya sınırı kendiliğinden değiştirme.
- Sohbetin tamamını veya uzun sohbet özetini bağlam dosyalarına kopyalama.
- Mevcut uygun dosya varken gereksiz yeni dosya oluşturma.
- Silme, kapsamlı yeniden yazma veya anlamı değiştiren işlem öncesinde kullanıcıdan onay al.
- İşlem sonunda yapılan ve önerilen değişiklikleri dosya yollarıyla birlikte kısa şekilde bildir.

## Hafızayı güncelleme

Kullanıcı “hafızayı güncelle” dediğinde:

1. Mevcut konuşmada kesinleşen hedefleri, kararları, kuralları, sınırları ve kalıcı proje bilgilerini belirle.
2. Bunları `context/README.md` haritasındaki mevcut bilgilerle karşılaştır.
3. Kesinleşmiş bilgileri ilgili mevcut bağlam dosyasına işle.
4. Kalıcı olup olmadığı belirsiz bilgileri ayrı listele ve kullanıcıya sor.
5. Yeni dosya yalnızca mevcut dosyaların hiçbirine uymayan ayrı bir konu varsa oluştur.
6. Dosya oluşturur, taşır, yeniden adlandırır, amacını değiştirir veya silersen `context/README.md` haritasını aynı işlemde güncelle.
7. Yalnızca dosya içeriği değişmiş ve amacı aynı kalmışsa ana haritayı değiştirme.
8. Kullanıcı tarafından yeni bir kaynak eklenmediyse `kaynak-indeksi.md` dosyasına dokunma.
9. Sonunda hangi kalıcı bilginin hangi dosyaya işlendiğini bildir.

## Bağlamı denetleme

Kullanıcı “bağlamı denetle” dediğinde:

1. `context/README.md` haritasını ve haritada gösterilen bağlam dosyalarını incele.
2. Haritada bulunmayan, artık var olmayan, taşınmış veya yeniden adlandırılmış bağlam dosyalarını belirle.
3. Dosyalar arasındaki çelişkileri, yinelenen bilgileri ve güncelliğini yitirmiş olabilecek kayıtları listele.
4. Geçici fikirlerin yanlışlıkla kalıcı bağlama girip girmediğini kontrol et.
5. Açık ve risksiz harita yolu düzeltmelerini yap.
6. Projenin anlamını, hedeflerini veya kararlarını değiştirecek düzeltmeleri uygulamadan önce kullanıcıya öneri sun.
7. Silme işlemini açık onay olmadan gerçekleştirme.
8. Denetim sonunda bulguları `düzeltildi`, `onay bekliyor` ve `bilgi gerekiyor` başlıklarıyla özetle.

## Kaynakları denetleme

Kullanıcı “kaynakları denetle” dediğinde:

1. `context/kaynaklar/README.md` ve `kaynak-indeksi.md` dosyalarını oku.
2. `belgeler/`, `veriler/`, `gorseller/` ve `ses-ve-video/` klasörlerindeki gerçek kaynakları indeksle karşılaştır.
3. Boş klasörleri koruyan `.gitkeep` dosyalarını gerçek kaynak olarak değerlendirme.
4. `baglantilar.md` kayıtlarının kaynak indeksinde karşılığı olup olmadığını kontrol et.
5. İndekste bulunmayan, yolu değişmiş, silinmiş veya yinelenmiş kaynakları belirle.
6. Kaynakların tür, tarih, dönem, çıkış noktası, kullanım amacı ve durum bilgilerindeki eksikleri listele.
7. Orijinal kaynakların içeriğini değiştirme.
8. Kaynağın doğruluğunu veya güncelliğini tahmin etme; şüpheli durumları kullanıcıya bildir.
9. Açık yol ve kayıt hatalarını düzelt; kaynak silme veya anlam değişikliği için onay iste.
10. Denetim sonunda yapılan değişiklikleri ve kullanıcıdan beklenen kararları özetle.
