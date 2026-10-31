# 🧭 IssueScout

**An AI guide for your first open-source contribution** — built for Hacktoberfest 2026.

Paste any GitHub repository and IssueScout helps you go from "where do I even start?" to a ready-to-send pull request.

## Features

- **Find an issue** – Lists beginner-friendly open issues (`good first issue`, `hacktoberfest`, `help wanted`, `documentation`, `bug`) and generates a step-by-step plan for the one you pick, including which files to look at.
- **Explain a screenshot** – Upload a screenshot of an error or UI problem and get a plain-English explanation of what is going on and how to approach it.
- **Write a PR** – Generates a clear pull request title and description for your change.
- **Light / dark theme** with one-click switch.
- **Automatic model fallback** – if the primary model is unavailable or rate-limited, IssueScout tries the next one.

## Tech stack

- [Streamlit](https://streamlit.io) – web UI
- [Google Gen AI SDK](https://pypi.org/project/google-genai/) – Gemma / Gemini models
- [GitHub REST API](https://docs.github.com/en/rest) – issues and repo file tree
- Pillow – screenshot handling

## Run locally

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your keys (optional – you can also paste them in the app sidebar)
export GEMINI_API_KEY="your-key"        # macOS / Linux
setx GEMINI_API_KEY "your-key"          # Windows

# 4. Start the app
streamlit run app.py
```

Then open http://localhost:8501.

## API keys

| Key | Required | Where to get it |
| --- | --- | --- |
| `GEMINI_API_KEY` | Yes | Free at [Google AI Studio](https://aistudio.google.com) |
| `GITHUB_TOKEN` | No | [GitHub token settings](https://github.com/settings/tokens) – raises the rate limit from 60 to 5,000 requests/hour |

Keys can be entered in the app sidebar, set as environment variables, or stored in `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key"
GITHUB_TOKEN = "your-token"
```

> ⚠️ Never commit `secrets.toml` or any real key to GitHub.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMMA_MODEL` | `gemma-4-31b-it` | Primary model ID (check the exact name in Google AI Studio) |

Fallback models: `gemma-3-27b-it`, `gemini-2.5-flash`.

## Deploy on Streamlit Community Cloud

1. Push `app.py` and `requirements.txt` to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **Create app**.
3. Select your repo, branch `main`, and main file `app.py`.
4. Under **Advanced settings → Secrets**, add your `GEMINI_API_KEY` (and optionally `GITHUB_TOKEN`).
5. Click **Deploy**.

## Project structure

```
├── app.py              # the whole Streamlit app
├── requirements.txt    # Python dependencies
└── README.md
```

## Contributing

Issues and pull requests are welcome. Happy Hacktoberfest! 🎃

## License

Add a license of your choice (for example MIT) in a `LICENSE` file.
