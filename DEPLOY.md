# Deploying TITAN Command Center

## Run locally
```bash
pip install -r requirements.txt
streamlit run titan_app.py
```

## Requirements
- **Python 3.10+**
- **BigQuery**: Place `service-key.json` in the project root (or set `KEY_FILE` in `settings.py` / `config_override.json` to its path). The app runs without BQ but Dashboard, Chat, and Evolution Lab need it.
- **Secrets**: `GEMINI_API_KEY` in `settings.py` or via `config_override.json` (Config tab). Restart after changing config.

## Streamlit Community Cloud
1. Push the repo and connect in [share.streamlit.io](https://share.streamlit.io).
2. Set **Secrets** (optional): `GEMINI_API_KEY`, and if needed the service account JSON as `GCP_SERVICE_KEY` (you would need to add code to read from `st.secrets` and write to `service-key.json` or use `GOOGLE_APPLICATION_CREDENTIALS`).
3. Main module: `titan_app.py`. The app uses `requirements.txt` and `.streamlit/config.toml`.

## Paths
- `service-key.json`, `TITAN_DNA.json`, `config_override.json`, `titan_users.json` are resolved from the **project root** (directory containing `titan_app.py`). Subprocess calls (Update DNA, Run Sentinel) use the project root as `cwd`.
