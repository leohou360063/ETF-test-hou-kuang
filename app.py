import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="台股投資助手", layout="centered")
st.title("📈 台股 ETF 蒙地卡羅模擬器")

# 側邊欄設定
st.sidebar.header("投資參數設定")
init_inv = st.sidebar.number_input("初始投入金額", value=100000)
mon_inv = st.sidebar.number_input("每月定期定額", value=10000)
years = st.sidebar.slider("投資年限 (年)", 1, 20, 10)

# 權重設定
st.sidebar.subheader("投資比例 (%)")
w_888 = st.sidebar.slider("00888", 0, 100, 40)
w_878 = st.sidebar.slider("00878", 0, 100, 30)
w_713 = st.sidebar.slider("00713", 0, 100, 30)

if st.button("開始執行模擬"):
    if w_888 + w_878 + w_713 != 100:
        st.error("錯誤：投資比例總和必須等於 100%！")
    else:
        with st.spinner('正在獲取最新股市數據...'):
            # 使用更穩定的抓取方式與更短的時間範圍
            tickers = ['00888.TW', '00878.TW', '00713.TW']
            weights = np.array([w_888, w_878, w_713]) / 100
            
            try:
                # 抓取最近一年的數據最穩定
                df = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)
                if not df.empty:
                    df = df['Close'].ffill().dropna()
                    rets = df.pct_change().dropna()
                    
                    if not rets.empty:
                        # 核心計算
                        port_rets = rets.dot(weights)
                        mu, sigma = port_rets.mean(), port_rets.std()
                        months = years * 12
                        all_paths = []
                        
                        for _ in range(500): # 縮減模擬次數加快手機跑速
                            m_rets = np.random.normal(mu * 21, sigma * np.sqrt(21), months)
                            path = [init_inv]
                            for r in m_rets:
                                path.append((path[-1] + mon_inv) * (1 + r))
                            all_paths.append(path)
                        
                        all_paths = np.array(all_paths)
                        final_v = all_paths[:, -1]
                        total_in = init_inv + (mon_inv * months)
                        
                        # 顯示數據
                        st.divider()
                        c1, c2, c3 = st.columns(3)
                        c1.metric("總投入本金", f"${total_in:,.0f}")
                        c2.metric("預期價值", f"${final_v.mean():,.0f}")
                        c3.metric("預估勝率", f"{np.mean(final_v > total_in):.1%}")
                        
                        # 繪圖
                        st.subheader("未來資產成長預測")
                        fig, ax = plt.subplots()
                        ax.plot(np.percentile(all_paths, 50, axis=0), color='blue', label='中位數預估')
                        ax.fill_between(range(months+1), np.percentile(all_paths, 5, axis=0), np.percentile(all_paths, 95, axis=0), alpha=0.2, color='blue')
                        ax.axhline(total_in, color='red', linestyle='--', label='投入本金')
                        ax.legend()
                        st.pyplot(fig)
                    else:
                        st.error("目前抓取的數據不足以計算，請 10 秒後再試。")
            except:
                st.error("與 Yahoo Finance 連線不穩，請再次點擊按鈕。")
