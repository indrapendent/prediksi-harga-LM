from flask import Flask, jsonify
import requests
import json

app = Flask(__name__)

# --- HARDCODED MODEL ---
MODEL_SLOPE = 1.0031972
MODEL_INTERCEPT = -5.01195503

def get_yahoo_price_manual(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        # TIMEOUT DIPERCEPAT JADI 3 DETIK (Agar tidak dibunuh Vercel)
        response = requests.get(url, headers=headers, timeout=3)
        data = response.json()
        
        result = data['chart']['result'][0]
        quote = result['indicators']['quote'][0]
        close_prices = quote['close']
        
        last_price = None
        for price in reversed(close_prices):
            if price is not None:
                last_price = float(price)
                break
                
        return last_price

    except Exception as e:
        print(f"Gagal ambil data {ticker}: {e}")
        return None

@app.route('/api/predict')
def predict():
    try:
        # 1. Coba ambil data (Maksimal 3 detik)
        price_gold_usd = get_yahoo_price_manual("GC=F")
        price_kurs_idr = get_yahoo_price_manual("IDR=X")
        
        status_msg = "Data Live (Real-time)"
        
        # 2. FALLBACK MODE (Jika Yahoo lemot/blokir, pakai data ini)
        if price_gold_usd is None or price_kurs_idr is None:
            price_gold_usd = 2665.00  # Harga Emas Estimasi
            price_kurs_idr = 15900.0  # Kurs Estimasi
            status_msg = "Mode Demo (Yahoo API Limit)"

        # 3. Hitung Prediksi
        predicted_usd = (price_gold_usd * MODEL_SLOPE) + MODEL_INTERCEPT
        
        # Konversi ke Rupiah/Gram
        gram_conversion = 31.1035
        price_idr_gram_now = (price_gold_usd / gram_conversion) * price_kurs_idr
        price_idr_gram_next = (predicted_usd / gram_conversion) * price_kurs_idr
        
        # Logika Sinyal
        change = price_idr_gram_next - price_idr_gram_now
        percent_change = (change / price_idr_gram_now) * 100
        
        signal = "TAHAN"
        if percent_change > 0.5: 
            signal = "BELI"
        elif percent_change < -0.5:
            signal = "JUAL"

        if "Demo" in status_msg:
            signal += " (Data Demo)"

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