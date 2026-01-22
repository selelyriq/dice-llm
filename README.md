# Job Scout

A local-first job search assistant that intelligently matches your resume and LinkedIn profile to technology jobs on Dice.com using AI-powered analysis.

## Features

- 🔒 **Privacy-First**: All data stored locally, no external servers
- 🤖 **AI-Powered Matching**: Claude analyzes your profile and ranks jobs with transparent scoring
- 🔍 **Smart Search**: Generates optimized Dice queries from your skills and preferences
- ⚖️ **Adjustable Scoring**: Control what matters most (skills, seniority, location, etc.)
- 📊 **Dual Profile Support**: Merge insights from both resume and LinkedIn PDFs
- 🎯 **Transparent**: See exactly why each job matched and what keywords you're missing

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd job-scout

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Install dependencies
uv sync

# Run the app
uv run streamlit run src/app.py
```

The app will open at `http://localhost:8501`

## Usage

### First Time Setup

1. **Upload Your Profile**
   - Upload your resume PDF in the sidebar
   - Optionally upload your LinkedIn profile PDF
   - Claude will extract and merge both into a unified profile

2. **Configure Search Constraints**
   - Select workplace types (Remote, Hybrid, On-Site)
   - Set minimum salary expectations
   - Add target job titles
   - Choose tech focus areas
   - Set location and search radius

3. **Adjust Scoring Weights** (optional)
   - Fine-tune how jobs are ranked
   - Balance role fit, skill overlap, seniority, constraints, and freshness

4. **Generate & Review Queries**
   - Click "Generate Queries" to create 5 tailored Dice searches
   - Edit or remove queries as needed
   - Claude prioritizes based on your LinkedIn skill endorsements

5. **Execute Search**
   - Click "Execute Search" to fetch and rank matches
   - Review results with expandable score breakdowns
   - See missing keywords and improvement suggestions

### Structured Commands

- **Find Roles**: Execute search with current profile and constraints
- **Broaden Search**: Relaxes filters and adds adjacent titles
- **Tighten Search**: Raises minimum score threshold (70+)
- **Explain Match [job_id]**: Detailed breakdown for specific job
- **Resume Keywords**: Get keyword suggestions based on top matches

## Architecture

### Data Storage (Local Only)

```
.job-scout/
├── profile.json      # Merged resume profile
├── linkedin.json     # LinkedIn profile data
└── searches.jsonl    # Search history (append-only)
```

All data is git-ignored and stays on your machine.

### Scoring System

Each job gets a 0-100 score with transparent breakdown:

- **Role/Title Fit** (25 points): Match with your target titles
- **Skill Overlap** (30 points): Your skills found in job description
- **Seniority Match** (15 points): Experience level alignment
- **Constraints Match** (20 points): Remote/salary/location requirements
- **Freshness** (10 points): How recently posted

Weights are adjustable via sliders in the UI.

### Dice MCP Integration

Connects to `https://mcp.dice.com/mcp` using the official MCP Python client:
- No authentication required
- Max 5 queries per search session (rate-limited)
- Exponential backoff on failures (1s, 2s, 4s)
- Supports all Dice filter parameters

## Project Structure

```
job-scout/
├── src/
│   ├── app.py                      # Streamlit UI entry point
│   ├── core/
│   │   ├── resume.py               # PDF parsing & normalization
│   │   ├── prompts.py              # Prompt templates
│   │   ├── ranker.py               # Scoring logic
│   │   └── schemas.py              # Pydantic models
│   └── integrations/
│       ├── llm.py                  # Claude API wrapper
│       └── mcp_client.py           # Dice MCP client with retry logic
├── tests/
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Security & Privacy

- ✅ API keys stored in `.env` only (never committed)
- ✅ Resume and LinkedIn data stored locally (git-ignored)
- ✅ No external logging or analytics
- ✅ Job descriptions treated as untrusted input
- ✅ Throttled requests to respect Dice ToS

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/
```

## Why Streamlit?

- **Superior state management**: Robust handling of profile data and editable queries
- **Better layout control**: Native columns, sidebar, expanders for complex UIs
- **Form-heavy apps**: Excels with many inputs (sliders, checkboxes, text areas)
- **Professional UX**: Product-like feel vs ML demo aesthetic
- **Multi-page ready**: Easy to extend with history viewer, settings, etc.

## Future Extensions

- Multi-board support (LinkedIn, Indeed, Greenhouse, Lever)
- ATS keyword mode for resume optimization
- CSV export for tracking and follow-up
- Team mode with shared profile templates

## License

MIT

## Contributing

This is a mentorship group utility. Contributions welcome! Open an issue or PR.
