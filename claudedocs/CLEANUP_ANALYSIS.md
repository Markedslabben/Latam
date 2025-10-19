# Project Cleanup Analysis

## Current State

After archiving legacy code and organizing the framework, you have:

```
Latam/
├── latam_hybrid/          # ✅ New framework (KEEP)
├── legacy/                # ✅ Archived old code (KEEP for now)
├── claudedocs/            # ✅ Project documentation (KEEP)
├── scripts/               # ❓ Utility scripts (EVALUATE)
├── Planningarea_shp/      # ❓ GIS shapefiles (EVALUATE)
└── Root files             # ❓ Various config/misc files (EVALUATE)
```

---

## File-by-File Analysis

### ✅ KEEP (Essential)

| File/Directory | Purpose | Action |
|----------------|---------|--------|
| **latam_hybrid/** | Framework package | **KEEP** - Production code |
| **legacy/** | Archived old code | **KEEP** - Reference |
| **claudedocs/** | Project documentation | **KEEP** - Important docs |
| **README.md** | Project readme | **KEEP** - Main documentation |
| **pyproject.toml** | Package config | **KEEP** - Essential |
| **pytest.ini** | Test configuration | **KEEP** - Essential |
| **environment.yaml** | Conda environment | **KEEP** - Essential |
| **requirements.txt** | Python dependencies | **KEEP** - Essential |
| **.env.example** | Environment template | **KEEP** - Useful reference |

---

## ❓ EVALUATE - scripts/

### Utility Scripts (Data Validation)

**KEEP - Useful utilities:**

| Script | Purpose | Recommendation |
|--------|---------|----------------|
| **check_leap_years.py** | Validate wind data leap years | ✅ **KEEP** - Updated to use path helpers |
| **check_pvgis_leap_years.py** | Validate solar data leap years | ✅ **KEEP** - Updated to use path helpers |
| **compare_winddata.py** | Compare wind datasets | ✅ **KEEP** - Updated to use path helpers |
| **analyze_weibull_10years.py** | Weibull distribution analysis | ✅ **KEEP** - Statistical analysis |
| **plot_weibull_comparison.py** | Weibull visualization | ✅ **KEEP** - Useful plots |
| **gis_visualization.py** | GIS plotting utilities | ✅ **KEEP** - Visualization tool |

**ARCHIVE or DELETE - Not actively used:**

| Script | Purpose | Recommendation |
|--------|---------|----------------|
| **pdf_to_markdown.py** | Convert PDFs to markdown | ❌ **ARCHIVE** - One-time utility |
| **README.md** | Old readme | ❌ **DELETE** - Outdated |
| **README-task-master.md** | Old task readme | ❌ **DELETE** - Outdated |
| **dev.js** | JavaScript dev script | ❌ **DELETE** - Not needed |
| **example_prd.txt** | Example PRD | ❌ **DELETE** - Template |
| **prd.txt** | PRD file | ❌ **DELETE** - Project doc |
| **task-complexity-report.json** | Complexity report | ❌ **DELETE** - Old analysis |

---

## ❓ EVALUATE - Root Files

### Configuration Files - KEEP

| File | Purpose | Action |
|------|---------|--------|
| pyproject.toml | Package configuration | ✅ **KEEP** |
| pytest.ini | Test configuration | ✅ **KEEP** |
| environment.yaml | Conda environment | ✅ **KEEP** |
| requirements.txt | Python dependencies | ✅ **KEEP** |
| .env.example | Environment template | ✅ **KEEP** |
| .gitignore | Git ignore rules | ✅ **KEEP** (or create if missing) |

### JavaScript/Node Files - DELETE

| File | Purpose | Action |
|------|---------|--------|
| package.json | Node.js config | ❌ **DELETE** - Not using JavaScript |
| package-lock.json | Node.js lockfile | ❌ **DELETE** - Not using JavaScript |

### Old/Obsolete Files - ARCHIVE or DELETE

| File | Purpose | Action |
|------|---------|--------|
| README-task-master.md | Old readme | ❌ **DELETE** - Outdated |
| .windsurfrules | Windsurf config | ❓ **KEEP** - If using Windsurf IDE |
| setup_env.bat | Environment setup | ❓ **EVALUATE** - Windows helper |
| switch_env.bat | Environment switcher | ❓ **EVALUATE** - Windows helper |

### Image Files - ARCHIVE

| File | Size | Action |
|------|------|--------|
| site_shading_analysis.png | 853 KB | ❌ **ARCHIVE** - Old result image |
| turbine_plot.png | 81 KB | ❌ **ARCHIVE** - Old result image |
| windrose.png | 86 KB | ❌ **ARCHIVE** - Old result image |

### GIS Data - KEEP or ORGANIZE

| Directory | Purpose | Action |
|-----------|---------|--------|
| Planningarea_shp/ | Planning area shapefiles | ❓ **MOVE** to `latam_hybrid/Inputdata/GISdata/` or archive |

---

## Cleanup Recommendations

### Priority 1: DELETE (Safe to Remove)

**JavaScript/Node files (not needed):**
```bash
rm package.json package-lock.json
```

**Old documentation in scripts/:**
```bash
rm scripts/README.md
rm scripts/README-task-master.md
rm scripts/dev.js
rm scripts/example_prd.txt
rm scripts/prd.txt
rm scripts/task-complexity-report.json
```

**Old root documentation:**
```bash
rm README-task-master.md
```

### Priority 2: ARCHIVE (Move to legacy)

**Old result images:**
```bash
mkdir -p legacy/old_misc
mv *.png legacy/old_misc/
```

**One-time utility scripts:**
```bash
mv scripts/pdf_to_markdown.py legacy/old_misc/
```

### Priority 3: ORGANIZE

**Move Planningarea_shp to proper location:**

Option A - Move to Inputdata:
```bash
mv Planningarea_shp/ latam_hybrid/Inputdata/GISdata/
```

Option B - Archive if redundant:
```bash
mv Planningarea_shp/ legacy/old_misc/
```

**Keep useful scripts organized:**
```bash
# scripts/ directory keeps:
# - check_leap_years.py
# - check_pvgis_leap_years.py
# - compare_winddata.py
# - analyze_weibull_10years.py
# - plot_weibull_comparison.py
# - gis_visualization.py
```

---

## Proposed Final Structure

### After Cleanup

```
Latam/
│
├── latam_hybrid/              # Framework package
│   ├── Inputdata/             # All data files
│   ├── docs/                  # Framework docs
│   ├── tests/                 # Test suite
│   └── [core, wind, solar, economics, etc.]
│
├── scripts/                   # Utility scripts (6 useful ones)
│   ├── check_leap_years.py
│   ├── check_pvgis_leap_years.py
│   ├── compare_winddata.py
│   ├── analyze_weibull_10years.py
│   ├── plot_weibull_comparison.py
│   └── gis_visualization.py
│
├── legacy/                    # Archived old code
│   ├── old_scripts/           # Old Python scripts
│   ├── old_modules/           # Old module directories
│   ├── old_results/           # Old result files
│   └── old_misc/              # Old images, one-time scripts
│       ├── site_shading_analysis.png
│       ├── turbine_plot.png
│       ├── windrose.png
│       └── pdf_to_markdown.py
│
├── claudedocs/                # Project documentation
│   └── [All project summaries]
│
├── Configuration Files
│   ├── README.md
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── environment.yaml
│   ├── requirements.txt
│   └── .env.example
│
└── Optional (if needed)
    ├── .windsurfrules        # If using Windsurf
    ├── setup_env.bat         # If using Windows helpers
    └── switch_env.bat        # If using Windows helpers
```

---

## Cleanup Script

### Safe Automated Cleanup

```bash
#!/bin/bash
# cleanup.sh - Safe project cleanup

echo "Starting project cleanup..."

# 1. Delete JavaScript files (not needed)
echo "Removing JavaScript files..."
rm -f package.json package-lock.json

# 2. Create legacy/old_misc directory
echo "Creating archive directory..."
mkdir -p legacy/old_misc

# 3. Archive old images
echo "Archiving old result images..."
mv *.png legacy/old_misc/ 2>/dev/null || true

# 4. Archive old documentation from scripts/
echo "Cleaning scripts directory..."
mv scripts/README.md legacy/old_misc/ 2>/dev/null || true
mv scripts/README-task-master.md legacy/old_misc/ 2>/dev/null || true
mv scripts/dev.js legacy/old_misc/ 2>/dev/null || true
mv scripts/example_prd.txt legacy/old_misc/ 2>/dev/null || true
mv scripts/prd.txt legacy/old_misc/ 2>/dev/null || true
mv scripts/task-complexity-report.json legacy/old_misc/ 2>/dev/null || true
mv scripts/pdf_to_markdown.py legacy/old_misc/ 2>/dev/null || true

# 5. Remove old root readme
echo "Removing old root documentation..."
rm -f README-task-master.md

# 6. Create .gitignore if missing
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Jupyter
.ipynb_checkpoints/

# IDE
.cursor/
.vscode/
.idea/

# Environment
.env

# Results (optional)
*.png
*.jpg
*.jpeg
EOF
fi

echo "Cleanup complete!"
echo ""
echo "Summary:"
echo "- Removed JavaScript files"
echo "- Archived old images to legacy/old_misc/"
echo "- Cleaned scripts/ directory"
echo "- Removed old documentation"
echo ""
echo "Directories remaining:"
ls -d */ | grep -v ".git\|.cursor"
```

---

## Decision Points for You

### 1. **Planningarea_shp/ Directory**

**Option A**: Move to Inputdata (if it's input data)
```bash
mv Planningarea_shp/ latam_hybrid/Inputdata/GISdata/
```

**Option B**: Archive (if redundant with files already in Inputdata/GISdata/)
```bash
mv Planningarea_shp/ legacy/old_misc/
```

**Question**: Is this the same as files already in `latam_hybrid/Inputdata/GISdata/`?

### 2. **Windows Batch Files**

- `setup_env.bat`
- `switch_env.bat`

**Question**: Do you use these? Keep if useful, delete if not.

### 3. **.windsurfrules**

**Question**: Are you using Windsurf IDE? Keep if yes, delete if no.

### 4. **scripts/ Directory Purpose**

Current useful scripts:
- Data validation (leap years, compare wind data)
- Statistical analysis (Weibull)
- Visualization (plots, GIS)

**Question**: Keep as standalone `scripts/` or move to `latam_hybrid/utils/`?

---

## Recommended Actions

### Do Now (Safe)

1. ✅ Delete JavaScript files (package.json, package-lock.json)
2. ✅ Archive old images to legacy/old_misc/
3. ✅ Clean scripts/ directory (remove docs/templates)
4. ✅ Delete old root readme (README-task-master.md)
5. ✅ Create/update .gitignore

### Decide (Your Choice)

1. ❓ Planningarea_shp/ - Move or archive?
2. ❓ Windows batch files - Keep or delete?
3. ❓ .windsurfrules - Keep or delete?
4. ❓ scripts/ location - Keep separate or move to latam_hybrid/utils/?

---

## Expected Outcome

### Before Cleanup
- 20+ files in root
- Mixed purposes (config, images, old docs)
- Unclear what's needed

### After Cleanup
- ~10 essential config files in root
- Clear organization:
  - `latam_hybrid/` - Framework
  - `scripts/` - Utilities
  - `legacy/` - Archived
  - `claudedocs/` - Docs
- Professional, maintainable structure

---

## Next Steps

1. Review this analysis
2. Answer decision questions
3. Run cleanup script or manual cleanup
4. Verify everything still works
5. Commit clean structure to git

Would you like me to:
1. Create the cleanup script?
2. Execute specific cleanup actions?
3. Help decide on the question marks?
