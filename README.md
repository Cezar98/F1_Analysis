# F1 Analysis App

An interactive **Streamlit** app that lets users:

- Select an F1 season, Grand Prix, and session.
- Analyze one driver's performance from lap and weather data.
- Compare two drivers in the same session.
- Export AI analysis as a downloadable `.txt` file.

The app uses:

- [FastF1](https://theoehrly.github.io/Fast-F1/) for race/session telemetry and timing data.
- OpenAI Responses API for concise performance summaries.

## 1) What someone can download and use

This repository is now runnable on any computer with Python 3.10+.

A user only needs to:

1. Download/clone this repository.
2. Install dependencies.
3. Set an OpenAI API key (optional but required for AI analysis).
4. Run the Streamlit app.

## 2) Quick start

### Prerequisites

- Python 3.10+
- `pip`

### Install

```bash
git clone <your-repo-url>
cd F1_Analysis
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure API key (for AI features)

Option A — environment variable:

```bash
export OPENAI_API_KEY="your_api_key_here"  # Windows PowerShell: $env:OPENAI_API_KEY="..."
```

Option B — Streamlit secrets (recommended for local app secrets):

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

### Run

```bash
streamlit run F1.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## 3) How users export results

After generating analysis in either mode:

- **Analyze driver performance**: click **Download Analysis as Text File**.
- **Compare drivers**: click **Download Analysis as Text File**.

The file will download with a descriptive name that includes season/race/session and driver(s).

## 4) Notes

- If no API key is set, AI buttons are disabled, but browsing sessions/drivers and plotting still works.
- First load can take longer while FastF1 cache is created.
- FastF1 historical availability may vary by season/session.
