# PulseMacro Studio

Modern makro kaydetme ve oynatma uygulaması. Windows üzerinde Python, Tkinter ve `pynput` kullanır. Lisans: MIT.

Makro kütüphanesinde fare/klavye eylemlerini kaydedebilir; hız ayarıyla, tek sefer veya belirli/sınırsız tekrar halinde oynatabilirsiniz. Global kısayollar, sürekli sol/sağ tıklama, kayıtları dışarıdan açma ve silme özellikleri bulunur. Hız ve tekrar tercihleri uygulama ayarlarında saklanır.

## Güncelleme bildirimi

Uygulama açılışta GitHub Releases sayfasındaki en son kararlı sürümü kontrol eder. Daha yeni bir sürüm varsa yüklü ve güncel sürüm numaralarını ve çalışan programın konumunu gösterir. Release içinde kurulum dosyası varsa doğrudan `PulseMacro-Setup-x.y.z.exe` indirmesi açılır; indirme tamamlanınca kurulum dosyasını çalıştırıp mevcut sürümün üzerine kurun. Güncelleme kendiliğinden kurulmaz. Sürüm numaraları aynıysa güncelleme bildirimi gösterilmez.

Kontrol yalnızca GitHub'ın herkese açık Releases API'sine yapılır. Uygulama bu kontrol sırasında kayıtları, klavye/fare verilerini veya kullanıcı adını göndermez. GitHub sunucuları normal web bağlantılarında IP adresini görebilir.

## Yeni sürüm yayımlama

1. `AutoClicker.py` ve `AutoClicker.iss` içindeki sürüm değerini artır.
2. Kaynak kodunu GitHub'daki `cryax-tr1/auto-clicker` deposuna yükle.
3. PyInstaller ile `AutoClicker.spec` dosyasını derle; yeni `PulseMacro.exe`, `dist` klasörüne yazılır.
4. Inno Setup 6 ile `BuildInstaller.ps1` çalıştır. Betik güncel `dist\PulseMacro.exe` dosyasını `release` klasörüne kopyalayıp yeni `PulseMacro-Setup-x.y.z.exe` dosyasını üretir.
5. GitHub deposunda **Releases → Draft a new release** seç.
6. Sürüm etiketi olarak `v1.1.2` gibi yeni sürüm numarasını gir.
7. Üretilen kurulum dosyasını Release varlığı olarak ekle ve yayımla.

v1.1.2 ile makro satırlarına dosya konumunu açma ve silme düğmeleri eklenir; Windows tıklama motorunun zamanlaması iyileştirilir. Release yayımlanmadan güncelleme kontrolü yeni sürüm bulamaz. Her yeni sürümde uygulama açılışta bu sürümü kontrol eder.

## Kurulum dosyası oluşturma

Windows makinesine [Inno Setup 6](https://jrsoftware.org/isdl.php) kurun. Inno Setup Compiler, `.iss` kurulum tarifini Windows kurulum `.exe` dosyasına dönüştürür; son kullanıcıların uygulamayı kullanmak için bu derleyiciyi kurması gerekmez. Önce `AutoClicker.spec` ile PyInstaller derlemesini çalıştırıp `dist\PulseMacro.exe` oluşturun, sonra PowerShell'den `powershell -ExecutionPolicy Bypass -File .\BuildInstaller.ps1` çalıştırın. Kurucu `release\PulseMacro-Setup-1.1.2.exe` olarak oluşturulur. Kurulum kullanıcı profiline yapılır; yönetici yetkisi istemez. Kurulum sihirbazı lisans onayı, dil, hedef klasör, masaüstü kısayolu ve kaldırma seçeneği sağlar.
