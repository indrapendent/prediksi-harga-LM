from flask import Flask, jsonify
import yfinance as yf
import joblib
import pandas as pd
import os
import numpy as np

app = Flask(__name__)

# Load model sekali saat serverless function 'warm up'
model_path = os.path.join(os.path.dirname(__file__), '../model/gold_model.pkl')
model = joblib.load(model_path)

@app.route('/api/predict')
def predict():
    try:
        # 1. Ambil harga emas LIVE terbaru
        ticker = yf.Ticker('GC=F')
        # Ambil data 5 hari terakhir untuk memastikan kita dapat data kemarin/hari ini
        data = ticker.history(period='5d') 
        
        if data.empty:
            return jsonify({"error": "Gagal mengambil data dari Yahoo Finance"}), 500

        current_price = data['Close'].iloc[-1]
        
        # 2. Prediksi Harga Besok
        # Input ke model adalah harga hari ini (Current Price)
        prediction_input = pd.DataFrame([[current_price]], columns=['Prev_Close'])
        predicted_price = model.predict(prediction_input)[0]
        
        # 3. Logika Sinyal (Algorithm Trading Sederhana)
        signal = "TAHAN"
        profit_percent = ((predicted_price - current_price) / current_price) * 100
        
        if profit_percent > 1.0: # Jika prediksi naik > 1%
            signal = "BELI (Potensi Naik)"
        elif profit_percent < -1.0: # Jika prediksi turun > 1%
            signal = "JUAL (Potensi Turun)"

        return jsonify({
            "current_price": round(current_price, 2),
            "predicted_next_price": round(predicted_price, 2),
            "change_percent": round(profit_percent, 2),
            "recommendation": signal
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Handler untuk Vercel
if __name__ == '__main__':
    app.run()