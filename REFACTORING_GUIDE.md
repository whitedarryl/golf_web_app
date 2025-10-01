# Refactoring Guide - Golf Tournament App

This document tracks ongoing refactoring efforts to improve code quality, maintainability, and reliability.

## ✅ Completed

### 1. Standardize course_id Usage
**Status**: ✅ Complete
**Date**: 2025-10-01

**Changes Made**:
- Created `utils/course_manager.py` for centralized course ID management
- Updated `convert_and_import_all_simplified.py` to use `get_latest_course_id()`
- Updated `import_handicap_ranks.py` to use `get_latest_course_id()`

**Impact**: Eliminates hardcoded `course_id=1` vs `course_id=2` conflicts that caused duplicate results.

---

## 🔄 In Progress

### 2. Consolidate Database Connection Management
**Status**: 🔄 In Progress (10% complete)
**Priority**: High

**Goal**: Replace all manual connection management with context managers for automatic cleanup.

**Pattern to Replace**:
```python
# ❌ OLD (Error-prone)
conn = mysql_connection()
cursor = conn.cursor()
try:
    cursor.execute("SELECT * FROM players")
    # ... do stuff
finally:
    cursor.close()
    conn.close()
```

**Replace With**:
```python
# ✅ NEW (Safe)
from utils.db import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    # ... do stuff
    # Auto-closes even on exception
```

**Files Needing Updates** (16 total):
- [x] `app1_golf_score_calculator/routes.py` - `admin_add_player()` (DONE)
- [ ] `app1_golf_score_calculator/routes.py` - 8 more functions
- [ ] `app1_golf_score_calculator/app.py`
- [ ] `app2_golf_script_runner/import_handicap_ranks.py`
- [ ] `app2_golf_script_runner/convert_and_import_all_simplified.py`
- [ ] `app2_golf_script_runner/import_golf_scores.py`
- [ ] `app2_golf_script_runner/archive_scores_snapshot.py`
- [ ] `app2_golf_script_runner/import_archive_scores.py`
- [ ] `app4_five_results/app.py`
- [ ] `app5_historical_data/app.py`
- [ ] `callaway_results_app/app.py`
- [ ] `bulk_import_archive_scores.py`

**Estimated Time**: 3-4 hours to complete all files

---

## 📋 Planned

### 3. Standardize Excel File Discovery
**Priority**: Medium

**Problem**: Each app searches for Excel files differently:
- Some look for `*Callaway scoring sheet.xlsx`
- Some look for `*.xls` (wrong extension!)
- All scan filesystem repeatedly (slow)

**Solution**: Create `utils/excel_manager.py`:
```python
def get_current_excel_file() -> str:
    """
    Get the path to the current tournament Excel file.

    Priority:
    1. EXCEL_FILE_PATH environment variable
    2. Most recent *Callaway scoring sheet.xlsx in project root
    3. Cached value from previous lookup
    """
    pass
```

**Files to Update**:
- `app1_golf_score_calculator/excel_cache.py`
- `app2_golf_script_runner/convert_xlsx_to_csv.py`
- `callaway_results_app/utils.py`
- All apps using file discovery

---

### 4. Add Input Validation
**Priority**: High (Security)

**Problem**: No validation on user inputs like golf scores, player names, etc.

**Examples**:
```python
# Current: No validation
holes = [int(request.form.get(f"hole_{i}", 0)) for i in range(1, 19)]

# Improved: Validate scores
def validate_golf_score(score: int, hole_num: int) -> int:
    if not isinstance(score, int):
        raise ValueError(f"Score must be an integer")
    if not (1 <= score <= 15):
        raise ValueError(f"Invalid score {score} for hole {hole_num}")
    return score

holes = [validate_golf_score(int(request.form.get(f"hole_{i}", 0)), i)
         for i in range(1, 19)]
```

**Files to Update**:
- `app1_golf_score_calculator/routes.py` - `submit()` function
- `app1_golf_score_calculator/routes.py` - `admin_add_player()`
- `app1_golf_score_calculator/routes.py` - `admin_remove_player()`

---

### 5. Replace Print Statements with Logging
**Priority**: Medium

**Problem**: 200+ `print()` statements for debugging. Should use proper logging.

**Pattern**:
```python
# ❌ OLD
print("🔍 INDEX ROUTE - counts:", counts)

# ✅ NEW
import logging
logger = logging.getLogger(__name__)
logger.debug("🔍 INDEX ROUTE - counts: %s", counts)
```

**Configuration** (in `.env`):
```env
LOG_LEVEL=INFO  # Production: only errors/warnings/info
LOG_LEVEL=DEBUG # Development: everything
```

**Benefits**:
- Control verbosity via config
- Automatic timestamps
- Can log to file for debugging tournaments
- Doesn't clutter production output

---

### 6. Consolidate Flask Apps
**Priority**: Low (Optional)

**Current**: 6 separate Flask apps glued with `DispatcherMiddleware`
**Question**: Is this intentional or did it evolve organically?

**Option A - Keep As-Is**:
- Pro: Modular, can deploy separately
- Con: Complex routing, separate sessions, no shared state

**Option B - Single App with Blueprints**:
```python
app = Flask(__name__)
app.register_blueprint(score_calculator_bp, url_prefix='/golf_score_calculator')
app.register_blueprint(five_results_bp, url_prefix='/five_results')
app.register_blueprint(callaway_bp, url_prefix='/callaway_results')
```

**Benefits of Option B**:
- Shared session/auth
- Single database pool
- Simpler configuration
- Easier debugging

**Decision**: Discuss with team before implementing

---

### 7. Add Player ID System
**Priority**: Low (Major refactoring)

**Problem**: Player identification uses name matching (fragile):
- "DJ Patterson" vs "D J Patterson"
- "Steve Cook" vs "Steve Cook Jr"
- Complex canonicalization logic

**Solution**: Use `player_id` as primary key:
```sql
-- Add to schema
ALTER TABLE players ADD COLUMN player_id INT AUTO_INCREMENT PRIMARY KEY;
ALTER TABLE scores ADD COLUMN player_id INT;
ALTER TABLE fives ADD COLUMN player_id INT;

-- Add foreign keys
ALTER TABLE scores ADD FOREIGN KEY (player_id) REFERENCES players(player_id);
```

**Benefits**:
- No name-matching bugs
- Faster JOINs (int vs string)
- Supports name changes
- Cleaner code

**Risk**: Requires data migration for existing tournaments

---

### 8. Better Error Messages
**Priority**: Medium

**Current**:
```python
except Exception as e:
    return jsonify(success=False, error=str(e)), 500
```

**Improved**:
```python
except mysql.connector.IntegrityError as e:
    logger.error("Player already exists: %s", e)
    return jsonify(success=False, message="Player already exists"), 409
except mysql.connector.OperationalError as e:
    logger.error("Database connection failed: %s", e)
    return jsonify(success=False, message="Database unavailable, try again"), 503
except ValueError as e:
    logger.warning("Invalid input: %s", e)
    return jsonify(success=False, message=str(e)), 400
except Exception as e:
    logger.exception("Unexpected error")
    return jsonify(success=False, message="An error occurred"), 500
```

---

### 9. Move Inline JavaScript to Files
**Priority**: Low

**Files**:
- `app1_golf_score_calculator/templates/index.html` - ~100 lines of inline JS

**Already Done**: Most JS is in separate files
**Remaining**: Move last inline scripts to `.js` files

---

### 10. Add Unit Tests
**Priority**: Medium

**Current**: No automated tests

**Suggested Framework**: `pytest`

**Example**:
```python
# tests/test_course_manager.py
def test_get_current_course_id():
    course_id = get_current_course_id()
    assert isinstance(course_id, int)
    assert course_id >= 1

def test_validate_golf_score():
    assert validate_golf_score(4, 1) == 4
    with pytest.raises(ValueError):
        validate_golf_score(99, 1)
```

---

## 🎯 Priority Order

**Do These First** (Bugs/Security):
1. ✅ #1 - Standardize course_id (DONE)
2. 🔄 #2 - Database connection management (IN PROGRESS)
3. #4 - Input validation
4. #8 - Better error handling

**Do These Next** (Performance/Maintainability):
5. #3 - Excel file discovery
6. #5 - Replace prints with logging

**Consider Later** (Architecture):
7. #6 - Consolidate Flask apps (discuss first)
8. #7 - Player ID system (major change)
9. #9 - Move inline JS
10. #10 - Add tests

---

## 📊 Progress Tracking

| Task | Priority | Status | Progress | Est. Time |
|------|----------|--------|----------|-----------|
| 1. course_id standardization | High | ✅ Done | 100% | - |
| 2. DB connection management | High | 🔄 In Progress | 10% | 3-4h |
| 3. Excel file discovery | Medium | 📋 Planned | 0% | 2h |
| 4. Input validation | High | 📋 Planned | 0% | 2h |
| 5. Logging | Medium | 📋 Planned | 0% | 2h |
| 6. Consolidate apps | Low | 📋 Planned | 0% | 8h |
| 7. Player ID system | Low | 📋 Planned | 0% | 16h |
| 8. Error handling | Medium | 📋 Planned | 0% | 2h |
| 9. Move inline JS | Low | 📋 Planned | 0% | 1h |
| 10. Unit tests | Medium | 📋 Planned | 0% | 8h |

---

## 🛠️ How to Continue

### Quick Wins (Do These First):
```bash
# 1. Finish database connection refactoring
# Replace mysql_connection() in routes.py (8 more functions)
# Estimated: 2 hours

# 2. Add input validation
# Add validate_golf_score() and use it in submit()
# Estimated: 30 minutes

# 3. Replace debug prints with logging
# Update routes.py and app.py to use logger
# Estimated: 1 hour
```

### Testing After Changes:
1. Run Docker: `start.bat`
2. Test score submission
3. Test add/remove player
4. Run tournament scripts
5. Check for any errors

---

**Last Updated**: 2025-10-01
**Next Review**: After completing #2 (DB connections)
