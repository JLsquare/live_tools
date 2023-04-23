import time
import pandas as pd
from collections import deque
from bitget import Bitget
from bitget.error import BitgetApiError

api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"

class EMA:
    def __init__(self, period):
        self.period = period
        self.multiplier = 2 / (period + 1)
        self.values = deque(maxlen=period)

    def add(self, value):
        self.values.append(value)
        if len(self.values) < self.period:
            return None

        if len(self.values) == self.period:
            return sum(self.values) / len(self.values)

        ema_prev = self.add(value)
        return ema_prev + (value - ema_prev) * self.multiplier

def get_historical_data(bitget, symbol, interval="60", limit=100):
    try:
        historical_data = bitget.spot().candles(symbol=symbol, granularity=interval, limit=limit)
        data = []

        for candle in historical_data:
            data.append([candle[0], float(candle[1]), float(candle[2]), float(candle[3]), float(candle[4]), float(candle[5])])

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df

    except BitgetApiError as e:
        print(f"Erreur lors de la récupération des données historiques : {str(e)}")
        return None

bitget = Bitget(api_key=api_key, api_secret=api_secret)
symbol = "btcusdt"  # Remplacez "btcusdt" par le symbole souhaité
ema_short = EMA(12)
ema_long = EMA(26)

while True:
    try:
        historical_data = get_historical_data(bitget, symbol)
        if historical_data is None:
            time.sleep(60)
            continue

        close_prices = historical_data['close'].values

        ema_short_values = []
        ema_long_values = []

        for price in close_prices:
            ema_short_values.append(ema_short.add(price))
            ema_long_values.append(ema_long.add(price))

        if ema_short_values[-1] is not None and ema_long_values[-1] is not None:
            buy_signal = ema_short_values[-1] > ema_long_values[-1] and ema_short_values[-2] <= ema_long_values[-2]
            sell_signal = ema_short_values[-1] < ema_long_values[-1] and ema_short_values[-2] >= ema_long_values[-2]

            if buy_signal:
                print("Signal d'achat détecté")
                try:
                    order_params = {
                        "symbol": symbol,
                        "side": "buy",
                        "type": "limit",  # Utiliser 'market' pour les ordres au marché
                        "price": str(close_prices[-1]),  # Ignoré si type = 'market'
                        "size": "0.001",  # Quantité à acheter
                    }
                    response = bitget.spot().place_order(**order_params)
                    print(f"Ordre d'achat créé : {response}")
                except BitgetApiError as e:
                    print(f"Erreur lors de la création de l'ordre d'achat : {str(e)}")

            if sell_signal:
                print("Signal de vente détecté")
                try:
                    order_params = {
                        "symbol": symbol,
                        "side": "sell",
                        "type": "limit",  # Utiliser 'market' pour les ordres au marché
                        "price": str(close_prices[-1]),  # Ignoré si type = 'market'
                        "size": "0.001",  # Quantité à vendre
                    }
                    response = bitget.spot().place_order(**order_params)
                    print(f"Ordre de vente créé : {response}")
                except BitgetApiError as e:
                    print(f"Erreur lors de la création de l'ordre de vente : {str(e)}")


    except Exception as e:
        print(f"Erreur lors de l'exécution de la stratégie : {str(e)}")

    time.sleep(60)
