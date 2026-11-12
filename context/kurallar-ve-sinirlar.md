# Kurallar ve Sınırlar

Bu dosya projede her zaman dikkate alınması gereken kalıcı kuralları, sınırları ve yasakları içerir.

## Zorunlu kurallar

<!-- Her çalışmada uygulanması gereken proje kuralları. -->

## Yapılmaması gerekenler

<!-- Kesin yasakları ve kaçınılması gereken davranışları yazın. -->

## Bütçe, süre ve kaynak sınırları

<!-- Bütçe, süre veya araç sınırları. -->

## Hukuki, güvenlik ve gizlilik sınırları

- (2026-11-12, kullanıcı kararı) APK imza bilgileri (`APK_IMZA_B64`, `APK_IMZA_SIFRESI`) GitHub'da kalıcı tutulmaz: yalnızca derleme sırasında konur, derleme bitince silinir. GitHub'da kalıcı duran gizli bilgiler yalnızca üç model API anahtarıdır (yarışın çalışması için şart).
- İmza anahtarı yalnızca bilgisayarda, `C:/Users/Tolga/dev/yatirim-imza` klasöründedir; silinmemeli (aynı imza olmadan yeni APK telefondakinin üzerine kurulamaz). Depoya konmaz.

## Kullanıcı onayı gerektiren işlemler

Yok. Kullanıcı 2026-11-07 tarihinde tüm izinleri kalıcı olarak önceden verdi. Ajanlar hiçbir işlem için (silme, üzerine yazma, yayımlama, GitHub, commit/push, bilgisayar kontrolü, paket kurma dahil) izin veya onay istemez; doğrudan uygular. Bu konu kullanıcıyla tekrar konuşulmaz.

