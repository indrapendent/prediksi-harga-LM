from flask import Flask, jsonify
import yfinance as yf

# --- FIX UNTUK VERCEL (PENTING) ---
# Memindahkan cache yfinance ke folder /tmp agar tidak error 'Read-only file system'
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"
# ----------------------------------

app = Flask(__name__)

# --- MODEL HARDCODED (USD) ---
# Tetap gunakan model USD karena lebih akurat untuk tren global
MODEL_SLOPE = 1.0031972
MODEL_INTERCEPT = -5.01195503
# -----------------------------

@app.route('/api/predict')
def predict():
    try:
        # 1. Ambil Data Emas Dunia (USD) & Kurs Rupiah
        # GC=F: Emas Futures (USD/Troy Oz)
        # IDR=X: Kurs USD ke IDR
        tickers = yf.Tickers('GC=F IDR=X')
        
        # Ambil data hari ini (period='1d' cukup untuk harga terakhir)
        gold_data = tickers.tickers['GC=F'].history(period='5d')
        kurs_data = tickers.tickers['IDR=X'].history(period='5d')
        
        if gold_data.empty or kurs_data.empty:
            return jsonify({"error": "Gagal mengambil data market"}), 500

        # Ambil harga penutupan terakhir (USD)
        current_price_usd_oz = float(gold_data['Close'].iloc[-1])
        current_kurs_idr = float(kurs_data['Close'].iloc[-1])

        # 2. Lakukan Prediksi (Dalam USD)
        # Kita prediksi dulu dalam USD karena model dilatih dengan data USD
        predicted_price_usd_oz = (current_price_usd_oz * MODEL_SLOPE) + MODEL_INTERCEPT
        
        # 3. Konversi ke Rupiah per Gram (Harga Logam Mulia)
        # Rumus: (Harga USD per Oz / 31.1035) * Kurs Rupiah
        gram_conversion = 31.1035
        
        price_idr_gram_now = (current_price_usd_oz / gram_conversion) * current_kurs_idr
        price_idr_gram_next = (predicted_price_usd_oz / gram_conversion) * current_kurs_idr
        
        # 4. Logika Sinyal
        change = price_idr_gram_next - price_idr_gram_now
        percent_change = (change / price_idr_gram_now) * 100
        
        signal = "TAHAN (Netral)"
        if percent_change > 0.5: 
            signal = "BELI (Potensi Naik)"
        elif percent_change < -0.5:
            signal = "JUAL (Potensi Turun)"

        return jsonify({
            # Format angka agar rapi (tanpa desimal untuk Rupiah)
            "current_price": "{:,.0f}".format(price_idr_gram_now).replace(',', '.'),
            "predicted_next_price": "{:,.0f}".format(price_idr_gram_next).replace(',', '.'),
            "change_percent": round(percent_change, 2),
            "recommendation": signal
        })

    except Exception as e:
        # Print error di log Vercel untuk debugging jika gagal lagi
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()