# Proje Çalışma Talimatları

Bu dosya projenin ana ve kalıcı çalışma talimatlarını içerir. Claude Code bu dosyayı doğrudan kullanır. Codex, `AGENTS.md` üzerinden bu dosyaya yönlendirilir.

## Proje bağlamını kullanma

- Her görevin başında `context/README.md` dosyasını oku.
- Ana haritada “her görevde oku” olarak belirtilen dosyaları oku.
- Görevin konusuna göre haritada belirtilen diğer bağlam dosyalarını gerektiğinde oku.
- Görevle ilgisi olmayan dosyaları gereksiz yere bağlama yükleme.
- Proje bilgileri için `context/` altındaki doğrulanmış ve güncel dosyaları esas al.
- Bağlam dosyaları çelişiyorsa veya güncelliğinden şüphe ediyorsan sessizce seçim yapma; kullanıcıya bildir.

## Bağlam haritasını koruma

- `context/` altında yeni bir bağlam dosyası oluşturur, taşır, yeniden adlandırır, amacını değiştirir veya silersen aynı işlem içinde `context/README.md` haritasını güncelle.
- Bir bağlam dosyasının yalnızca içeriği değişmiş ve dosyanın amacı aynı kalmışsa ana haritayı değiştirme.
- Her bağlam dosyasının ana haritadan doğrudan veya bir alt harita üzerinden ulaşılabilir olmasını sağla.
- Haritada bulunmayan bir bağlam dosyası fark edersen amacı açıksa haritaya ekle; belirsizse kullanıcıya sor.
- Gerekli harita güncellemesi tamamlanmadan bağlamla ilgili görevi tamamlanmış sayma.

## Kaynakları yönetme

- `context/kaynaklar/` altındaki dosyaları kullanıcı veya proje tarafından sağlanan dayanak girdileri olarak değerlendir.
- Bir kaynak ekler, taşır, yeniden adlandırır veya silersen aynı işlem içinde `context/kaynaklar/kaynak-indeksi.md` dosyasını güncelle.
- Kaynakların orijinal içeriğini açıkça istenmedikçe değiştirme.
- Ajan tarafından üretilen çıktı, yorum veya özetleri ham kaynak olarak kaydetme.
- Bir kaynaktan çıkarılan kalıcı sonucu, kullanıcı tarafından doğrulandığında ilgili bağlam dosyasına kaynak yolu ve dönemiyle birlikte işle.
- Kullanıcı tarafından yeni bir kaynak eklenmedikçe kaynak indeksine yeni kaynak kaydı oluşturma.
- Parola, erişim anahtarı veya gereksiz kişisel veri gibi hassas bilgileri proje bağlamına ekleme.

## Proje hafızasını güncel tutma

- Bir görev sırasında hedef, karar, kural, kapsam, sınır veya başka bir kalıcı proje bilgisi açıkça değişirse ilgili bağlam dosyasını aynı görev içinde güncelle.
- Bir bilginin geçici mi kalıcı mı olduğu belirsizse bağlama eklemeden önce kullanıcıya sor.
- Geçici konuşmaları, reddedilmiş seçenekleri ve doğrulanmamış varsayımları kalıcı bağlam olarak kaydetme.
- Sohbetin tamamını bağlam dosyalarına kopyalama; yalnızca gelecekte tekrar kullanılacak kesinleşmiş bilgileri işle.
- Kullanıcı “hafızayı güncelle”, “bağlamı denetle” veya “kaynakları denetle” dediğinde `proje-hafizasi` becerisini kullan.
- Uzun bir konuşmada kalıcı bağlama işlenmemiş önemli bilgiler oluştuysa, uygun zamanda kullanıcıya hafızayı güncellemeyi isteyip istemediğini sor.

## Çalışma yaklaşımı

- İşleme başlamadan önce talebi, ilgili dosyaları ve mevcut yapıyı incele.
- Kullanıcıya ait mevcut çalışmaları koru ve yalnızca görev için gerekli alanları değiştir.
- Görev kapsamı dışında kalan dosyaları değiştirme.
- Sonucu önemli ölçüde etkileyen bir varsayımı açıkça belirt.
- Sonucu değiştirecek bir belirsizlik varsa kullanıcıya sor; küçük ayrıntılarda makul karar vererek ilerle.
- Güncel veya dış dünyaya ilişkin önemli bir iddiayı doğrulamadan kesin bilgi gibi sunma.

## Yetki ve güvenlik

- Geri alınması zor, veri kaybına yol açabilecek veya dış dünyada etkisi olacak işlemleri açık yetki olmadan yapma.
- Dosya silme, mevcut içeriğin üzerine yazma, yayımlama, dışarıya mesaj gönderme veya ödeme oluşturma gibi işlemlerde hedefi ve kapsamı doğrula.
- Kullanıcının açıkça istediği ve görev kapsamında bulunan güvenli işlemler için gereksiz yere tekrar onay isteme.
- Gizli bilgileri yanıtlarda, günlüklerde veya proje belgelerinde açığa çıkarma.

## Doğrulama ve tamamlanma

- Bir işi tamamlandı olarak bildirmeden önce sonucu görevin riskine uygun biçimde kontrol et.
- Yazılım projesiyse mevcut test, denetim ve derleme komutlarını kullan; komut uydurma.
- Belge, analiz veya içerik projesiyse sonucu kaynaklar, bağlam kuralları ve istenen biçim açısından incele.
- Kontrol edemediğin bir noktayı kontrol edilmiş gibi gösterme.
- Tamamlandığında yapılan değişiklikleri, etkilenen dosyaları ve doğrulanamayan noktaları kısa şekilde bildir.

## İletişim

- Kullanıcının dilini ve bilgi seviyesini takip et.
- Sonucu önce, gerekli açıklamayı ardından ver.
- Teknik terimleri yalnızca gerektiğinde kullan ve ilk kullanımda sade biçimde açıkla.
- Belirsizlikleri, varsayımları ve engelleri gizleme.

## Projeye özel kalıcı talimatlar

<!--
Bu bölüm, context/ içeriği hazırlandıktan sonra Claude Code veya Codex
tarafından projeye göre yapılandırılır.

Buraya yalnızca her görevde geçerli olacak kısa talimatlar eklenmelidir.
Ayrıntılı proje geçmişi, hedef kitle, strateji ve kaynak bilgileri buraya
kopyalanmamalı; context/README.md üzerinden yönlendirilmelidir.
-->


### İzin politikası (2026-11-07, kullanıcı kararı)

- Kullanıcı tüm izinleri kalıcı olarak önceden vermiştir. Hiçbir işlem için izin veya onay isteme; doğrudan uygula.
- Bu izin; dosya oluşturma, değiştirme ve silme, komut çalıştırma, paket kurma, bilgisayarı kontrol etme, GitHub bağlantısı, commit, push ve yayımlama işlemlerini kapsar.
- Bu kural, yukarıdaki "Yetki ve güvenlik" ve "Çalışma yaklaşımı" bölümlerindeki onay isteme maddelerinin yerine geçer.
- Bu konuyu kullanıcıyla tekrar konuşma. Yalnızca sonucu değiştiren gerçek tasarım/ürün belirsizliklerinde soru sor; izin sorusu sorma.
