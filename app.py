import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="台股投資助手", layout="centered")
st.title("📈 台股 ETF 蒙地卡羅模擬器")

# 側邊欄
st.sidebar.header("投資參數設定")
init_inv = st.sidebar.number_input("初始投入金額", value=100000)
mon_inv = st.sidebar.number_input("每月定期定額", value=10000)
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
        with st.spinner('正在獲取數據...（這可能需要幾秒鐘）'):
            # 使用更穩定的抓取方式
            tickers = ['00888.TW', '00878.TW', '00713.TW']
            weights = np.array([w_888, w_878, w_713]) / 100
            
            try:
                # 抓取最近兩年的數據即可，增加成功率
                df = yf.download(tickers, period="2y", interval="1d", auto_adjust=True)['Close']
                
                if df.empty or df.isnull().all().all():
                    # 嘗試備用方案
                    st.warning("第一波數據抓取異常，嘗試備用連線...")
                    df = yf.download(tickers, period="1y")['Adj Close']

                df = df.ffill().dropna()
                rets = df.pct_change().dropna()

                if not rets.empty:
                    # 計算組合回報
                    port_rets = rets.dot(weights)
                    mu = port_rets.mean()
                    sigma = port_rets.std()
                    
                    months = years * 12
                    all_paths = []
                    
                    # 執行 1000 次模擬
                    for _ in range(1000):
                        # 月報酬率模擬
                        m_rets = np.random.normal(mu * 21, sigma * np.sqrt(21), months)
                        # 計算複利
                        path = [init_inv]
                        for r in m_rets:
                            next_val = (path[-1] + mon_inv) * (1 + r)
                            path.append(next_val)
                        all_paths.append(path)
                    
                    all_paths = np.array(all_paths)
                    final_v = all_paths[:, -1]
                    total_in = init_inv + (mon_inv * months)
                    
                    st.divider()
                    c1, c2, c3 = st.columns(3)
                    c1.metric("總投入本金", f"${total_in:,.0f}")
                    c2.metric("預期平均價值", f"${final_v.mean():,.0f}")
                    c3.metric("預估勝率", f"{np.mean(final_v > total_in):.1%}")
                    
                    # 畫圖
                    st.subheader("資產成長預測走勢")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    months_range = range(months + 1)
                    ax.plot(months_range, np.percentile(all_paths, 50, axis=0), label="中位數路徑", color='blue')
                    ax.fill_between(months_range, np.percentile(all_paths, 5, axis=0), np.percentile(all_paths, 95, axis=0), alpha=0.2, color='blue')
                    ax.axhline(total_in, color='red', linestyle='--', label="本金水位")
                    ax.set_xlabel("月份")
                    ax.set_ylabel("資產價值")
                    ax.legend()
                    st.pyplot(fig)
                else:
                    st.error("目前的市場數據不完整，請檢查網路或稍後再點擊一次。")
                    
            except Exception as e:
                st.error(f"連線至 Yahoo Finance 失敗，請再試一次。")
