@echo off
REM One command: scrape the WHOLE state (all regions, all sources) into the unified DB.
REM Double-click this, or run from a terminal in the repo folder.
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python not found. Install Python 3 first. & pause & exit /b)
python -m pip install requests --quiet
python scraper\run_region.py all --sources facts,pur,thp
echo.
echo Done. Unified DB: data\db\applications.sqlite   Statewide map: data\exports\california.geojson
pause
