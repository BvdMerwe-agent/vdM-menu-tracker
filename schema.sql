-- Menu & Grocery Tracker Schema
-- SQLite - designed for Floor's 12-week rotating meal plan

PRAGMA foreign_keys = ON;

-- ============================================================
-- RECIPES
-- ============================================================
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('dinner','lunch','breakfast','snack')) DEFAULT 'dinner',
    cuisine TEXT DEFAULT '',
    prep_time INTEGER DEFAULT 0,  -- minutes
    cook_time INTEGER DEFAULT 0,  -- minutes
    servings INTEGER DEFAULT 4,
    difficulty TEXT CHECK(difficulty IN ('easy','medium','hard')) DEFAULT 'easy',
    calories INTEGER DEFAULT NULL,
    tags TEXT DEFAULT '',         -- comma-separated: "vegetarian,spicy,one-pot"
    season TEXT DEFAULT '',        -- "summer,winter" or empty for year-round
    notes TEXT DEFAULT '',
    source TEXT DEFAULT '',        -- URL or cookbook name
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1       -- 0 = archived
);

-- ============================================================
-- INGREDIENTS (canonical list)
-- ============================================================
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT '',      -- produce,dairy,meat,pantry,frozen,bakery
    default_unit TEXT DEFAULT 'g',
    shelf_life_days INTEGER DEFAULT NULL,  -- how many days it typically lasts
    staple INTEGER DEFAULT 0,      -- 1 = always keep in stock (salt, oil, etc.)
    store_section TEXT DEFAULT '', -- supermarket aisle grouping
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- RECIPE ↔ INGREDIENT linkage
-- ============================================================
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity REAL DEFAULT 1,
    unit TEXT DEFAULT 'g',
    prep_note TEXT DEFAULT '',     -- "finely chopped", "if available"
    optional INTEGER DEFAULT 0,
    UNIQUE(recipe_id, ingredient_id)
);

-- ============================================================
-- 12-WEEK MEAL PLAN
-- ============================================================
CREATE TABLE IF NOT EXISTS meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT 'Default 12-week plan',
    start_date DATE DEFAULT CURRENT_DATE,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS meal_plan_weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,   -- 1-12
    UNIQUE(plan_id, week_number)
);

CREATE TABLE IF NOT EXISTS meal_plan_meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL REFERENCES meal_plan_weeks(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6), -- 0=Mon, 6=Sun
    meal_type TEXT CHECK(meal_type IN ('lunch','dinner')) NOT NULL,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
    cooked INTEGER DEFAULT 0,       -- 0=planned, 1=actually made
    skipped INTEGER DEFAULT 0,    -- 0=no, 1=yes (logged as skipped)
    overridden_with INTEGER DEFAULT NULL REFERENCES recipes(id),  -- if swapped
    notes TEXT DEFAULT '',
    UNIQUE(week_id, day_of_week, meal_type)
);

-- ============================================================
-- PANTRY / FRIDGE INVENTORY
-- ============================================================
CREATE TABLE IF NOT EXISTS pantry_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    quantity REAL DEFAULT 0,
    unit TEXT DEFAULT 'g',
    expires_on DATE DEFAULT NULL,
    bought_on DATE DEFAULT CURRENT_DATE,
    location TEXT DEFAULT 'fridge', -- fridge, freezer, pantry, cellar
    state TEXT DEFAULT 'fresh',     -- fresh, frozen, leftover, opened
    opened_on DATE DEFAULT NULL,
    notes TEXT DEFAULT '',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- WEEKLY SHOPPING LISTS (auto-generated from plan + pantry delta)
-- ============================================================
CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER REFERENCES meal_plan_weeks(id),
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'draft',    -- draft, sent, shopped, archived
    delivery_target TEXT DEFAULT '',-- e.g. Telegram chat ID
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS shopping_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(id),
    name TEXT NOT NULL,             -- denormalized for display
    quantity REAL DEFAULT 1,
    unit TEXT DEFAULT 'piece',
    bought INTEGER DEFAULT 0,     -- 0=pending, 1=bought
    estimated_price_eur REAL DEFAULT NULL,
    store_section TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    week_day TEXT DEFAULT ''        -- "Mon dinner" context
);

-- ============================================================
-- MEAL HISTORY (track what was actually eaten)
-- ============================================================
CREATE TABLE IF NOT EXISTS meal_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE DEFAULT CURRENT_DATE,
    meal_type TEXT CHECK(meal_type IN ('breakfast','lunch','dinner','snack')),
    recipe_id INTEGER REFERENCES recipes(id),
    custom_name TEXT DEFAULT '',     -- if not from recipe
    servings_eaten INTEGER DEFAULT 0,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5) DEFAULT NULL,
    notes TEXT DEFAULT '',
    logged_by TEXT DEFAULT 'Floor',  -- who reported it
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- FOOD WASTE LOG (track what went bad)
-- ============================================================
CREATE TABLE IF NOT EXISTS waste_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER REFERENCES ingredients(id),
    name TEXT NOT NULL,              -- denormalized
    quantity REAL DEFAULT 0,
    unit TEXT DEFAULT 'g',
    reason TEXT DEFAULT '',         -- expired, leftover, overbought, forgotten
    wasted_on DATE DEFAULT CURRENT_DATE,
    estimated_cost_eur REAL DEFAULT NULL,
    notes TEXT DEFAULT ''
);

-- ============================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================

-- Upcoming week's shopping needs
CREATE VIEW IF NOT EXISTS v_upcoming_meals AS
SELECT
    mpw.week_number,
    mpm.day_of_week,
    mpm.meal_type,
    r.name AS recipe_name,
    r.servings,
    r.prep_time + r.cook_time AS total_time
FROM meal_plan_meals mpm
JOIN meal_plan_weeks mpw ON mpm.week_id = mpw.id
LEFT JOIN recipes r ON mpm.recipe_id = r.id
WHERE mpw.plan_id = (SELECT id FROM meal_plans WHERE active = 1 ORDER BY start_date DESC LIMIT 1)
ORDER BY mpw.week_number, mpm.day_of_week, mpm.meal_type;

-- Pantry items expiring soon (next 3 days)
CREATE VIEW IF NOT EXISTS v_expiring_soon AS
SELECT
    pi.*,
    i.name AS ingredient_name,
    i.category,
    julianday(expires_on) - julianday('now') AS days_left
FROM pantry_items pi
JOIN ingredients i ON pi.ingredient_id = i.id
WHERE pi.expires_on IS NOT NULL
  AND julianday(expires_on) - julianday('now') <= 3
  AND pi.quantity > 0
ORDER BY days_left ASC;

-- Weekly ingredient summary (all needed for a given week)
CREATE VIEW IF NOT EXISTS v_weekly_ingredients AS
SELECT
    mpw.week_number,
    ri.ingredient_id,
    i.name AS ingredient_name,
    i.category,
    SUM(ri.quantity) AS total_quantity,
    ri.unit,
    COUNT(DISTINCT ri.recipe_id) AS used_in_recipes
FROM meal_plan_meals mpm
JOIN meal_plan_weeks mpw ON mpm.week_id = mpw.id
JOIN recipe_ingredients ri ON mpm.recipe_id = ri.recipe_id
JOIN ingredients i ON ri.ingredient_id = i.id
WHERE mpw.plan_id = (SELECT id FROM meal_plans WHERE active = 1 ORDER BY start_date DESC LIMIT 1)
GROUP BY mpw.week_number, ri.ingredient_id, ri.unit
ORDER BY i.category, i.name;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_pantry_expires ON pantry_items(expires_on);
CREATE INDEX IF NOT EXISTS idx_plan_active ON meal_plans(active);
CREATE INDEX IF NOT EXISTS idx_recipe_type ON recipes(type);
