# 🧭 IssueScout

**Your guide to making your first open-source contribution.** Built for Hacktoberfest 2026.

Paste a public GitHub repo link, and IssueScout helps you go from "where do I start?" to a finished pull request.

---

## What can it do?

| Feature | What you do | What you get |
| --- | --- | --- |
| **Find an issue** | Paste a repo link and pick a label (like `good first issue`) | A simple summary, difficulty, time estimate, files to look at, a step-by-step plan, and common mistakes to avoid |
| **Explain a screenshot** | Upload a picture of an error (PNG, JPG or WebP) | The likely cause and how to fix it |
| **Write a PR** | Paste your `git diff` (and an issue number if you have one) | A commit message and a ready-to-use PR description |

Extras: download any answer as a Markdown file, switch between light and dark theme, and see friendly error messages instead of scary stack traces.

---

## Quick start

You need **Python 3.9+** and internet. The AI runs on Google's servers, so your computer doesn't need to be powerful.

**1. Get the code**

```bash
git clone https://github.com/shobhit-lab/IssueScout.git
cd IssueScout
```

**2. Install**

```bash
pip install -r requirements.txt
```

**3. Add your free Gemini key**

Get one at [Google AI Studio](https://aistudio.google.com), then run:

```bash
export GEMINI_API_KEY="your-key"     # macOS / Linux
setx GEMINI_API_KEY "your-key"       # Windows (reopen the terminal after)
```

> Skipping this step is fine. You can also paste the key into the app's sidebar.

**4. Run it**

```bash
streamlit run app.py
```

Open http://localhost:8501 and you're ready to go. 🎉

---

## API keys

| Key | Needed? | Why |
| --- | --- | --- |
| `GEMINI_API_KEY` | **Yes** | Powers the AI. Free from [Google AI Studio](https://aistudio.google.com) |
| `GITHUB_TOKEN` | No | Gives you more GitHub requests (5,000/hour instead of 60). Create one in [GitHub settings](https://github.com/settings/tokens) |

You can add keys in the app sidebar, as environment variables, or in `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key"
GITHUB_TOKEN = "your-token"
```

> ⚠️ **Never upload your keys to GitHub.** Add `.streamlit/secrets.toml` to your `.gitignore`.

---

## Choosing a model (optional)

The default model is `gemma-4-31b-it`. To use a different one, set `GEMMA_MODEL` or change **Advanced → Model ID** in the sidebar.

If a model is busy or unavailable, IssueScout automatically tries the next one: `gemma-3-27b-it`, then `gemini-2.5-flash`.

---

## Put it online (free)

1. Push `app.py` and `requirements.txt` to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **Create app**.
3. Choose your repo, branch `main`, and file `app.py`.
4. Under **Advanced settings → Secrets**, paste your keys in the TOML format shown above.
5. Click **Deploy**.

---

## Something not working?

| Problem | Fix |
| --- | --- |
| "Add your Gemini API key in the sidebar first." | Paste your key in the sidebar, or set `GEMINI_API_KEY`. |
| "GitHub rate limit reached." | Add a free GitHub token, or wait a few minutes. |
| "Repository not found." | Check the link. Private repos need a token with access. |
| "All models failed." | The model name may be wrong. Try another under **Advanced**. |
| Page looks too big | Delete the `html { zoom: 1.25; }` line at the end of the CSS in `app.py`. |

---

## Project files

```
├── app.py              # the whole app
├── requirements.txt    # Python packages
└── README.md           # this file
```

## Built with

[Streamlit](https://streamlit.io) (UI) · [Google Gen AI SDK](https://pypi.org/project/google-genai/) (AI) · [GitHub REST API](https://docs.github.com/en/rest) (issues and files) · [Pillow](https://python-pillow.org) (images) · [Requests](https://requests.readthedocs.io) (API calls)

## Contributing

Issues and pull requests are welcome. Happy Hacktoberfest! 🎃

## License

This project is licensed under the [MIT License](LICENSE).
