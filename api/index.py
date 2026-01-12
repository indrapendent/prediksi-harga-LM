from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- MODEL SEDERHANA (Trend Follower) ---
# Karena kita pakai harga IDR langsung, kita gunakan Slope positif
# Artinya kita memprediksi tren kenaikan kecil harian (misal 0.1% - 0.3%)
# berdasarkan pola historis emas jangka panjang.
MODEL_MULTIPLIER = 1.0015  # Prediksi naik 0.15% besok (Konservatif)

def get_antam_price():
    """
    Scraping langsung ke website resmi Antam (Logam Mulia)
    Mengambil harga emas batangan 1 gram.
    """
    try:
        # Target: Website resmi Antam
        url = "https://www.logammulia.com/id/harga-emas-hari-ini"
        
        # Header browser biasa
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Timeout 5 detik cukup
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Logika Scraping (Mencari elemen harga)
        # Struktur web Antam: Ada tabel, kita cari teks yang mengandung harga
        # Biasanya di dalam class '.price' atau tabel spesifik.
        
        # Cara paling aman: Cari semua elemen tabel, ambil harga baris pertama (0.5 gr) atau kedua (1 gr)
        # Di web LogamMulia, biasanya urutannya: 0.5 gr, 1 gr, 2 gr...
        
        # Kita cari elemen yang mengandung "1 gr" lalu ambil harga di sebelahnya
        rows = soup.find_all('tr')
        price_found = None
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                text_berat = cols[0].get_text(strip=True) # Kolom Berat
                text_harga = cols[1].get_text(strip=True) # Kolom Harga Dasar
                
                if "1 gr" in text_berat:
                    # Bersihkan format "Rp 1.250.000" -> jadi angka 1250000
                    clean_price = text_harga.replace('Rp', '').replace('.', '').replace(',', '').strip()
                    price_found = float(clean_price)
                    break
        
        return price_found

    except Exception as e:
        print(f"Gagal Scraping Antam: {e}")
        return None

@app.route('/api/predict')
def predict():
    try:
        # 1. Ambil Data Real-time dari Antam
        current_price = get_antam_price()
        
        status_msg = "Sumber: www.logammulia.com (Live)"
        
        # 2. FALLBACK (Jika web Antam down/maintenance)
        if current_price is None:
            current_price = 1350000.0  # Harga asumsi aman
            status_msg = "Mode Demo (Gagal koneksi ke Antam)"

        # 3. Hitung Prediksi
        # Rumus simpel: Harga Sekarang * Multiplier Tren
        predicted_price = current_price * MODEL_MULTIPLIER
        
        # 4. Hitung Persentase Perubahan
        change = predicted_price - current_price
        percent_change = (change / current_price) * 100
        
        # 5. Tentukan Sinyal
        signal = "TAHAN (Wait & See)"
        # Logika: Jika spread keuntungan > biaya admin (biasanya besar), baru beli.
        # Tapi untuk simulasi, kita pakai threshold kecil.
        if percent_change > 0.1: 
            signal = "BELI (Tren Positif)"
        elif percent_change < -0.1:
            signal = "JUAL (Tren Negatif)"

        return jsonify({
            "current_price": "{:,.0f}".format(current_price).replace(',', '.'),
            "predicted_next_price": "{:,.0f}".format(predicted_price).replace(',', '.'),
            "change_percent": round(percent_change, 2),
            "recommendation": signal,
            "status": status_msg
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()