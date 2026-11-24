# 🚲 Bike Sharing Demand Explorer

An interactive Streamlit app that analyses the UCI **Bike Sharing Dataset** (`hour.csv`): 17,379 hourly
records of Capital Bikeshare rentals in Washington D.C. during 2011–2012.

**Live app:** https://abushanab1.streamlit.app/  
**Data source:** https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset

## What the app shows

- **KPIs:** total rentals, average rentals per hour, peak hour, busiest day, and 2012-vs-2011 growth.
- **Charts answering seven questions:** growth over time, daily rhythm (working day vs weekend), weekday × hour
  heatmap, seasonality by month and year, effect of weather, effect of temperature, and effect of humidity/wind.
  If `casual` and `registered` columns exist, a casual-vs-registered chart is added.
- **Filters (sidebar):** date range, season, weather, day type, hour of day, and temperature. All KPIs and charts update.
- **Conclusion:** the main findings in plain words, with practical takeaways.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files

| File | Purpose |
| --- | --- |
| `app.py` | The Streamlit app |
| `data/hour.csv` | The hourly dataset |
| `requirements.txt` | Python dependencies |
