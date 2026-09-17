import time


import pandas as pd
import plotly.express as px
import streamlit as st
st.set_page_config(page_title="Watchlist Explorer", layout="wide")
st.title("Watchlist Explorer")
st.caption("Six tech stocks, weekly, 2018-2019. Indexed to 1.00 on 2018-01-01.")
@st.cache_data
def load_data():
    time.sleep(2) # stand-in for a slow API / database call — delete in a real app
    wide = px.data.stocks()
    wide["date"] = pd.to_datetime(wide["date"])
    long = wide.melt(id_vars="date", var_name="ticker", value_name="price")
    return long.sort_values(["ticker", "date"])
df = load_data()
st.dataframe(df.head(10))

with st.sidebar: 
    st.header("Controls")
    tickers = st.multiselect(
        "Tickers",
        options=sorted(df["ticker"].unique()),
        default=["AAPL", "MSFT", "AMZN"],)
    start, end = st.slider(
        "Date range",
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),
        value=(df["date"].min().date(), df["date"].max().date()),)

rebase = st.checkbox("Rebase to 100 at window start", value=True)
view = df[df["ticker"].isin(tickers) & df["date"].dt.date.between(start, end)].copy()
if view.empty:
    st.info("Pick at least one ticker in the sidebar.")
    st.stop()
if rebase:
    view["price"] = view.groupby("ticker")["price"].transform(lambda s: s / s.iloc[0] *100)
st.dataframe(view.head())