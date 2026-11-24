"""Bike Sharing Demand Explorer - Streamlit app.

Dataset: UCI Bike Sharing Dataset (hour.csv), Washington D.C. Capital Bikeshare,
2011-2012, one row per hour.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bike Sharing Explorer", page_icon="🚲", layout="wide")

DATA_PATH = Path(__file__).parent / "data" / "hour.csv"
SEASONS = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
WEATHER = {1: "Clear", 2: "Mist / cloudy", 3: "Light rain / snow", 4: "Heavy rain / snow"}
WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BLUE, ORANGE = "#2563eb", "#f97316"


# ---------------------------------------------------------------- data
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["dteday"], format="mixed")
    df["year"] = df["yr"].map({0: 2011, 1: 2012})
    df["season_name"] = df["season"].map(SEASONS)
    df["weather"] = df["weathersit"].map(WEATHER)
    df["weekday_name"] = df["weekday"].map(dict(enumerate(WEEKDAYS)))
    df["day_type"] = df["workingday"].map({1: "Working day", 0: "Weekend / holiday"})
    df["month_name"] = df["mnth"].map(dict(enumerate(MONTHS, start=1)))
    # the dataset stores normalised values; convert back to real units
    df["temp_c"] = df["temp"] * 41
    df["feels_c"] = df["atemp"] * 50
    df["humidity"] = df["hum"] * 100
    df["wind_kmh"] = df["windspeed"] * 67
    return df


df = load_data()
has_split = {"casual", "registered"}.issubset(df.columns)

# ---------------------------------------------------------------- sidebar filters
st.sidebar.header("🔎 Filters")
dmin, dmax = df["date"].min().date(), df["date"].max().date()
date_range = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
seasons = st.sidebar.multiselect("Season", list(SEASONS.values()), default=list(SEASONS.values()))
weathers = st.sidebar.multiselect("Weather", list(WEATHER.values()), default=list(WEATHER.values()))
day_types = st.sidebar.multiselect(
    "Day type", ["Working day", "Weekend / holiday"], default=["Working day", "Weekend / holiday"]
)
hours = st.sidebar.slider("Hour of day", 0, 23, (0, 23))
tmin, tmax = float(df["temp_c"].min()), float(df["temp_c"].max())
temps = st.sidebar.slider("Temperature (°C)", int(tmin), int(tmax) + 1, (int(tmin), int(tmax) + 1))

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
else:
    start, end = dmin, dmax

f = df[
    (df["date"].dt.date >= start)
    & (df["date"].dt.date <= end)
    & df["season_name"].isin(seasons)
    & df["weather"].isin(weathers)
    & df["day_type"].isin(day_types)
    & df["hr"].between(*hours)
    & df["temp_c"].between(*temps)
]

# ---------------------------------------------------------------- header + KPIs
st.title("🚲 Bike Sharing Demand Explorer")
st.caption(
    "Hourly Capital Bikeshare rentals in Washington D.C., 2011-2012 "
    "([UCI Bike Sharing Dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset)). "
    "Use the sidebar filters; every chart and number updates."
)

if f.empty:
    st.warning("No data matches these filters. Widen them in the sidebar.")
    st.stop()

peak_hour = f.groupby("hr")["cnt"].mean().idxmax()
y = f.groupby("year")["cnt"].sum()
growth = (y.get(2012, 0) / y.get(2011, 0) - 1) * 100 if {2011, 2012} <= set(y.index) and y.get(2011, 0) > 0 else None

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total rentals", f"{f['cnt'].sum():,}")
k2.metric("Avg rentals / hour", f"{f['cnt'].mean():.0f}")
k3.metric("Peak hour (avg)", f"{peak_hour}:00")
k4.metric("Busiest day (total)", f"{f.groupby('date')['cnt'].sum().max():,}")
k5.metric("2012 vs 2011", f"{growth:+.0f}%" if growth is not None else "n/a",
          help="Total rentals growth; needs both years inside the filter.")
st.caption(f"{len(f):,} hourly records selected out of {len(df):,}.")

st.divider()

# ---------------------------------------------------------------- Q1 trend
st.subheader("1. How has demand grown over time?")
daily = f.groupby("date", as_index=False)["cnt"].sum()
daily["7-day average"] = daily["cnt"].rolling(7, min_periods=1).mean()
fig = px.line(daily, x="date", y=["cnt", "7-day average"],
              labels={"value": "Rentals per day", "date": "", "variable": ""},
              color_discrete_sequence=["#94a3b8", BLUE])
fig.update_layout(legend=dict(orientation="h", y=1.1), margin=dict(t=30))
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- Q2 hourly
c1, c2 = st.columns(2)
with c1:
    st.subheader("2. When during the day do people ride?")
    hourly = f.groupby(["hr", "day_type"], as_index=False)["cnt"].mean()
    fig = px.line(hourly, x="hr", y="cnt", color="day_type", markers=True,
                  labels={"hr": "Hour of day", "cnt": "Avg rentals per hour", "day_type": ""},
                  color_discrete_map={"Working day": BLUE, "Weekend / holiday": ORANGE})
    fig.update_layout(legend=dict(orientation="h", y=1.12), margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")
with c2:
    st.subheader("3. Which weekday + hour is busiest?")
    heat = f.pivot_table(index="weekday_name", columns="hr", values="cnt", aggfunc="mean").reindex(WEEKDAYS)
    fig = px.imshow(heat, aspect="auto", color_continuous_scale="Blues",
                    labels={"x": "Hour of day", "y": "", "color": "Avg rentals"})
    fig.update_layout(margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- Q4 season / month
c3, c4 = st.columns(2)
with c3:
    st.subheader("4. How seasonal is demand?")
    monthly = f.groupby(["year", "mnth", "month_name"], as_index=False)["cnt"].mean().sort_values("mnth")
    monthly["year"] = monthly["year"].astype(str)
    fig = px.bar(monthly, x="month_name", y="cnt", color="year", barmode="group",
                 labels={"month_name": "", "cnt": "Avg rentals per hour", "year": "Year"},
                 category_orders={"month_name": MONTHS},
                 color_discrete_map={"2011": "#93c5fd", "2012": BLUE})
    fig.update_layout(legend=dict(orientation="h", y=1.12), margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")
with c4:
    st.subheader("5. How does weather change ridership?")
    w = f.groupby("weather", as_index=False).agg(avg=("cnt", "mean"), hours=("cnt", "size"))
    w["weather"] = pd.Categorical(w["weather"], list(WEATHER.values()), ordered=True)
    w = w.sort_values("weather")
    fig = px.bar(w, x="weather", y="avg", text=w["avg"].round(0),
                 labels={"weather": "", "avg": "Avg rentals per hour"},
                 color_discrete_sequence=[BLUE])
    fig.update_traces(textposition="outside")
    fig.update_layout(margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")
    st.caption("Heavy rain/snow has very few hours in the data (3), so treat that bar with caution.")

# ---------------------------------------------------------------- Q6 temperature / humidity
c5, c6 = st.columns(2)
with c5:
    st.subheader("6. What temperature do riders prefer?")
    t = f.assign(band=pd.cut(f["temp_c"], [-5, 5, 10, 15, 20, 25, 30, 45],
                             labels=["<5", "5–10", "10–15", "15–20", "20–25", "25–30", "30+"]))
    t = t.groupby("band", observed=True, as_index=False)["cnt"].mean()
    fig = px.bar(t, x="band", y="cnt", labels={"band": "Temperature (°C)", "cnt": "Avg rentals per hour"},
                 color_discrete_sequence=[ORANGE])
    fig.update_layout(margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")
with c6:
    st.subheader("7. Do humidity and wind matter?")
    metric = st.radio("Variable", ["Humidity (%)", "Wind speed (km/h)"], horizontal=True)
    col = "humidity" if metric.startswith("Humidity") else "wind_kmh"
    sample = f.sample(min(len(f), 4000), random_state=0)
    fig = px.scatter(sample, x=col, y="cnt", opacity=0.3, trendline="lowess",
                     labels={col: metric, "cnt": "Rentals per hour"},
                     color_discrete_sequence=[BLUE])
    fig.update_layout(margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")
    st.caption("Random sample of up to 4,000 hours for readability; the trend line is a smoothed average.")

if has_split:
    st.subheader("8. Casual vs registered riders by hour")
    s = f.groupby("hr")[["casual", "registered"]].mean().reset_index().melt("hr")
    fig = px.area(s, x="hr", y="value", color="variable",
                  labels={"hr": "Hour of day", "value": "Avg rentals per hour", "variable": ""})
    st.plotly_chart(fig, width="stretch")

st.divider()

# ---------------------------------------------------------------- conclusion
st.header("📌 Conclusion")
st.markdown(
    """
These findings come from the **full, unfiltered dataset**.

- **Two different rhythms.** On working days, demand has two sharp peaks: about **8:00** (≈480 rentals/hour)
  and **17:00-18:00** (≈500+), which looks like commuting. On weekends and holidays there is one
  broad peak from late morning to mid-afternoon (≈350-370 around noon-15:00).
- **Warm weather drives rides.** Average hourly rentals rise from about **70** below 10 °C to about **330** above 30 °C.
  Summer and fall are the busiest seasons (≈236 and ≈199 per hour); winter is the quietest (≈111).
- **Bad weather hurts.** Clear hours average ≈205 rentals, light rain or snow ≈112. High humidity also
  goes with fewer rides (≈286 per hour when humidity is under 40%, ≈107 when above 80%).
  Wind speed has almost no relationship with demand.
- **The system grew fast.** Total rentals rose about **65%** from 2011 (≈1.24 M) to 2012 (≈2.05 M),
  and the seasonal pattern repeated in both years.
- **Day of week matters little on its own.** Average demand per weekday is similar (≈177-196). What changes
  is *when* people ride, not how much.

**Practical takeaways:** keep bikes stocked near work and transit areas for the morning and evening commute peaks, move
maintenance to the low-demand winter and overnight hours, and expect weather forecasts to be a strong predictor of daily demand.

*Caveat: these are associations in observational data, not proof of cause. Temperature, season and humidity are
related to each other, so their effects overlap.*
"""
)
