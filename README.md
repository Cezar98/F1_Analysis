# F1 Analysis App (FastF1 + OpenAI)

A ready-to-run Streamlit app that lets you:
- Explore Formula 1 sessions (2018+)
- Analyze a single driver's lap performance with AI
- Compare two drivers with AI
- Download generated AI analysis as a `.txt` file

## What this project needs to run

- **Python 3.10+** (recommended: 3.11)
- An **OpenAI API key** (optional, only needed for AI analysis)
- Internet access (FastF1 fetches session data)

## Quick start (local machine)

```bash
# 1) Clone
git clone <your-repo-url>
cd F1_Analysis

# 2) Create virtual environment
python -m venv .venv

# 3) Activate it
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

# 4) Install dependencies
pip install -r requirements.txt

# 5) Set API key (optional but required for AI features)
# macOS/Linux
export OPENAI_API_KEY="your_api_key_here"
# Windows PowerShell
# $env:OPENAI_API_KEY="your_api_key_here"

# 6) Run the app
streamlit run F1.py
```

Then open the local URL Streamlit prints (typically `http://localhost:8501`).

## Usage

1. Select a season.
2. Select a Grand Prix.
3. Select a session.
4. Choose one service:
   - **Analyze driver performance**
   - **Compare drivers**
5. Run AI analysis and download the output text file.

## Notes

- AI features are disabled if `OPENAI_API_KEY` is not set.
- FastF1 cache is stored in the `cache/` directory for faster repeated runs.
- For seasons before 2018, data coverage can be less complete.

## Troubleshooting

- **No OpenAI analysis button available:** Set `OPENAI_API_KEY` and restart Streamlit.
- **Session load errors:** Retry later; timing APIs can occasionally fail.
- **Slow first run:** Normal behavior while FastF1 populates cache.

## License

This project is licensed under the terms in `LICENSE`.
