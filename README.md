# NOC Network Dashboard (Real-Time)

Halo! Ini adalah project saya untuk bikin dashboard monitoring jaringan sederhana tapi fungsional. 

Awalnya kepikiran bikin ini karena pas lagi nge-lab atau nge-troubleshoot jaringan, kadang ribet kalau harus buka banyak tab CMD cuma buat nge-ping ke beberapa IP dan ngecek traffic lokal. Jadi, saya bikin command center mini pakai Python biar semuanya langsung kelihatan visual di satu layar.

Selain buat fungsi monitoring, saya juga lumayan merhatiin sisi security di source code-nya. Eksekusi modul `subprocess` buat nge-ping udah saya amankan dari potensi command injection (kode ini udah lolos cek linter Bandit).

# Fitur yang Kepake Banget
* Live Ping Monitor: Mantau latency (ms) ke beberapa host sekaligus, grafiknya jalan terus secara real-time.
* Bandwidth Meter: Nampilin speed upload & download (dalam satuan Mbps) langsung dari interface jaringan PC yang lagi aktif.
* Sidebar Control: Kalau mau ganti IP target atau ngatur delay refresh-nya, tinggal ketik di panel sebelah kiri, nggak usah buka-buka kode lagi.
* Dark Mode UI: Tampilannya sengaja dibikin gelap ala-ala layar NOC beneran biar nyaman di mata.

# Dibangun Pakai Apa Aja?
* Python 3.12
* Streamlit (buat ngerender UI web-nya)
* Plotly & Pandas (buat bikin grafik datanya)
* Psutil (buat narik data utilisasi jaringan langsung dari OS)

# Cara Jalanin di Laptop/PC Kamu

Syarat utama: Pastiin udah install Python di Windows kamu.

1. Clone repo ini:
   ```bash
   [git clone [https://github.com/username-kamu/noc-network-dashboard.git](https://github.com/username-kamu/noc-network-dashboard.git)](https://github.com/muchamad-gilang-dwi-saputra/noc-network-dashboard)
   cd noc-network-dashboard

2. Install library yang dibutuhin:
```bash
py -3.12 -m pip install streamlit plotly pandas psutil

```
3. Jalanin aplikasinya:
```
py -3.12 -m streamlit run app.py

```
4. Selesai! Nanti otomatis kebuka di browser
