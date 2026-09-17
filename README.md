# Weather Explorer

A Streamlit dashboard that compares current weather in multiple cities and shows a five-day forecast using OpenWeatherMap.

## Run locally

From the project folder:

```bash
python -m pip install -r requirements.txt
export OPENWEATHER_API_KEY="your_new_api_key"
streamlit run Assignment_2/app.py
```

Alternatively, create `Assignment_2/.streamlit/secrets.toml`:

```toml
OPENWEATHER_API_KEY = "your_new_api_key"
```

That secrets file is ignored by Git.

## Publish with Streamlit Community Cloud

1. Push this project to GitHub.
2. Select `Assignment_2/app.py` as the main file.
3. Add this secret in the app settings:

```toml
OPENWEATHER_API_KEY = "your_new_api_key"
```

Never commit an API key to GitHub. The key previously used in this project should be rotated before publishing.
# assignment_2
