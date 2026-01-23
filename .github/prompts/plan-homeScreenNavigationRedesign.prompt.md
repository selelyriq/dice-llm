# ScriptClub Scout - Home Screen & Navigation Redesign Plan

## Overview

Redesign the ScriptClub Scout application with a centered home screen, top navigation bar, tab-based layouts with state persistence, and consolidated CSS styling.

## Design Decisions

- **Navigation**: Top horizontal navigation bar (text-only, no emojis)
- **Layout**: Tab-based interface for pages with multiple sections
- **State Management**: Preserve tab state across page navigations
- **Styling**: Consolidated CSS in shared module
- **Sidebar**: Completely hidden, all content moved to main area
- **File Naming**: Keep number prefixes (1*, 2*, etc.) for consistent ordering
- **Tab Names**: Descriptive names for clarity

## Implementation Steps

### 1. Create Consolidated Styles Module

**File**: `src/ui/styles.py`

**Functions**:

- `get_glass_morphism_styles()` - Returns CSS string with:
  - Original glass-morphism dark theme with purple/blue gradients
  - White borders (rgba(255, 255, 255, 1)) for better contrast
  - Sidebar completely hidden: `section[data-testid="stSidebar"] { display: none !important; }`
  - Top navigation bar styles
  - Home page centered content styles
  - Navigation card styles
- `load_styles()` - Applies styles to current page using `st.markdown()`

**Key CSS Classes Added**:

- `.top-nav` - Navigation bar container
- `.top-nav-home` - "ScriptClub Scout" home link
- `.top-nav-links` - Container for page links
- `.top-nav-link` - Individual page link
- `.top-nav-link-active` - Active page highlight
- `.home-center` - Centered home page content
- `.nav-card` - Navigation cards on home page

### 2. Create Top Navigation Component

**File**: `src/ui/navigation.py`

**Function**: `render_top_nav(current_page: str = "Home")`

**Structure**:

- Left side: "ScriptClub Scout" link to home (preserves tab states when clicked)
- Right side: Text-only links to all pages
  - Job Search
  - Market Intelligence
  - Search History
  - Profile Comparison
  - Settings
- Highlights current active page
- Uses custom HTML/CSS for styling
- Alternative implementation with `st.page_link()` commented out as fallback

**Pages List**:

```python
pages = [
    ("Home", "Home.py"),
    ("Job Search", "pages/1_Job_Search.py"),
    ("Market Intelligence", "pages/2_Market_Intelligence.py"),
    ("Search History", "pages/3_Search_History.py"),
    ("Profile Comparison", "pages/4_Profile_Comparison.py"),
    ("Settings", "pages/5_Settings.py"),
]
```

### 3. Redesign Home Page

**File**: `Home.py`

**Changes**:

1. Import consolidated styles and navigation: `from src.ui.styles import load_styles` and `from src.ui.navigation import render_top_nav`
2. Apply styles: `load_styles()`
3. Render navigation: `render_top_nav("Home")`
4. Center title and description using `.home-center` CSS class
5. **Remove**: Features text section (4 floating text blocks)
6. **Add**: 6 navigation button cards in 2x3 grid using `st.columns(3)`:
   - Job Search
   - Market Intelligence
   - Search History
   - Profile Comparison
   - Settings
   - (Optional 6th card for documentation/help)
7. Each card uses `st.page_link()` for navigation
8. Keep: Getting Started section, Privacy Notice
9. Optional: Add centered subtitle/tagline

**Navigation Cards Content**:

- Job Search: "Upload resume & LinkedIn profile • AI-powered query generation • Smart job scoring"
- Market Intelligence: "Analyze job market trends • Skill demand analysis • Salary distributions"
- Search History: "View past searches • Rerun successful queries • Track your progress"
- Profile Comparison: "Track resume changes • Compare skill evolution • Visual diff analysis"
- Settings: "Configure API keys • Manage data retention • Privacy settings"

### 4. Refactor Job Search Page

**File**: Rename `pages/1_🎯_Job_Search.py` → `pages/1_Job_Search.py`

**Changes**:

1. Remove emoji from filename
2. Import styles and navigation
3. Replace inline CSS with `load_styles()`
4. Add `render_top_nav("Job Search")`
5. Initialize tab state: `if "job_search_tab" not in st.session_state: st.session_state.job_search_tab = 0`
6. Create tabs using `st.tabs()`:

**Tab Structure**:

- **Tab 1: "Profile & Constraints"**
  - Profile status display (current profile name, dates)
  - Resume file uploader
  - LinkedIn file uploader
  - Process Documents button
  - All search constraints:
    - Workplace types multiselect
    - Employment types multiselect
    - Minimum salary input
    - Location with radius slider
    - Posted date selectbox
    - Sponsor visa checkbox
    - Easy apply checkbox
    - Max jobs to rank

- **Tab 2: "Scoring & Queries"**
  - Two columns:
    - Left: Scoring Weights sliders (Role Fit, Skill Overlap, Seniority Match, Constraints Match, Freshness)
    - Right: Generated Queries (AI-generated, editable text areas)

- **Tab 3: "Results & Analysis"**
  - Job matches display
  - Expandable cards with scores
  - Match explanations
  - Matched skills & missing keywords

**Bottom Section (Outside Tabs)**:

- Commands buttons: Find Roles, Broaden Search, Tighten Search, Resume Keywords

**Tab State Management**:

```python
selected_tab = st.tabs(["Profile & Constraints", "Scoring & Queries", "Results & Analysis"])
```

### 5. Refactor Market Intelligence Page

**File**: Rename `pages/2_📊_Market_Intelligence.py` → `pages/2_Market_Intelligence.py`

**Changes**:

1. Remove emoji from filename
2. Import styles and navigation
3. Replace inline CSS with `load_styles()`
4. Add `render_top_nav("Market Intelligence")`
5. Initialize tab state: `if "market_tab" not in st.session_state: st.session_state.market_tab = 0`

**Tab Structure**:

- **Tab 1: "Search Parameters"**
  - Keywords text area (multi-line)
  - Posted date selectbox
  - Jobs per keyword number input
  - Workplace types multiselect
  - "🔍 Analyze Market Trends" button

- **Tab 2: "Results & Charts"**
  - Market overview metrics (4 columns)
  - Aggregate overview with charts
  - Trends by keyword (expandable sections)
  - AI insights expander

- **Tab 3: "Export & Settings"**
  - Chart engine selector (plotly vs altair)
  - Export CSV button
  - Additional export options

### 6. Refactor Search History Page

**File**: Rename `pages/3_📜_Search_History.py` → `pages/3_Search_History.py`

**Changes**:

1. Remove emoji from filename
2. Import styles and navigation
3. Replace inline CSS with `load_styles()`
4. Add `render_top_nav("Search History")`
5. Initialize tab state: `if "history_tab" not in st.session_state: st.session_state.history_tab = 0`

**Tab Structure**:

- **Tab 1: "Search History"**
  - Statistics metrics (4 columns: Total Searches, Jobs Found, Avg Score, Top Score)
  - Date range display
  - Search history list with expandable cards:
    - Timestamp, results count, top score
    - Queries used
    - Search constraints
    - Top matches
    - Action buttons (Rerun, Copy, Delete)

- **Tab 2: "Filters & Options"**
  - Date range filter (All Time, Last 7 Days, Last 30 Days, Custom Range)
  - Custom date inputs (From/To)
  - Score filter slider (Minimum top score)
  - Apply filters button

- **Tab 3: "Data Management"**
  - Retention policy info (privacy mode status, days retained)
  - Link to Settings page
  - Export History as JSON button
  - Clear All History button (with confirmation)

### 7. Refactor Profile Comparison Page

**File**: Rename `pages/4_📊_Profile_Comparison.py` → `pages/4_Profile_Comparison.py`

**Changes**:

1. Remove emoji from filename
2. Import styles and navigation
3. Replace inline CSS with `load_styles()`
4. Add `render_top_nav("Profile Comparison")`
5. Initialize tab state: `if "profile_comparison_tab" not in st.session_state: st.session_state.profile_comparison_tab = 0`

**Tab Structure**:

- **Tab 1: "Update Profile"**
  - Resume file uploader
  - LinkedIn file uploader
  - "🔄 Process and Archive Current Version" button
  - Current profile status

- **Tab 2: "Compare Versions"**
  - Version selector dropdown
  - Two-column comparison (Current vs Selected)
  - Profile summaries with metrics
  - Detailed comparison:
    - Skills added/removed
    - Title changes
    - Keyword density comparison
  - Visual diff display

- **Tab 3: "Evolution Timeline"**
  - Line charts showing skills over time
  - Experience timeline
  - Data table view
  - Version management info (keeps last 10)

### 8. Refactor Settings Page

**File**: Rename `pages/5_⚙️_Settings.py` → `pages/5_Settings.py`

**Changes**:

1. Remove emoji from filename
2. Import styles and navigation
3. Replace inline CSS with `load_styles()`
4. Add `render_top_nav("Settings")`
5. Initialize tab state: `if "settings_tab" not in st.session_state: st.session_state.settings_tab = 0`

**Tab Structure**:

- **Tab 1: "API Keys & Privacy"**
  - API Keys Section:
    - Anthropic API key input (password)
    - Save button
  - Privacy & Data Retention Section:
    - Privacy mode toggle
    - Market snapshot TTL
    - Search history retention days
    - Max market snapshots
    - Auto-cleanup toggle
    - Save retention settings button

- **Tab 2: "Storage & Data Management"**
  - Storage Usage Section:
    - Total storage metric with status indicator
    - Progress bar (1024 MB limit)
    - Storage breakdown (Profiles, Searches, Market Data)
  - Data Management Section:
    - Run Retention Policy Cleanup button
    - Force Auto-Cleanup button
    - Export all data button
    - Clear market data button
    - Clear search history button
    - Data directory path display

- **Tab 3: "Visualization Preferences"**
  - Chart engine radio (plotly/altair)
  - Color scheme selectbox
  - Other display preferences

## State Persistence Implementation

All pages use session state to remember tab selections:

```python
# Initialize tab state (do once per page)
if "page_name_tab" not in st.session_state:
    st.session_state.page_name_tab = 0

# Create tabs and bind to state
tabs = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
for idx, tab in enumerate(tabs):
    with tab:
        if idx == st.session_state.page_name_tab:
            # Render tab content
            pass
```

**Home Button Behavior**: Clicking "ScriptClub Scout" preserves all tab states when returning to pages.

## File Structure After Changes

```
Home.py (updated)
pages/
  1_Job_Search.py (renamed, refactored)
  2_Market_Intelligence.py (renamed, refactored)
  3_Search_History.py (renamed, refactored)
  4_Profile_Comparison.py (renamed, refactored)
  5_Settings.py (renamed, refactored)
src/
  ui/
    __init__.py
    styles.py (new)
    navigation.py (new)
    components.py (existing)
    charts.py (existing)
```

## Testing Checklist

- [ ] Styles load correctly on all pages
- [ ] Top navigation displays and links work
- [ ] Sidebar is completely hidden
- [ ] Home page centered layout renders correctly
- [ ] Navigation cards on home page are clickable
- [ ] All 5 pages render with tabs
- [ ] Tab state persists when navigating between pages
- [ ] Clicking "ScriptClub Scout" returns home without resetting tab states
- [ ] All functionality from original sidebars works in new tab layouts
- [ ] White borders visible on dark blocks
- [ ] Mobile responsiveness acceptable
- [ ] No console errors
- [ ] File uploads work in new tab layout
- [ ] Forms and inputs function correctly
- [ ] Buttons and actions work as expected

## Rollback Plan

If issues arise:

1. Keep original page files as backups (e.g., `1_🎯_Job_Search.py.bak`)
2. Original inline CSS can be restored to each page
3. Streamlit's default sidebar can be re-enabled by removing `display: none`
4. Tab structure can be reverted to original layout

## Future Enhancements

- Responsive CSS breakpoints for mobile
- Dark/light theme toggle
- Customizable color schemes
- Keyboard shortcuts for navigation
- Search functionality in top nav
- User preferences saved to localStorage
- Animation transitions between tabs
- Progress indicators for long-running operations
