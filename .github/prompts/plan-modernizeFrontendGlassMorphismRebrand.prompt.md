## Plan: Modernize Frontend with Glass-Morphism & Rebrand to ScriptClub Scout

Transform the Streamlit app with a sleek glass-morphism design featuring a medium-blur frosted-glass sidebar, background gradient behind the homepage header, and glass-effect on all expanders. Rebrand from "Job Scout" to "ScriptClub Scout" across all 20+ locations. Maintain current green/red/blue semantic colors and Streamlit default fonts.

### Steps

1. **Create `.streamlit/config.toml`** with dark theme base, custom primary colors (purple-blue gradient palette: #667eea, #764ba2), and dark background to support glass-morphism aesthetics
2. **Inject global glass-morphism CSS** in [Home.py](Home.py#L12) targeting `[data-testid="stSidebar"]` with 10px backdrop-filter blur and rgba(255,255,255,0.05) background, `[data-testid="stExpander"]` with frosted-glass effect, border-radius, and subtle borders, plus styling for metrics and hiding default grey borders
3. **Add gradient background to header section** in [Home.py](Home.py#L16-L22) by injecting CSS div with linear-gradient (purple-blue) positioned behind existing title/welcome text using absolute positioning or wrapping in custom HTML container
4. **Replicate glass-morphism CSS** to all 5 page files in [pages/](pages/) after their `set_page_config` calls for consistent transparent sidebar, glass expanders, and component styling across the entire app
5. **Global rebrand to "ScriptClub Scout"** via find-replace in [Home.py](Home.py), [pages/1_🎯_Job_Search.py](pages/1_🎯_Job_Search.py), [pages/2_📊_Market_Intelligence.py](pages/2_📊_Market_Intelligence.py), [pages/3_📜_Search_History.py](pages/3_📜_Search_History.py), [pages/4_📊_Profile_Comparison.py](pages/4_📊_Profile_Comparison.py), [pages/5_⚙️_Settings.py](pages/5_⚙️_Settings.py), [README.md](README.md), [IMPLEMENTATION.md](IMPLEMENTATION.md), [QUICKSTART.md](QUICKSTART.md), [pyproject.toml](pyproject.toml), [src/**init**.py](src/__init__.py), [src/app.py](src/app.py), [src/ui/components.py](src/ui/components.py), [scripts/setup.sh](scripts/setup.sh), [scripts/verify.py](scripts/verify.py), and [tests/test_basic.py](tests/test_basic.py)
6. **Enhance feature cards and sections** in [Home.py](Home.py#L26-L96) by adding subtle glass-effect borders and backgrounds to the 2-column feature grid, getting-started section, and privacy notice using custom CSS classes

### Further Considerations

1. **Gradient positioning**: Should the gradient span full viewport height / Stop at header section / Fade to solid dark background partway down the page?
2. **Logo/branding**: Add "ScriptClub Scout" logo/icon to header / Keep text-only with emoji / Create custom icon to replace 🎯?
