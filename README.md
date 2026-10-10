# Makro

Windows uygulaması; Python, Tkinter ve `pynput` kullanır. Lisans: MIT.

## Güncelleme bildirimi

Uygulama açılışta GitHub Releases sayfasındaki en son kararlı sürümü kontrol eder. Daha yeni bir sürüm varsa kullanıcıya bildirim gösterir ve onay verirse resmi Release sayfasını açar. Güncelleme kendiliğinden kurulmaz; kullanıcı yeni `AutoClicker.exe` dosyasını indirip mevcut dosyanın yerine koyar. Pencere ve kurulum adı Makro olarak gösterilir.

Kontrol yalnızca GitHub'ın herkese açık Releases API'sine yapılır. Uygulama bu kontrol sırasında kayıtları, klavye/fare verilerini veya kullanıcı adını göndermez. GitHub sunucuları normal web bağlantılarında IP adresini görebilir.

## Yeni sürüm yayımlama

1. `AutoClicker.py` içindeki `APP_VERSION` değerini artır (ör. `1.0.1` → `1.0.2`).
2. `AutoClicker.iss` içindeki `AppVersion` değerini de aynı sürüme yükselt.
3. Kaynak kodunu GitHub'daki `cryax-tr1/auto-clicker` deposuna yükle.
4. PyInstaller ile yeni `AutoClicker.exe` dosyasını oluştur.
5. Inno Setup 6 ile `BuildInstaller.ps1` çalıştırıp yeni `Makro-Setup-x.y.z.exe` dosyasını üret.
6. GitHub deposunda **Releases → Draft a new release** seç.
7. Sürüm etiketi olarak `v1.0.1` gibi yeni sürüm numarasını gir.
8. Üretilen kurulum dosyasını Release varlığı olarak ekle ve yayımla.

İlk sürüm için de Release yayımlanmalıdır. Release yayımlanmadan güncelleme kontrolü yeni sürüm bulamaz. Her yeni sürümde uygulama, açılışta bu sürümü bildirir.

## Kurulum dosyası oluşturma

Windows makinesine [Inno Setup 6](https://jrsoftware.org/isdl.php) kurun. Önce `AutoClicker.spec` ile PyInstaller üzerinden `release\AutoClicker.exe` oluşturun, sonra PowerShell'den `powershell -ExecutionPolicy Bypass -File .\BuildInstaller.ps1` çalıştırın. Kurucu `release\Makro-Setup-1.0.1.exe` olarak oluşturulur. Kurulum kullanıcı profiline yapılır; yönetici yetkisi istemez. Kurulum sihirbazı lisans onayı, dil, hedef klasör, masaüstü kısayolu ve kaldırma seçeneği sağlar. Ana ekranda geliştirici adı ve tıklanabilir Discord daveti gösterilir.
