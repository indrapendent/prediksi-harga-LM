import yfinance as yf
import pandas as pd
from sklearn.linear_model import LinearRegression

# 1. Ambil data
print("Mengambil data...")
df = yf.download('GC=F', start='2020-01-01')
df = df[['Close']]

# 2. Feature Engineering
df['Prev_Close'] = df['Close'].shift(1)
df = df.dropna()

# 3. Train
X = df[['Prev_Close']]
y = df['Close']
model = LinearRegression()
model.fit(X, y)

# 4. OUTPUT RUMUS (PENTING)
print("\n=== SALIN ANGKA INI ===")
print(f"SLOPE (m)     : {model.coef_[0]}")
print(f"INTERCEPT (c) : {model.intercept_}")
print("=======================\n")