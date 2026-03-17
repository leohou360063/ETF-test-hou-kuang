import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="台股永續高息投資助手", layout="centered")
st.title("📈 台股 ETF 蒙地卡羅模擬器")

# 側邊欄
st.sidebar.header("投資參數設定")
initial_investment = st.sidebar.number_input("初始投入金額", value=100000)
monthly_investment = st.sidebar.number_input("每月定期定額", value=10000)
years = st.sidebar.slider("投資年限 (年)", 1, 20, 10)

# 權重設定
st.sidebar.subheader("投資比例 (%)")
w_888 = st.sidebar.slider("00888 (產投高息)", 0, 100, 40)
w_878 = st.sidebar.slider("00878 (永續高息)", 0, 100, 30)
w_713 = st.sidebar.slider("00713 (高息低波)", 0, 100, 30)

if st.button("開始執行模擬"):
    if w_888 + w_878 + w_713 != 100:
        st.error("錯誤：投資比例總和必須等於 100%！")
    else:
        with st.spinner('正在從 Yahoo Finance 抓取最新數據...'):
            tickers = ['00888.TW', '00878.TW', '00713.TW']
            weights = np.array([w_888, w_878, w_713]) / 100
            
            # 使用 auto_adjust 確保數據正確
            data = yf.download(tickers, period="max", auto_adjust=True)['Close']
            
            if data.isnull().values.any():
                data = data.fillna(method='ffill')
            
            returns = data.pct_change().dropna()
            
            # 確保有抓到數據
            if returns.empty:
                st.error("抓不到股市數據，請稍後再試。")
            else:
                portfolio_returns = returns.dot(weights)
                mu = portfolio_returns.mean()
                sigma = portfolio_returns.std()
                
                months = years * 12
                all_paths = []
                
                # 執行 1000 次模擬
                for _ in range(1000):
                    # 確保 mu 和 sigma 不是空值
                    monthly_ret = np.random.normal(mu * 21, sigma * np.sqrt(21), months)
                    path = initial_investment * np.cumprod(1 + monthly_ret)
                    # 考慮每月投入 (簡易版)
                    for i in range(len(path)):
                        path[i] += monthly_investment * ((1 + mu * 21)**i)
                    all_paths.append(path)
                
                all_paths = np.array(all_paths)
                final_values = all_paths[:, -1]
                total_invested = initial_investment + (monthly_investment * months)
                
                # 顯示結果
                st.divider()
                c1, c2, c3 = st.columns(3)
                c1.metric("總投入本金", f"${total_invested:,.0f}")
                c2.metric("預期平均價值", f"${final_values.mean():,.0f}")
                c3.metric("勝率", f"{np.mean(final_values > total_invested):.1%}")
                
                # 圖表
                st.subheader("未來資產走勢預測")
                fig, ax = plt.subplots()
                ax.plot(np.percentile(all_paths, 50, axis=0), color='blue', label='預期中位數')
                ax.plot(np.percentile(all_paths, 5, axis=0), color='red', linestyle='--', label='保守情況')
                ax.fill_between(range(months), np.percentile(all_paths, 5, axis=0), np.percentile(all_paths, 95, axis=0), alpha=0.2)
                ax.legend()
                st.pyplot(fig)
