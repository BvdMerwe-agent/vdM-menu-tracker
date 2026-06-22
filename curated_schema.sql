-- ============================================================
-- CURATED WEEKLY MEAL SYSTEM (interactive, user-driven)
-- Instead of pre-generating 12 weeks, collect 14 meals on Sunday
-- that can be shuffled for the upcoming week.
-- ============================================================

CREATE TABLE IF NOT EXISTS curated_weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,          -- Monday of this week
    status TEXT DEFAULT 'collecting' CHECK(status IN ('collecting','ready','active','past')),
    -- collecting = accepting meal suggestions
    -- ready = 14 meals collected, waiting to be scheduled
    -- active = currently assigned to days
    -- past = week is over
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finalized_at DATETIME DEFAULT NULL,
    notes TEXT DEFAULT ''
);

-- Individual meals in the current/next curated week
CREATE TABLE IF NOT EXISTS curated_week_meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL REFERENCES curated_weeks(id) ON DELETE CASCADE,
    slot_index INTEGER NOT NULL CHECK(slot_index BETWEEN 0 AND 13), -- 0-6 lunch, 7-13 dinner
    meal_type TEXT NOT NULL CHECK(meal_type IN ('lunch','dinner')),
    recipe_id INTEGER REFERENCES recipes(id),
    -- When a meal is scheduled:
    scheduled_day INTEGER DEFAULT NULL CHECK(scheduled_day BETWEEN 0 AND 6), -- 0=Mon, 6=Sun
    scheduled_meal_type TEXT DEFAULT NULL CHECK(scheduled_meal_type IN ('lunch','dinner')),
    cooked INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    added_by TEXT DEFAULT 'Floor',
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_id, slot_index)
);

-- ================================================
-- Indexes
-- ================================================
CREATE INDEX IF NOT EXISTS idx_curated_weeks_status ON curated_weeks(status);
CREATE INDEX IF NOT EXISTS idx_curated_week_meals_week ON curated_week_meals(week_id);

-- ================================================
-- Views
-- ================================================

-- Current week's schedule (if active)
CREATE VIEW IF NOT EXISTS v_curated_schedule AS
SELECT
    cw.id as week_id,
    cw.week_start,
    cw.status,
    cwm.scheduled_day,
    CASE cwm.scheduled_day
        WHEN 0 THEN 'Mon' WHEN 1 THEN 'Tue' WHEN 2 THEN 'Wed'
        WHEN 3 THEN 'Thu' WHEN 4 THEN 'Fri' WHEN 5 THEN 'Sat' WHEN 6 THEN 'Sun'
    END as day_name,
    cwm.scheduled_meal_type as meal_type,
    r.id as recipe_id,
    r.name as recipe_name,
    r.cuisine,
    r.prep_time,
    r.cook_time,
    cwm.cooked,
    cwm.skipped,
    cwm.added_by
FROM curated_weeks cw
JOIN curated_week_meals cwm ON cw.id = cwm.week_id
LEFT JOIN recipes r ON cwm.recipe_id = r.id
WHERE cw.status IN ('ready','active')
ORDER BY cwm.scheduled_day, CASE cwm.scheduled_meal_type WHEN 'lunch' THEN 0 ELSE 1 END;

-- Pool view: meals collected but not yet assigned to days
CREATE VIEW IF NOT EXISTS v_curated_pool AS
SELECT
    cw.id as week_id,
    cw.week_start,
    cwm.slot_index,
    cwm.meal_type,
    r.id as recipe_id,
    r.name as recipe_name,
    r.tags,
    cwm.added_by
FROM curated_weeks cw
JOIN curated_week_meals cwm ON cw.id = cwm.week_id
LEFT JOIN recipes r ON cwm.recipe_id = r.id
WHERE cw.status = 'collecting'
ORDER BY cwm.meal_type, cwm.slot_index;
