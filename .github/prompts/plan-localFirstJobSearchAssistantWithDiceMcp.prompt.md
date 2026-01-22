# Plan: Local-First Job Search Assistant with Dice MCP

Build a privacy-focused Python app that parses resumes and LinkedIn profiles with pypdf2, generates natural language job searches via the remote Dice MCP server at https://mcp.dice.com/mcp, and ranks matches with Claude—saving user data locally in `.job-scout/` directory with full transparency and user control.

## Steps

1. **Bootstrap Python project** with [pyproject.toml](pyproject.toml) (dependencies: `streamlit`, `pypdf2`, `anthropic`, `mcp`, `python-dotenv`, `pydantic`, `httpx`), [.env.example](.env.example) for ANTHROPIC_API_KEY, [.gitignore](.gitignore) including `.job-scout/`, [README.md](README.md) with setup instructions, and folder structure: `src/`, `src/core/`, `src/integrations/`, `scripts/`, `tests/`

2. **Build wrapped MCP client** in [src/integrations/mcp_client.py](src/integrations/mcp_client.py) connecting to `https://mcp.dice.com/mcp` via HTTP transport with exponential backoff retry logic (1s, 2s, 4s intervals), HTTP 429 rate limit handling, connection error recovery, and detailed validation error messages for `search_jobs` parameters

3. **Implement dual-source profile parsing with auto-load** in [src/core/resume.py](src/core/resume.py): on app start, check for `.job-scout/profile.json` and `.job-scout/linkedin.json`, display "Current Profile: [name] (Resume: [date], LinkedIn: [date])"; on new uploads, extract text with pypdf2 from resume and/or LinkedIn PDF, merge and normalize with Claude into unified `ResumeProfile` schema in [src/core/schemas.py](src/core/schemas.py), save both sources separately (overwrite)

4. **Create transparent query generation and adjustable ranking** in [src/core/ranker.py](src/core/ranker.py) and [src/core/prompts.py](src/core/prompts.py): Claude generates 5 Dice queries shown to user with edit/remove options before execution, fetch results via MCP with appropriate filters, dedupe by job ID, score with user-adjustable weight sliders (role fit: 0-100, skill overlap: 0-100, seniority: 0-100, constraints: 0-100, freshness: 0-100)

5. **Build three-column Streamlit UI** in [src/app.py](src/app.py): left column with `st.sidebar` for profile display (resume + LinkedIn upload widgets) + constraint inputs (workplace_types checkboxes, employment_types, min salary, target titles, tech focus, location/radius, posted_date); middle column for scoring weight sliders + generated query review with `st.text_area` editable fields + "Execute Search" button; right column for `st.spinner` progress + results cards using `st.expander` for match breakdowns, missing keywords, job details, and action links

6. **Add session persistence and structured commands** in [src/app.py](src/app.py): use `st.session_state` for in-session data, append each search (timestamp, constraints, queries, results count, top matches) to `.job-scout/searches.jsonl`, implement command router using `st.selectbox` or button row for "Find roles", "Broaden search" (relaxes filters + adds adjacent titles), "Tighten search" (raises score thresholds), "Explain match [job_id]", "Resume keywords" with prompt templates in [src/core/prompts.py](src/core/prompts.py)

## Architecture Details

### Dependencies

- **streamlit**: Production-ready web UI framework with superior state management and layout control
- **pypdf2**: Resume and LinkedIn PDF text extraction
- **anthropic**: Claude API for profile normalization, query generation, and ranking
- **mcp**: Official MCP Python client for HTTP transport
- **python-dotenv**: Environment variable management
- **pydantic**: Data validation and schemas
- **httpx**: HTTP client with retry capabilities

### Data Storage (Local, Git-Ignored)

```
.job-scout/
  profile.json           # Merged resume profile (overwritten on new upload)
  linkedin.json          # Parsed LinkedIn profile data (overwritten on new upload)
  searches.jsonl         # Append-only search history (one JSON per line)
```

### MCP Integration

- **Server URL**: `https://mcp.dice.com/mcp`
- **Transport**: HTTP/SSE (remote server)
- **Tool**: `search_jobs` with parameters:
  - `keyword` (required)
  - `location`, `radius`, `radius_unit`
  - `workplace_types`: ["Remote", "On-Site", "Hybrid"]
  - `employment_types`: ["FULLTIME", "CONTRACTS", "PARTTIME", "THIRD_PARTY"]
  - `posted_date`: "ONE", "THREE", "SEVEN"
  - `willing_to_sponsor`, `easy_apply`
  - `jobs_per_page` (1-100), `page_number`
- **Rate Limit**: Max 5 queries per search session
- **Error Handling**: Exponential backoff (1s, 2s, 4s) on failures

### Profile Schemas

```python
class ResumeProfile(BaseModel):
    target_titles: List[str]
    core_skills: List[str]  # Top 20
    secondary_skills: List[str]
    cloud_stack: List[str]  # aws, azure, gcp
    years_experience_estimate: int
    recent_roles: List[Dict[str, str]]  # title, company, years
    keywords_to_emphasize: List[str]
    extracted_name: Optional[str]
    sources: Dict[str, bool]  # {"resume": True, "linkedin": True}
    last_updated: str  # ISO timestamp

class LinkedInProfile(BaseModel):
    skills: List[str]  # All listed skills
    endorsements: Dict[str, int]  # skill -> endorsement count
    experience: List[Dict[str, str]]  # Detailed work history
    projects: List[Dict[str, str]]  # Projects and accomplishments
    certifications: List[str]
    extracted_name: Optional[str]
    last_updated: str  # ISO timestamp
```

### Scoring System (User-Adjustable Weights)

- **Role/Title Fit** (default: 25/100): Match between target titles and job title
- **Skill Overlap** (default: 30/100): Core skills found in job description
- **Seniority Match** (default: 15/100): Years experience vs job level
- **Constraints Match** (default: 20/100): Remote/salary/location/sponsorship requirements
- **Freshness** (default: 10/100): How recently posted

Each job gets a 0-100 score with transparent breakdown shown to user.

### Query Generation Flow

1. Claude analyzes merged resume + LinkedIn profile + user constraints
2. Generates 5 diverse Dice queries as natural language (leveraging LinkedIn skill endorsements for priority)
3. Displays queries to user in Streamlit `st.text_area` editable fields
4. User can edit, remove (clear field), or approve queries
5. On approval, convert to `search_jobs` MCP calls with appropriate filters
6. Fetch results, dedupe by job ID, rank with scoring system

### Structured Chat Commands

- **"Find roles"**: Execute search with current profile + constraints
- **"Broaden search"**: Relaxes filters (expand location radius, add adjacent titles, remove posted_date filter)
- **"Tighten search"**: Raises minimum score threshold (e.g., only show 70+ matches)
- **"Explain match [job_id]"**: Detailed breakdown of why specific job scored as it did
- **"Resume keywords"**: Analyzes top matches, suggests keywords to add to resume

## Security & Privacy

- API keys in `.env` only (never committed)
- Resume and LinkedIn data stored locally in `.job-scout/` (git-ignored)
- No external logging or analytics
- Job descriptions treated as untrusted input (strict system prompts)
- Throttled requests to respect Dice ToS

## User Experience Flow

1. **First Run**: User uploads resume and/or LinkedIn PDF → Claude extracts and merges profiles → Saved to `.job-scout/profile.json` and `.job-scout/linkedin.json`
2. **Return Visit**: App auto-loads both profiles, shows "Current Profile: [Name] (Resume: [date], LinkedIn: [date])" in sidebar
3. **Configure Search**: User sets constraints via sidebar widgets (remote, salary, titles, tech focus, location)
4. **Adjust Scoring**: User tweaks weight sliders in main column if needed (optional, defaults provided)
5. **Generate Queries**: Click "Generate Queries" → Claude produces 5 queries → Displayed in editable text areas
6. **Execute Search**: Click "Execute Search" → Progress spinner shown → Results appear in right column with scores
7. **Review Results**: Click expanders to see match breakdown, missing keywords, job details, apply links
8. **Follow-Up**: Use command buttons/selectbox to refine search or analyze matches

## Setup Instructions (README)

```bash
git clone <repo>
cd job-scout
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
uv sync
uv run streamlit run src/app.py
# Streamlit opens at http://localhost:8501
```

## Why Streamlit Over Gradio

- **Superior state management**: `st.session_state` robustly handles profile data, editable queries, and search history
- **Better layout control**: Native `st.columns`, `st.sidebar`, `st.expander`, `st.tabs` for complex three-column design
- **Form-heavy apps**: Excels with many inputs (sliders, checkboxes, text areas) which this app requires
- **Professional UX**: Product-like feel vs Gradio's ML demo aesthetic, better for mentorship group utility
- **Multi-page ready**: Easy to add search history viewer, settings, profile comparison pages later

## Implementation Ready

This plan is complete and actionable. All architectural decisions finalized:

- Remote MCP server via wrapped client with retry logic
- Dual-source profiles (resume + LinkedIn), merged intelligently, overwrite on new uploads
- Append-only search history in JSONL format
- 5-query limit with user transparency and Streamlit-powered editing
- Adjustable scoring weights for multi-level mentorship group (entry to senior)
- Local-first with `.gitignore` protection, no external data storage
