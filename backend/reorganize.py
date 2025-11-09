"""
Backend Reorganization Script
Executes complete folder restructuring with import updates
"""

import os
import shutil
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent

print("=" * 80)
print("BACKEND REORGANIZATION - BIGBANG MODE")
print("=" * 80)

# Step 1: Create new structure (already done)
print("\n[1/10] OK - New structure created")

# Step 2: Move backtesting/csv_logger to backtesting/reporting/
print("\n[2/10] Moving CSV logger to reporting...")
os.makedirs(BASE_DIR / "backtesting" / "reporting", exist_ok=True)
if (BASE_DIR / "backtesting" / "csv_logger.py").exists():
    shutil.move(
        BASE_DIR / "backtesting" / "csv_logger.py",
        BASE_DIR / "backtesting" / "reporting" / "csv_logger.py"
    )
print("  OK - CSV logger moved")

# Step 3: Remove old folders
print("\n[3/10] Removing old folder structure...")
folders_to_remove = [
    "analysis",
    "strategies",
    "config",
    "data/portfolio"
]

for folder in folders_to_remove:
    folder_path = BASE_DIR / folder
    if folder_path.exists():
        shutil.rmtree(folder_path)
        print(f"  OK - Removed {folder}")

# Step 4: Move models and output to runtime
print("\n[4/10] Moving runtime artifacts...")
if (BASE_DIR / "models").exists():
    shutil.move(BASE_DIR / "models", BASE_DIR / "runtime" / "models")
    print("  OK - Moved models/ to runtime/models/")

if (BASE_DIR / "output").exists():
    shutil.move(BASE_DIR / "output", BASE_DIR / "runtime" / "output")
    print("  OK - Moved output/ to runtime/output/")

if (BASE_DIR / "data_cache").exists():
    shutil.move(BASE_DIR / "data_cache", BASE_DIR / "runtime" / "cache")
    print("  OK - Moved data_cache/ to runtime/cache/")

# Step 5: Update imports in all Python files
print("\n[5/10] Updating imports...")

IMPORT_MAPPINGS = {
    "from analysis.indicators": "from domain.indicators",
    "from analysis.patterns": "from domain.patterns",
    "from analysis.models.features": "from domain.ml.features",
    "from analysis.models.predictors": "from domain.ml.predictors",
    "from analysis.models": "from domain.ml",
    "from strategies.implementations": "from domain.strategies.implementations",
    "from strategies.base": "from domain.strategies.base",
    "from strategies.portfolio": "from domain.strategies.portfolio",
    "from strategies import": "from domain.strategies import",
    "from config.settings": "from infrastructure.config.settings",
    "from config import": "from infrastructure.config import",
    "from data.portfolio": "from backtesting.portfolio",
    "from backtesting.csv_logger": "from backtesting.reporting.csv_logger",
    "import analysis.indicators": "import domain.indicators",
    "import analysis.patterns": "import domain.patterns",
    "import strategies": "import domain.strategies",
    "import config": "import infrastructure.config",
}

def update_imports_in_file(file_path):
    """Update imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"    Error updating {file_path}: {e}")
    return False

# Find all Python files
python_files = list(BASE_DIR.rglob("*.py"))
updated_count = 0

for py_file in python_files:
    # Skip this script and __pycache__
    if "reorganize.py" in str(py_file) or "__pycache__" in str(py_file):
        continue

    if update_imports_in_file(py_file):
        updated_count += 1

print(f"  OK - Updated imports in {updated_count} files")

# Step 6: Update path references (models, cache, output)
print("\n[6/10] Updating path references...")

PATH_MAPPINGS = {
    r"models_dir = Path\(__file__\)\.parent\.parent\.parent / 'models'":
        r"models_dir = Path(__file__).parent.parent.parent / 'runtime' / 'models'",
    r"output_dir = Path\(__file__\)\.parent\.parent\.parent / 'output'":
        r"output_dir = Path(__file__).parent.parent.parent / 'runtime' / 'output'",
    r"backend/models": "backend/runtime/models",
    r"backend/output": "backend/runtime/output",
    r"backend/data_cache": "backend/runtime/cache",
    r"Path\('data_cache'\)": "Path('runtime/cache')",
    r"Path\('models'\)": "Path('runtime/models')",
    r"Path\('output'\)": "Path('runtime/output')",
}

path_updated_count = 0
for py_file in python_files:
    if "reorganize.py" in str(py_file) or "__pycache__" in str(py_file):
        continue

    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for old_path, new_path in PATH_MAPPINGS.items():
            content = re.sub(old_path, new_path, content)

        if content != original_content:
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)
            path_updated_count += 1
    except Exception as e:
        pass

print(f"  OK - Updated paths in {path_updated_count} files")

# Step 7: Create __init__.py for new backtesting/portfolio and reporting
print("\n[7/10] Creating missing __init__.py files...")
init_files = [
    "backtesting/portfolio/__init__.py",
    "backtesting/reporting/__init__.py",
    "backtesting/analysis/__init__.py",
    "runtime/__init__.py",
]

for init_file in init_files:
    init_path = BASE_DIR / init_file
    if not init_path.exists():
        init_path.touch()
        print(f"  OK - Created {init_file}")

# Step 8: Update gitignore
print("\n[8/10] Updating .gitignore...")
gitignore_path = BASE_DIR.parent / ".gitignore"
gitignore_additions = [
    "\n# Runtime artifacts",
    "backend/runtime/models/",
    "backend/runtime/cache/",
    "backend/runtime/output/",
]

try:
    with open(gitignore_path, 'a', encoding='utf-8') as f:
        f.write("\n".join(gitignore_additions))
    print("  OK - Updated .gitignore")
except:
    print("  WARNING - Could not update .gitignore")

# Step 9: Summary
print("\n[9/10] Reorganization Summary:")
print(f"  - Removed old folders: {len(folders_to_remove)}")
print(f"  - Updated imports in: {updated_count} files")
print(f"  - Updated paths in: {path_updated_count} files")
print("  - New structure:")
print("    - domain/ (business logic)")
print("    - core/ (models, exceptions)")
print("    - infrastructure/ (config, logging)")
print("    - runtime/ (models, cache, output)")

print("\n[10/10] OK - Reorganization complete!")
print("\n" + "=" * 80)
print("NEXT STEPS:")
print("1. Review changes with 'git status'")
print("2. Test the API: python -m uvicorn api.main:app --reload")
print("3. Run tests: pytest tests/")
print("4. If everything works, commit changes")
print("=" * 80)
