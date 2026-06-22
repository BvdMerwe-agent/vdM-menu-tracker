#!/usr/bin/env python3
"""
Menu Tracker - Core module for Floor's kitchen brain.

12-week rotating meal plan, grocery tracking, pantry inventory, waste reduction.
"""
import sqlite3
import json
import random
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

DB_PATH = Path(__file__).parent / "menu.db"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Recipe:
    id: int
    name: str
    type: str
    cuisine: str
    prep_time: int
    cook_time: int
    servings: int
    difficulty: str
    tags: str
    season: str
    notes: str
    ingredients: List[Dict[str, Any]] = None

@dataclass
class ShoppingListItem:
    ingredient_id: Optional[int]
    name: str
    quantity: float
    unit: str
    store_section: str
    week_day: str
    bought: int = 0

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(schema_path: Optional[Path] = None):
    """Initialise schema from SQL file if tables don't exist yet."""
    schema = schema_path or (Path(__file__).parent / "schema.sql")
    if schema.exists():
        conn = sqlite3.connect(str(DB_PATH))
        conn.executescript(schema.read_text())
        conn.commit()
        conn.close()

# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------
def add_recipe(
    name: str,
    type_: str = "dinner",
    cuisine: str = "",
    prep_time: int = 0,
    cook_time: int = 0,
    servings: int = 4,
    difficulty: str = "easy",
    tags: str = "",
    season: str = "",
    notes: str = "",
    source: str = "",
) -> int:
    conn = get_conn()
    cursor = conn.execute(
        """
        INSERT INTO recipes (name, type, cuisine, prep_time, cook_time, servings, difficulty, tags, season, notes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, type_, cuisine, prep_time, cook_time, servings, difficulty, tags, season, notes, source),
    )
    rid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rid

def get_recipe(rid: int) -> Optional[Recipe]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM recipes WHERE id = ?", (rid,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    # Strip DB-only columns not in the Recipe dataclass
    for key in ('calories', 'source', 'active', 'created_at'):
        d.pop(key, None)
    recipe = Recipe(**d)
    recipe.ingredients = [dict(x) for x in conn.execute(
        """
        SELECT ri.*, i.name AS ingredient_name, i.category
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
        """,
        (rid,),
    ).fetchall()]
    conn.close()
    return recipe

def list_recipes(type_: str = None, tags: str = None, active_only: bool = True) -> List[Dict]:
    conn = get_conn()
    sql = "SELECT * FROM recipes WHERE 1=1"
    params = []
    if type_:
        sql += " AND type = ?"
        params.append(type_)
    if active_only:
        sql += " AND active = 1"
    if tags:
        sql += " AND (tags LIKE ? OR tags LIKE ?)"
        params.extend([f"%{tags}%", f"%{tags.title()}%"])
    sql += " ORDER BY name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_recipe(rid: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM recipes WHERE id = ?", (rid,))
    conn.commit()
    conn.close()

def update_recipe(rid: int, **fields) -> None:
    if not fields:
        return
    conn = get_conn()
    cols = [f"{k} = ?" for k in fields]
    conn.execute(f"UPDATE recipes SET {', '.join(cols)} WHERE id = ?", (*fields.values(), rid))
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Ingredients
# ---------------------------------------------------------------------------
def add_ingredient(
    name: str,
    category: str = "",
    default_unit: str = "g",
    shelf_life_days: int = None,
    staple: bool = False,
    store_section: str = "",
) -> int:
    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO ingredients (name, category, default_unit, shelf_life_days, staple, store_section)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name.lower(), category, default_unit, shelf_life_days, 1 if staple else 0, store_section),
        )
        iid = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Already exists — fetch it
        row = conn.execute("SELECT id FROM ingredients WHERE name = ?", (name.lower(),)).fetchone()
        iid = row["id"]
    conn.commit()
    conn.close()
    return iid

def add_recipe_ingredient(recipe_id: int, ingredient_id: int, quantity: float, unit: str = "g", prep_note: str = "", optional: bool = False):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, prep_note, optional) VALUES (?, ?, ?, ?, ?, ?)",
        (recipe_id, ingredient_id, quantity, unit, prep_note, 1 if optional else 0),
    )
    conn.commit()
    conn.close()

def list_ingredients(category: str = None) -> List[Dict]:
    conn = get_conn()
    sql = "SELECT * FROM ingredients"
    params = []
    if category:
        sql += " WHERE category = ?"
        params.append(category)
    sql += " ORDER BY category, name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# Meal Plans (12-week system)
# ---------------------------------------------------------------------------
def create_plan(name: str = "Default 12-week plan", start_date: str = None) -> int:
    """Create a new 12-week meal plan and initialise its weeks."""
    start = start_date or datetime.date.today().isoformat()
    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO meal_plans (name, start_date) VALUES (?, ?)",
        (name, start),
    )
    plan_id = cursor.lastrowid
    for w in range(1, 13):
        conn.execute(
            "INSERT INTO meal_plan_weeks (plan_id, week_number) VALUES (?, ?)",
            (plan_id, w),
        )
    conn.commit()
    conn.close()
    return plan_id

def get_active_plan() -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM meal_plans WHERE active = 1 ORDER BY start_date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_plan_week(plan_id: int, week_number: int) -> Optional[int]:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM meal_plan_weeks WHERE plan_id = ? AND week_number = ?",
        (plan_id, week_number),
    ).fetchone()
    conn.close()
    return row["id"] if row else None

def assign_meal(week_id: int, day_of_week: int, meal_type: str, recipe_id: int, notes: str = "") -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO meal_plan_meals (week_id, day_of_week, meal_type, recipe_id, notes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(week_id, day_of_week, meal_type) DO UPDATE SET
            recipe_id=excluded.recipe_id, notes=excluded.notes, cooked=0, overridden_with=NULL
        """,
        (week_id, day_of_week, meal_type, recipe_id, notes),
    )
    conn.commit()
    conn.close()

def generate_12_week_plan(
    plan_id: int,
    dinner_recipes: List[int],
    lunch_recipes: List[int],
    strategy: str = "rotation",
) -> None:
    """
    Populate a full 12-week plan.
    strategy='rotation':   spread recipes evenly, minimise repeats per month
    strategy='random':     pure random per slot
    """
    conn = get_conn()
    random.seed(42)
    for wn in range(1, 13):
        week_id = get_plan_week(plan_id, wn)
        for dow in range(7):  # 0=Mon ... 6=Sun
            for mt in ("lunch", "dinner"):
                pool = dinner_recipes if mt == "dinner" else lunch_recipes
                if strategy == "rotation":
                    # Pick based on week offset so each slot rotates through pool
                    idx = (wn * 7 + dow + hash(mt)) % len(pool)
                    chosen = pool[idx]
                else:
                    chosen = random.choice(pool)
                assign_meal(week_id, dow, mt, chosen)
    conn.close()

def get_week_menu(plan_id: int, week_number: int) -> Dict[str, Dict]:
    """Return Mon..Sun mapping for a given week."""
    conn = get_conn()
    week_id = get_plan_week(plan_id, week_number)
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    menu = {}
    for dow in range(7):
        day_menu = {"lunch": None, "dinner": None}
        for mt in ("lunch", "dinner"):
            row = conn.execute(
                """
                SELECT mpm.*, r.name AS recipe_name, r.prep_time + r.cook_time AS total_time
                FROM meal_plan_meals mpm
                LEFT JOIN recipes r ON mpm.recipe_id = r.id
                WHERE mpm.week_id = ? AND mpm.day_of_week = ? AND mpm.meal_type = ?
                """,
                (week_id, dow, mt),
            ).fetchone()
            if row:
                day_menu[mt] = dict(row)
        menu[DAYS[dow]] = day_menu
    conn.close()
    return menu

def get_current_week_number(plan_id: int) -> int:
    """Given the plan start_date, which week are we in (1-12, cycling)?"""
    conn = get_conn()
    row = conn.execute("SELECT start_date FROM meal_plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    if not row:
        return 1
    start = datetime.datetime.strptime(row["start_date"], "%Y-%m-%d").date()
    today = datetime.date.today()
    days_since = (today - start).days
    # Cycle through 12 weeks
    return ((days_since // 7) % 12) + 1

def mark_meal_cooked(week_id: int, day_of_week: int, meal_type: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE meal_plan_meals SET cooked = 1 WHERE week_id = ? AND day_of_week = ? AND meal_type = ?",
        (week_id, day_of_week, meal_type),
    )
    conn.commit()
    conn.close()

def swap_meal(week_id: int, day_of_week: int, meal_type: str, new_recipe_id: int) -> None:
    conn = get_conn()
    conn.execute(
        """
        UPDATE meal_plan_meals
        SET overridden_with = ?
        WHERE week_id = ? AND day_of_week = ? AND meal_type = ?
        """,
        (new_recipe_id, week_id, day_of_week, meal_type),
    )
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Pantry
# ---------------------------------------------------------------------------
def add_pantry_item(
    ingredient_id: int,
    quantity: float = 0,
    unit: str = "g",
    expires_on: str = None,
    location: str = "fridge",
    state: str = "fresh",
    notes: str = "",
) -> int:
    conn = get_conn()
    cursor = conn.execute(
        """
        INSERT INTO pantry_items (ingredient_id, quantity, unit, expires_on, location, state, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (ingredient_id, quantity, unit, expires_on, location, state, notes),
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid

def update_pantry_qty(item_id: int, delta: float) -> None:
    conn = get_conn()
    row = conn.execute("SELECT quantity FROM pantry_items WHERE id = ?", (item_id,)).fetchone()
    if row:
        new_qty = max(0, row["quantity"] + delta)
        conn.execute("UPDATE pantry_items SET quantity = ? WHERE id = ?", (new_qty, item_id))
        conn.commit()
    conn.close()

def list_pantry() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT pi.*, i.name AS ingredient_name, i.category
        FROM pantry_items pi
        JOIN ingredients i ON pi.ingredient_id = i.id
        WHERE pi.quantity > 0
        ORDER BY i.category, i.name
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pantry_item(ingredient_id: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM pantry_items WHERE ingredient_id = ? AND quantity > 0 LIMIT 1",
        (ingredient_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def remove_zero_items():
    conn = get_conn()
    conn.execute("DELETE FROM pantry_items WHERE quantity <= 0")
    conn.commit()
    conn.close()

def list_expiring(days: int = 3) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        f"""
        SELECT pi.*, i.name AS ingredient_name, i.category,
               CAST(julianday(expires_on) - julianday('now') AS INT) AS days_left
        FROM pantry_items pi
        JOIN ingredients i ON pi.ingredient_id = i.id
        WHERE pi.expires_on IS NOT NULL
          AND pi.quantity > 0
          AND julianday(expires_on) - julianday('now') <= ?
        ORDER BY days_left ASC
        """,
        (days,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# Shopping Lists
# ---------------------------------------------------------------------------
def generate_shopping_list(week_id: int, plan_id: int = None) -> int:
    """
    Build a shopping list from the plan for the given week,
    subtracting pantry inventory for non-staples.
    """
    conn = get_conn()
    # Get all recipes for this week
    rows = conn.execute(
        """
        SELECT mpm.day_of_week, mpm.meal_type, ri.ingredient_id, ri.quantity, ri.unit,
               i.name AS ingredient_name, i.category, i.staple
        FROM meal_plan_meals mpm
        JOIN recipe_ingredients ri ON mpm.recipe_id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE mpm.week_id = ? AND mpm.cooked = 0
        """,
        (week_id,),
    ).fetchall()

    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Aggregate required quantities per ingredient
    required: Dict[int, Dict] = {}
    for r in rows:
        iid = r["ingredient_id"]
        day_label = f"{DAYS[r['day_of_week']]} {r['meal_type']}"
        if iid not in required:
            required[iid] = {
                "name": r["ingredient_name"],
                "category": r["category"],
                "quantity": 0.0,
                "unit": r["unit"],
                "staple": r["staple"],
                "days": set(),
            }
        required[iid]["quantity"] += r["quantity"]
        required[iid]["days"].add(day_label)

    # Subtract pantry for non-staples
    for iid, info in list(required.items()):
        if info["staple"]:
            continue  # always buy staples (salt, oil, etc.) — or leave them off
        pantry = conn.execute(
            "SELECT quantity, unit FROM pantry_items WHERE ingredient_id = ? AND quantity > 0 LIMIT 1",
            (iid,),
        ).fetchone()
        if pantry:
            # Naive subtraction — assumes same units for now
            info["quantity"] -= pantry["quantity"]
            if info["quantity"] <= 0:
                del required[iid]

    # Insert shopping list
    cursor = conn.execute(
        "INSERT INTO shopping_lists (week_id, status) VALUES (?, ?)",
        (week_id, "draft"),
    )
    list_id = cursor.lastrowid

    for iid, info in required.items():
        conn.execute(
            """
            INSERT INTO shopping_list_items (list_id, ingredient_id, name, quantity, unit, store_section, week_day)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                list_id,
                iid,
                info["name"],
                max(0, info["quantity"]),
                info["unit"],
                info["category"],
                ", ".join(sorted(info["days"]))[:80],  # trim long strings
            ),
        )

    conn.commit()
    conn.close()
    return list_id

def get_shopping_list(list_id: int) -> Tuple[Dict, List[Dict]]:
    conn = get_conn()
    header = conn.execute("SELECT * FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    items = conn.execute(
        "SELECT * FROM shopping_list_items WHERE list_id = ? ORDER BY store_section, name",
        (list_id,),
    ).fetchall()
    conn.close()
    return (dict(header) if header else {}, [dict(i) for i in items])

def mark_bought(item_id: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE shopping_list_items SET bought = 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def mark_shopped(list_id: int) -> None:
    """When shopping is done, move purchased items to pantry."""
    conn = get_conn()
    items = conn.execute(
        "SELECT ingredient_id, name, quantity, unit FROM shopping_list_items WHERE list_id = ? AND bought = 1",
        (list_id,),
    ).fetchall()
    for item in items:
        existing = conn.execute(
            "SELECT id, quantity FROM pantry_items WHERE ingredient_id = ? AND state = 'fresh' ORDER BY id DESC LIMIT 1",
            (item["ingredient_id"],),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE pantry_items SET quantity = quantity + ? WHERE id = ?",
                (item["quantity"], existing["id"]),
            )
        else:
            # Need to look up shelf life
            ing_row = conn.execute(
                "SELECT shelf_life_days FROM ingredients WHERE id = ?", (item["ingredient_id"],)
            ).fetchone()
            expires = None
            if ing_row and ing_row["shelf_life_days"]:
                expires = (datetime.date.today() + datetime.timedelta(days=ing_row["shelf_life_days"])).isoformat()
            conn.execute(
                "INSERT INTO pantry_items (ingredient_id, quantity, unit, expires_on, state) VALUES (?, ?, ?, ?, ?)",
                (item["ingredient_id"], item["quantity"], item["unit"], expires, "fresh"),
            )
    conn.execute("UPDATE shopping_lists SET status = 'shopped' WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Meal History & Waste Log
# ---------------------------------------------------------------------------
def log_meal(date: str, meal_type: str, recipe_id: int = None, custom_name: str = "", servings_eaten: int = 0, rating: int = None, notes: str = "", logged_by: str = "Floor"):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO meal_history (date, meal_type, recipe_id, custom_name, servings_eaten, rating, notes, logged_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (date, meal_type, recipe_id, custom_name, servings_eaten, rating, notes, logged_by),
    )
    conn.commit()
    conn.close()

def log_waste(ingredient_id: int, name: str, quantity: float, unit: str, reason: str = "expired", cost: float = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO waste_log (ingredient_id, name, quantity, unit, reason, estimated_cost_eur) VALUES (?, ?, ?, ?, ?, ?)",
        (ingredient_id, name, quantity, unit, reason, cost),
    )
    conn.commit()
    conn.close()

def waste_stats(days: int = 30) -> Dict:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT reason, COUNT(*) AS count, COALESCE(SUM(estimated_cost_eur), 0) AS cost
        FROM waste_log
        WHERE wasted_on >= date('now', ?)
        GROUP BY reason
        """,
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    return {r["reason"]: {"count": r["count"], "cost": r["cost"]} for r in rows}

# ---------------------------------------------------------------------------
# Pretty-print helpers for Telegram
# ---------------------------------------------------------------------------
def fmt_shopping_list(list_id: int) -> str:
    header, items = get_shopping_list(list_id)
    if not items:
        return "🛒 Shopping list is empty."
    lines = ["📋 *Shopping List*", ""]
    sections: Dict[str, List[str]] = {}
    for item in items:
        sec = item.get("store_section") or "Other"
        check = "☑️" if item["bought"] else "⬜"
        qty = f"{item['quantity']:.0f}" if item["quantity"] == int(item["quantity"]) else f"{item['quantity']:.1f}"
        line = f"{check} {qty} {item['unit']} {item['name']}"
        if item.get("week_day"):
            line += f" _(for {item['week_day']})_"
        sections.setdefault(sec, []).append(line)
    for sec in sorted(sections.keys(), key=lambda s: (s == "Other", s)):
        lines.append(f"*{sec}:*")
        lines.extend(sections[sec])
        lines.append("")
    return "\n".join(lines)

def fmt_week_menu(week_number: int, plan_id: int = None) -> str:
    plan_id = plan_id or (get_active_plan() or {}).get("id")
    if not plan_id:
        return "❌ No active meal plan."
    menu = get_week_menu(plan_id, week_number)
    lines = [f"📆 *Week {week_number} — Menu*", ""]
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day in DAYS:
        dm = menu.get(day, {})
        lunch = dm.get("lunch")
        dinner = dm.get("dinner")
        lines.append(f"*{day}:*")
        if lunch:
            name = lunch.get("recipe_name", "?")
            time = lunch.get("total_time", "")
            cooked = " ✅" if lunch.get("cooked") else ""
            lines.append(f"  🥪 {name}{cooked}" + (f" ({time}m)" if time else ""))
        else:
            lines.append("  🥪 —")
        if dinner:
            name = dinner.get("recipe_name", "?")
            time = dinner.get("total_time", "")
            cooked = " ✅" if dinner.get("cooked") else ""
            lines.append(f"  🍽 {name}{cooked}" + (f" ({time}m)" if time else ""))
        else:
            lines.append("  🍽 —")
        lines.append("")
    return "\n".join(lines)

def fmt_pantry_summary() -> str:
    items = list_pantry()
    if not items:
        return "🫙 Pantry is empty."
    by_location: Dict[str, List[str]] = {}
    for item in items:
        loc = item.get("location", "?")
        qty = f"{item['quantity']:.0f}" if item["quantity"] == int(item["quantity"]) else f"{item['quantity']:.1f}"
        line = f"• {qty} {item['unit']} {item['ingredient_name']}"
        if item.get("expires_on"):
            days = (datetime.datetime.strptime(item["expires_on"], "%Y-%m-%d").date() - datetime.date.today()).days
            if days <= 2:
                line += f" ⚠️ {days}d"
            else:
                line += f" ({days}d)"
        by_location.setdefault(loc, []).append(line)
    lines = ["🫙 *Pantry*", ""]
    for loc in sorted(by_location.keys()):
        lines.append(f"*{loc.capitalize()}:*")
        lines.extend(by_location[loc])
        lines.append("")
    return "\n".join(lines)

def fmt_expiring() -> str:
    items = list_expiring(3)
    if not items:
        return "✅ Nothing expiring in the next 3 days."
    lines = ["⚠️ *Expiring Soon:*", ""]
    for item in items:
        qty = f"{item['quantity']:.0f}" if item["quantity"] == int(item["quantity"]) else f"{item['quantity']:.1f}"
        days = item.get("days_left", "?")
        lines.append(f"• {qty} {item['unit']} {item['ingredient_name']} — {days} day{'s' if days != 1 else ''} left")
    return "\n".join(lines)

# =============================================================================
# CURATED WEEKLY MEALS (interactive, user-driven Sunday curation)
# =============================================================================

def _monday_of(date: datetime.date = None) -> datetime.date:
    """Return the Monday of the week containing `date` (defaults to today)."""
    if date is None:
        date = datetime.date.today()
    return date - datetime.timedelta(days=date.weekday())  # Monday=0

def start_curated_week(week_start: str = None) -> int:
    """Create a new curated week that starts collecting meals. Returns the week_id."""
    if week_start is None:
        week_start = _monday_of(datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO curated_weeks (week_start, status) VALUES (?, 'collecting')",
        (week_start,)
    )
    week_id = cur.lastrowid
    conn.commit()
    conn.close()
    return week_id

def get_collecting_week() -> Optional[Dict]:
    """Find the currently collecting curated week."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM curated_weeks WHERE status = 'collecting' ORDER BY week_start DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def add_meal_to_collection(recipe_id: int, meal_type: str, added_by: str = "user") -> Dict:
    """Add a recipe to the current collecting week. Returns status."""
    cw = get_collecting_week()
    if not cw:
        # Auto-start one if none exists
        week_id = start_curated_week()
        cw = get_collecting_week()
    week_id = cw["id"]
    conn = get_conn()
    
    # Count how many of this type already
    count = conn.execute(
        "SELECT COUNT(*) as c FROM curated_week_meals WHERE week_id = ? AND meal_type = ?",
        (week_id, meal_type)
    ).fetchone()["c"]
    
    max_per_type = {"lunch": 7, "dinner": 7}
    if count >= max_per_type.get(meal_type, 7):
        conn.close()
        return {"success": False, "error": f"Already have 7 {meal_type} meals. Remove one first."}
    
    # Get next slot_index for this type
    slot = count if meal_type == "lunch" else count + 7
    
    conn.execute(
        """INSERT INTO curated_week_meals (week_id, slot_index, meal_type, recipe_id, added_by)
           VALUES (?, ?, ?, ?, ?)""",
        (week_id, slot, meal_type, recipe_id, added_by)
    )
    
    # Check if we hit 14 total
    total = conn.execute(
        "SELECT COUNT(*) as c FROM curated_week_meals WHERE week_id = ?",
        (week_id,)
    ).fetchone()["c"]
    
    status_msg = f"Added. {total}/14 meals collected."
    if total >= 14:
        conn.execute(
            "UPDATE curated_weeks SET status = 'ready' WHERE id = ?",
            (week_id,)
        )
        status_msg = f"✅ Pool full! {total}/14 meals collected. Ready to shuffle."
    
    conn.commit()
    conn.close()
    return {"success": True, "week_id": week_id, "slot": slot, "total": total, "message": status_msg}

def remove_meal_from_collection(slot_index: int, week_id: int = None) -> Dict:
    """Remove a meal by slot index from the collecting pool."""
    cw = get_collecting_week() if week_id is None else None
    if week_id is None:
        if not cw:
            return {"success": False, "error": "No collecting week found."}
        week_id = cw["id"]
    conn = get_conn()
    conn.execute(
        "DELETE FROM curated_week_meals WHERE week_id = ? AND slot_index = ?",
        (week_id, slot_index)
    )
    # Re-number slots within each type
    lunches = conn.execute(
        "SELECT id FROM curated_week_meals WHERE week_id = ? AND meal_type = 'lunch' ORDER BY slot_index",
        (week_id,)
    ).fetchall()
    for i, row in enumerate(lunches):
        conn.execute("UPDATE curated_week_meals SET slot_index = ? WHERE id = ?", (i, row["id"]))
    dinners = conn.execute(
        "SELECT id FROM curated_week_meals WHERE week_id = ? AND meal_type = 'dinner' ORDER BY slot_index",
        (week_id,)
    ).fetchall()
    for i, row in enumerate(dinners):
        conn.execute("UPDATE curated_week_meals SET slot_index = ? WHERE id = ?", (i + 7, row["id"]))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Meal removed."}

def get_curated_pool(week_id: int = None) -> List[Dict]:
    """Return all meals in the collecting pool for a week."""
    conn = get_conn()
    if week_id is None:
        cw = get_collecting_week()
        if not cw:
            conn.close()
            return []
        week_id = cw["id"]
    rows = conn.execute("""
        SELECT cwm.slot_index, cwm.meal_type, cwm.recipe_id, r.name as recipe_name,
               r.cuisine, r.tags, cwm.added_by
        FROM curated_week_meals cwm
        LEFT JOIN recipes r ON cwm.recipe_id = r.id
        WHERE cwm.week_id = ?
        ORDER BY cwm.meal_type, cwm.slot_index
    """, (week_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def shuffle_and_schedule(week_id: int = None, strategy: str = "random") -> Dict:
    """Randomly assign the 14 collected meals to the 7 days × 2 meals.
       strategy: 'random' or 'balanced' (tries to vary cuisines)."""
    conn = get_conn()
    if week_id is None:
        # Try collecting first, then ready
        cw = get_collecting_week()
        if not cw:
            row = conn.execute(
                "SELECT id FROM curated_weeks WHERE status = 'ready' ORDER BY week_start DESC LIMIT 1"
            ).fetchone()
            if not row:
                conn.close()
                return {"success": False, "error": "No week ready to shuffle."}
            week_id = row["id"]
        else:
            week_id = cw["id"]
    
    pool = conn.execute("""
        SELECT id, recipe_id, meal_type FROM curated_week_meals
        WHERE week_id = ?
        ORDER BY meal_type, RANDOM()
    """, (week_id,)).fetchall()
    
    if len(pool) < 14:
        conn.close()
        return {"success": False, "error": f"Only {len(pool)}/14 meals collected. Need all 14 to shuffle."}
    
    # Assign to days: slot 0-6 are lunches (Mon-Sun), 7-13 are dinners (Mon-Sun)
    lunches = [p for p in pool if p["meal_type"] == "lunch"]
    dinners = [p for p in pool if p["meal_type"] == "dinner"]
    
    for day in range(7):
        # Schedule lunch
        lunch = lunches[day] if day < len(lunches) else None
        if lunch:
            conn.execute("""
                UPDATE curated_week_meals
                SET scheduled_day = ?, scheduled_meal_type = 'lunch'
                WHERE id = ?
            """, (day, lunch["id"]))
        # Schedule dinner
        dinner = dinners[day] if day < len(dinners) else None
        if dinner:
            conn.execute("""
                UPDATE curated_week_meals
                SET scheduled_day = ?, scheduled_meal_type = 'dinner'
                WHERE id = ?
            """, (day, dinner["id"]))
    
    conn.execute("UPDATE curated_weeks SET status = 'active', finalized_at = datetime('now') WHERE id = ?", (week_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Shuffled! 14 meals scheduled for the week."}

def get_curated_schedule(week_id: int = None) -> List[Dict]:
    """Return the active week's day-by-day schedule."""
    conn = get_conn()
    if week_id is None:
        row = conn.execute(
            "SELECT id FROM curated_weeks WHERE status = 'active' ORDER BY week_start DESC LIMIT 1"
        ).fetchone()
        if not row:
            conn.close()
            return []
        week_id = row["id"]
    rows = conn.execute("""
        SELECT 
            cw.id as week_id, cw.week_start, cw.status,
            cwm.scheduled_day,
            CASE cwm.scheduled_day
                WHEN 0 THEN 'Mon' WHEN 1 THEN 'Tue' WHEN 2 THEN 'Wed'
                WHEN 3 THEN 'Thu' WHEN 4 THEN 'Fri' WHEN 5 THEN 'Sat' WHEN 6 THEN 'Sun'
            END as day_name,
            cwm.scheduled_meal_type as meal_type,
            r.id as recipe_id, r.name as recipe_name,
            r.cuisine, r.prep_time, r.cook_time,
            cwm.cooked, cwm.skipped
        FROM curated_weeks cw
        JOIN curated_week_meals cwm ON cw.id = cwm.week_id
        LEFT JOIN recipes r ON cwm.recipe_id = r.id
        WHERE cw.id = ? AND cwm.scheduled_day IS NOT NULL
        ORDER BY cwm.scheduled_day,
                 CASE cwm.scheduled_meal_type WHEN 'lunch' THEN 0 ELSE 1 END
    """, (week_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fmt_curated_pool() -> str:
    """Telegram-formatted pool status."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM curated_weeks WHERE status IN ('collecting', 'ready') ORDER BY week_start DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return "📭 No active meal collection. Start one with `/collect` or say 'Start collecting meals'."
    
    cw = dict(row)
    pool = get_curated_pool(cw["id"])
    lines = [f"📦 *Collecting Week Starting {cw['week_start']}*", f"\n{len(pool)}/14 meals in the pool.\n"]
    lunches = [p for p in pool if p["meal_type"] == "lunch"]
    dinners = [p for p in pool if p["meal_type"] == "dinner"]
    
    lines.append("*🥪 Lunches:*")
    for i, m in enumerate(lunches, 1):
        name = m["recipe_name"] or "TBD"
        lines.append(f"  {i}. {name}")
    lines.append(f"  _(need {7 - len(lunches)} more)_")
    
    lines.append("\n*🍽 Dinners:*")
    for i, m in enumerate(dinners, 1):
        name = m["recipe_name"] or "TBD"
        lines.append(f"  {i}. {name}")
    lines.append(f"  _(need {7 - len(dinners)} more)_")
    
    if len(pool) >= 14:
        lines.append("\n✅ *Pool full! Say 'shuffle' to assign meals to days.*")
    
    return "\n".join(lines)

def fmt_curated_schedule() -> str:
    """Telegram-formatted active schedule."""
    schedule = get_curated_schedule()
    if not schedule:
        return "📭 No active schedule. Collect 14 meals and shuffle first."
    lines = [f"📅 *Week of {schedule[0]['week_start']}*", ""]
    DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for day_num in range(7):
        day_meals = [m for m in schedule if m["scheduled_day"] == day_num]
        if not day_meals:
            continue
        day_label = DAYS[day_num]
        lines.append(f"*{day_label}*")
        for m in day_meals:
            icon = "🥪" if m["meal_type"] == "lunch" else "🍽"
            status = "✅" if m["cooked"] else ""
            name = m["recipe_name"] or "TBD"
            lines.append(f"  {icon} {name} {status}")
        lines.append("")
    return "\n".join(lines)

def advance_week() -> Dict:
    """Close current week and start a new one. Called by cron or user."""
    conn = get_conn()
    # Archive old active weeks
    conn.execute(
        "UPDATE curated_weeks SET status = 'past' WHERE status = 'active'"
    )
    # Close collecting weeks too
    conn.execute(
        "UPDATE curated_weeks SET status = 'ready' WHERE status = 'collecting' AND id NOT IN (SELECT MAX(id) FROM curated_weeks)"
    )
    conn.commit()
    conn.close()
    
    # Start new collection for next week
    next_monday = _monday_of(datetime.date.today() + datetime.timedelta(days=7))
    week_id = start_curated_week(next_monday.isoformat())
    return {"success": True, "week_id": week_id, "week_start": next_monday.isoformat(), "message": f"New week collection started: {next_monday.isoformat()}"}

def list_all_recipes_for_selection(meal_type: str = None, tag_filter: str = None) -> List[Dict]:
    """Return recipes suitable for showing to the user during collection."""
    conn = get_conn()
    sql = "SELECT id, name, type, cuisine, tags, prep_time, cook_time FROM recipes WHERE active = 1"
    params = []
    if meal_type:
        sql += " AND type = ?"
        params.append(meal_type)
    if tag_filter:
        sql += " AND tags LIKE ?"
        params.append(f"%{tag_filter}%")
    sql += " ORDER BY type, name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# CLI convenience (extended)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Menu Tracker CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_plan = sub.add_parser("plan", help="Show week menu")
    p_plan.add_argument("--week", type=int, default=get_current_week_number((get_active_plan() or {}).get("id", 1)), help="Week 1-12")

    p_shop = sub.add_parser("shop", help="Generate or show shopping list")
    p_shop.add_argument("--week", type=int, help="Week number")
    p_shop.add_argument("--mark-shopped", type=int, help="Mark list as shopped")

    p_pantry = sub.add_parser("pantry", help="Show pantry")
    p_expiring = sub.add_parser("expiring", help="Show expiring items")

    args = parser.parse_args()

    if args.cmd == "plan":
        plan = get_active_plan()
        if not plan:
            print("No active plan.")
        else:
            print(fmt_week_menu(args.week, plan["id"]))
    elif args.cmd == "shop":
        if args.mark_shopped:
            mark_shopped(args.mark_shopped)
            print("Marked as shopped and moved to pantry.")
        else:
            plan = get_active_plan()
            week_num = args.week or get_current_week_number(plan["id"])
            week_id = get_plan_week(plan["id"], week_num)
            lid = generate_shopping_list(week_id)
            print(fmt_shopping_list(lid))
    elif args.cmd == "pantry":
        print(fmt_pantry_summary())
    elif args.cmd == "expiring":
        print(fmt_expiring())
    else:
        parser.print_help()
