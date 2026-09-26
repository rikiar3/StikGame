# StikGame

StikGame mengubah browser ponsel menjadi controller game untuk PC Windows. PC menjalankan server; ponsel membuka halaman controller melalui Wi-Fi yang sama. Input diteruskan ke gamepad Xbox 360 virtual di PC.

## Persyaratan

- Windows pada PC yang akan menjalankan gamepad virtual
- Python 3.10 atau lebih baru dan `pip`
- Driver ViGEmBus terpasang di PC agar gamepad virtual dapat dibuat
- Ponsel dan PC tersambung ke jaringan Wi-Fi yang sama

## Menjalankan dari source

Dari folder proyek, buat virtual environment dan pasang dependensi:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py server.py
```

Server menampilkan alamat lokal dan QR code di terminal. Buka alamat itu dari browser ponsel. Jika Windows Firewall meminta izin, izinkan akses pada jaringan privat yang tepercaya. Hentikan server dengan `Ctrl+C`.

## Membuat aplikasi Windows

Jalankan `build_exe.bat` dari folder proyek. Script memasang PyInstaller dan dependensi proyek, lalu membuat `dist\StikGame.exe`. ViGEmBus tetap perlu dipasang pada PC yang menjalankan EXE.

## File untuk GitHub

Push file source dan konfigurasi berikut:

- `server.py` dan `templates/index.html`: kode aplikasi
- `requirements.txt`: daftar dependensi Python
- `build_exe.bat` dan `StikGame.spec`: prosedur dan konfigurasi build
- `README.md` dan `.gitignore`: dokumentasi dan aturan Git

Jangan push file lokal atau hasil build berikut:

- `.venv/`: virtual environment lokal
- `build/` dan `dist/`: file sementara dan hasil build EXE
- `__pycache__/` dan file `*.pyc`: cache Python
- Kredensial, token, file konfigurasi rahasia, atau data pribadi jika kelak ditambahkan

Aturan `.gitignore` mengecualikan virtual environment, cache Python, dan output build. `StikGame.spec` sengaja tidak diabaikan karena merupakan konfigurasi build yang berguna di repository.

## Catatan keamanan

Server mendengarkan koneksi pada jaringan lokal dan tidak memakai autentikasi. Gunakan hanya pada jaringan tepercaya, jangan teruskan port server ke internet, dan matikan server setelah selesai.