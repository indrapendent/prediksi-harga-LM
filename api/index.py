from flask import Flask, jsonify
import yfinance as yf
import requests
import appdirs as ad

# --- 1. FIX CACHE READ-ONLY ---
ad.user_cache_dir = lambda *args: "/tmp"

app = Flask(__name__)

# --- 2. MODEL WEIGHTS ---
MODEL_SLOPE = 1.0031972
MODEL_INTERCEPT = -5.01195503

def get_live_data():
    """
    Mencoba mengambil data dengan penyamaran browser.
    """
    try:
        # Buat sesi palsu agar dikira Browser Chrome (Bukan Bot Vercel)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        # Gunakan sesi tersebut di yfinance
        gold = yf.Ticker("GC=F", session=session)
        kurs = yf.Ticker("IDR=X", session=session)

        # Ambil history (gunakan '1mo' agar lebih aman datanya ada)
        gold_hist = gold.history(period="5d")
        kurs_hist = kurs.history(period="5d")

        if gold_hist.empty or kurs_hist.empty:
            raise Exception("Data Yahoo Finance kosong")

        return float(gold_hist['Close'].iloc[-1]), float(kurs_hist['Close'].iloc[-1])
    
    except Exception as e:
        print(f"GAGAL AMBIL LIVE DATA: {e}")
        return None, None

@app.route('/api/predict')
def predict():
    try:
        # Coba ambil data live
        price_gold_usd, price_kurs_idr = get_live_data()
        
        is_demo_mode = False
        
        # --- 3. FALLBACK MECHANISM (DATA CADANGAN) ---
        # Jika Yahoo memblokir Vercel, kita pakai data statis terakhir
        # agar aplikasi tetap jalan (tidak crash) saat presentasi
        if price_gold_usd is None or price_kurs_idr is None:
            is_demo_mode = True
            price_gold_usd = 2050.00  # Asumsi harga emas dunia $2050
            price_kurs_idr = 15500.0  # Asumsi kurs Rp 15.500

        # --- PERHITUNGAN ---
        predicted_usd = (price_gold_usd * MODEL_SLOPE) + MODEL_INTERCEPT
        
        gram_conversion = 31.1035
        price_idr_gram_now = (price_gold_usd / gram_conversion) * price_kurs_idr
        price_idr_gram_next = (predicted_usd / gram_conversion) * price_kurs_idr
        
        # Logika Sinyal
        change = price_idr_gram_next - price_idr_gram_now
        percent_change = (change / price_idr_gram_now) * 100
        
        signal = "TAHAN (Netral)"
        if percent_change > 0.5: 
            signal = "BELI (Potensi Naik)"
        elif percent_change < -0.5:
            signal = "JUAL (Potensi Turun)"

        # Tambahkan label jika ini data demo
        status_msg = "Data Live (Real-time)"
        if is_demo_mode:
            status_msg = "Mode Demo (Koneksi Yahoo Dibatasi)"
            signal += " [DEMO]"

        return jsonify({
            "current_price": "{:,.0f}".format(price_idr_gram_now).replace(',', '.'),
            "predicted_next_price": "{:,.0f}".format(price_idr_gram_next).replace(',', '.'),
            "change_percent": round(percent_change, 2),
            "recommendation": signal,
            "status": status_msg
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()