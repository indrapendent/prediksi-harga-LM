import yfinance as yf
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# 1. Ambil data emas (GC=F adalah Gold Futures)
print("Mengambil data...")
df = yf.download('GC=F', start='2020-01-01')
df = df[['Close']]

# 2. Feature Engineering (Buat fitur 'Hari Kemarin' untuk prediksi 'Hari Ini')
df['Prev_Close'] = df['Close'].shift(1)
df = df.dropna()

# 3. Siapkan Data
X = df[['Prev_Close']]
y = df['Close']

# 4. Train Model
model = LinearRegression()
model.fit(X, y)

# 5. Simpan Model
joblib.dump(model, 'model/gold_model.pkl')
print("Model berhasil disimpan ke folder model/gold_model.pkl")