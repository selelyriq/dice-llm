# Quick Start Guide

## Installation

1. **Ensure prerequisites are installed:**
   ```bash
   # Check Python version
   python --version  # Should be 3.10+
   
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Run the setup script:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Configure your API key:**
   ```bash
   # Edit .env and add your Anthropic API key
   nano .env
   # Or use your preferred editor
   ```

4. **Run the app:**
   ```bash
   uv run streamlit run src/app.py
   ```

The app will open at `http://localhost:8501`

## First-Time Use

1. **Upload Your Profile**
   - In the sidebar, upload your resume PDF
   - Optionally upload your LinkedIn profile PDF
   - Click "Process Documents" to extract and normalize your profile

2. **Set Search Constraints**
   - Choose workplace types (Remote, Hybrid, On-Site)
   - Select employment types (Full-time, Contracts, etc.)
   - Set location and radius if needed
   - Configure other filters (salary, visa sponsorship, etc.)

3. **Adjust Scoring Weights** (optional)
   - Use the sliders in the first column to control how jobs are ranked
   - Higher weights mean that factor matters more

4. **Generate Search Queries**
   - Click "Generate Queries" to have Claude create 5 Dice searches
   - Edit the generated queries if needed
   - Remove any queries you don't want (clear the text)

5. **Execute Search**
   - Click "Execute Search" to fetch jobs from Dice
   - The app will rank all results against your profile
   - View results in the right column

6. **Review Results**
   - Click on any job to expand details
   - See score breakdowns and match explanations
   - Click "View Job" to see the full posting on Dice
   - Click "Explain Match" for detailed analysis

## Structured Commands

- **Resume Keywords**: Get suggestions for keywords to add to your resume based on top matches
- **Tighten Search**: Filter to show only jobs scoring 70+
- **Broaden Search**: Coming soon - automatically relax filters

## Data Storage

All your data is stored locally in `~/.job-scout/`:
- `profile.json` - Your unified resume profile
- `linkedin.json` - Your LinkedIn profile data
- `searches.jsonl` - History of all your searches

This directory is git-ignored for privacy.

## Troubleshooting

### API Key Issues
```bash
# Make sure your API key is set
cat .env | grep ANTHROPIC_API_KEY
```

### PDF Extraction Issues
- Ensure PDFs are text-based (not scanned images)
- Try re-exporting from the source application

### MCP Connection Issues
- Check your internet connection
- The Dice MCP server is at https://mcp.dice.com/mcp
- If getting rate limits, wait a few minutes between searches

### Streamlit Issues
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache

# Restart the app
uv run streamlit run src/app.py
```

## Tips for Best Results

1. **LinkedIn Profile**: If you have one, upload it! The endorsement data helps prioritize skills
2. **Edit Queries**: The AI-generated queries are good, but you know your search best
3. **Adjust Weights**: Junior roles? Increase "role_fit". Senior? Increase "skill_overlap"
4. **Location Strategy**: For remote roles, leave location empty
5. **Freshness**: Recent postings (ONE/THREE days) are more likely to still be available

## Next Steps

Check the main [README.md](README.md) for full documentation and architecture details.
