# Proje Bağlamı Haritası

Bu dosya `context/` klasörünün ana haritasıdır. Proje bağlamını tek başına tekrar etmez; hangi bilginin nerede olduğunu ve ne zaman okunacağını gösterir.

## Okuma düzeni

### Her görevde oku

- `proje-ozeti.md`: Projenin ne olduğunu, kapsamını ve mevcut durumunu anlamak için.
- `kurallar-ve-sinirlar.md`: Her çalışmada geçerli sınırları ve zorunlu kuralları uygulamak için.

### Göreve göre oku

- `hedefler.md`: Önceliklendirme, planlama, strateji veya başarı değerlendirmesi yapılırken.
- `kararlar.md`: Yeni karar alınırken, önceki bir karar sorgulanırken veya çelişki ihtimali varsa.
- `kaynaklar/README.md`: Kaynak eklenecekse veya kaynaklara dayalı inceleme yapılacaksa.
- `kaynaklar/kaynak-indeksi.md`: Belirli bir PDF, tablo, görsel, bağlantı, ses veya video aranıyorsa.

## Mevcut bağlam haritası

| Konum | İçeriği | Ne zaman okunmalı? |
|---|---|---|
| `proje-ozeti.md` | Projenin tanımı, amacı, kapsamı ve mevcut durumu | Her görevde |
| `hedefler.md` | Aktif hedefler, öncelikler ve başarı ölçütleri | Planlama ve önceliklendirmede |
| `kurallar-ve-sinirlar.md` | Kalıcı kurallar, sınırlar, yasaklar ve yetki gerektiren alanlar | Her görevde |
| `kararlar.md` | Kesinleşmiş kararlar, gerekçeleri ve durumları | Karar veya değişiklik öncesinde |
| `kaynaklar/README.md` | Kaynak sisteminin kullanım ve düzenleme kuralları | Kaynak işlemlerinde |
| `kaynaklar/kaynak-indeksi.md` | Projede bulunan gerçek kaynakların envanteri | Kanıt veya kaynak aranırken |
| `kaynaklar/baglantilar.md` | İnternet ve çevrim içi kaynak kayıtları | Dış bağlantı gerektiğinde |

## Yeni bağlam dosyası ekleme

Dosya isimleri zorunlu değildir. Projenin ihtiyacına göre `q4-plani.md`, `yeni-yil-hedefleri.md`, `hedef-kitle.md`, `ekip.md` veya başka bir dosya oluşturulabilir.

Yeni bir bağlam dosyası eklendiğinde:

1. Dosyaya açık ve anlaşılır bir ad ver.
2. Dosyanın başında amacını belirt.
3. Dosyayı bu haritaya ekle.
4. Haritada ne içerdiğini ve hangi durumda okunacağını yaz.
5. Dosya taşınır, yeniden adlandırılır, amacı değişir veya silinirse haritayı aynı işlemde güncelle.

Bir dosyanın yalnızca içeriği güncellendiyse ve amacı değişmediyse haritayı değiştirmek gerekmez.

## Haritalama ilkesi

- `context/` içindeki her anlamlı bağlam dosyası bu ana haritadan doğrudan veya bir alt `README.md` üzerinden ulaşılabilir olmalıdır.
- Ana haritada tek tek ham kaynaklar listelenmez; onların envanteri `kaynaklar/kaynak-indeksi.md` içinde tutulur.
- Haritada bulunmayan dosyalar kalıcı proje bağlamının güvenilir bir parçası kabul edilmeden önce incelenmelidir.
- Çelişkili veya eski bilgi fark edilirse sessizce değiştirilmemeli; kullanıcıya bildirilmelidir.

## Güncelleme ilkesi

- Kesinleşen kalıcı bilgiler ilgili mevcut dosyaya işlenir.
- Geçici fikirler, reddedilmiş seçenekler ve doğrulanmamış varsayımlar kalıcı bağlama eklenmez.
- Yeni dosya yalnızca mevcut dosyalardan hiçbirinin amacına uymuyorsa oluşturulur.
- Bağlamın tamamı her görevde denetlenmez; kullanıcı “bağlamı denetle” dediğinde kapsamlı denetim yapılır.

