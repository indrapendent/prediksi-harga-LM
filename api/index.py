from flask import Flask, jsonify
import yfinance as yf
# HAPUS import joblib, sklearn, pandas, dll yang tidak perlu
# Kita pertahankan yfinance (yang otomatis bawa pandas/numpy) tapi kita pakai sehemat mungkin.

app = Flask(__name__)

# --- MASUKKAN ANGKA DARI LAPTOP ANDA DI SINI ---
MODEL_SLOPE = 0.9992  # Contoh, ganti dengan hasil train_model.py Anda
MODEL_INTERCEPT = 1.254 # Contoh, ganti dengan hasil train_model.py Anda
# -----------------------------------------------

@app.route('/api/predict')
def predict():
    try:
        # 1. Ambil data real-time
        ticker = yf.Ticker('GC=F')
        data = ticker.history(period='5d')
        
        if data.empty:
            return jsonify({"error": "Gagal mengambil data"}), 500

        # Ambil harga penutupan terakhir
        current_price = float(data['Close'].iloc[-1])
        
        # 2. Prediksi Manual (Tanpa Scikit-Learn)
        # Rumus: y = mx + c
        predicted_price = (current_price * MODEL_SLOPE) + MODEL_INTERCEPT
        
        # 3. Logika Sinyal
        signal = "TAHAN"
        profit_percent = ((predicted_price - current_price) / current_price) * 100
        
        if profit_percent > 0.5: # Ambang batas kita turunkan sedikit karena regresi harian biasanya tipis
            signal = "BELI (Potensi Naik)"
        elif profit_percent < -0.5:
            signal = "JUAL (Potensi Turun)"

        return jsonify({
            "current_price": round(current_price, 2),
            "predicted_next_price": round(predicted_price, 2),
            "change_percent": round(profit_percent, 2),
            "recommendation": signal
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()