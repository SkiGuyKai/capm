import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import numpy as np
import requests

class CAPM:

    def __init__(self, symbol):
        self.symbol = symbol
        self.stk, self.capm_df = self.__GET_DATA()
        self.beta, self.r_s = self.__CALC()


    def __GET_DATA(self):
        r = requests.get('https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?fields=record_date,security_desc,avg_interest_rate_amt&filter=security_desc:eq:Treasury Bills&sort=-record_date')
        raw = r.json()
        data = raw['data']

        rf_data = [round(float(i['avg_interest_rate_amt']) / 100, 4) for i in data]
        rf_df = pd.DataFrame(rf_data[:61])
        rf_df = rf_df.loc[::-1]

        stock = yf.Ticker(self.symbol)
        market = yf.Ticker('spy')

        mkt = market.history(period='5y', interval='1mo')
        stk = stock.history(period='5y', interval='1mo')
        mkt.dropna(inplace=True)
        stk.dropna(inplace=True)

        stk['rm'] = round(mkt['Close'].pct_change(), 4)
        stk['rs'] = round(stk['Close'].pct_change(), 4)
        stk['rf'] = rf_df.values
        stk = stk.iloc[:60, -3:]
        stk.dropna(inplace=True)

        capm_df = pd.DataFrame()
        capm_df['market excess'] = stk['rm'] - stk['rf']
        capm_df['stock excess'] = stk['rs'] - stk['rf']
        capm_df.dropna(inplace=True)

        return stk, capm_df


    def __CALC(self):
        self.x = self.capm_df['market excess']
        x_bar = self.x.mean()
        self.y = self.capm_df['stock excess']
        y_bar = self.y.mean()

        x_0 = self.x - x_bar
        y_0 = self.y - y_bar

        n = x_0 * y_0
        d = x_0 ** 2
        q = n.sum() / d.sum()
        r_s = (self.stk.iloc[-1, -1] + q * self.stk['rm'].mean()) * 12 ** 0.5
        
        self.x_bar = x_bar
        self.q = q

        return q, r_s



    def plot(self):
        x_v = np.linspace(-0.2, 0.2)
        y_v = x_v * self.q

        plt.grid(True)
        plt.axhline(0, color='black')
        plt.axvline(0, color='black')
        plt.xlim((self.x.min() - 0.05, self.x.max() + 0.05))
        plt.ylim((self.y.min() - 0.05, self.y.max() + 0.05))

        plt.scatter(self.x, self.y)
        lplot, = plt.plot(x_v, y_v, 'r')
        lbl = f'y = {self.stk.iloc[-1, -1]} + {round(self.q, 3)}({round(self.x_bar, 3)})'
        plt.legend([lplot], [lbl])
        plt.show()