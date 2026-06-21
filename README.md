# vdM Menu & Grocery Tracker

A 12-week rotating meal planner, pantry tracker, and shopping-list generator for the vdM household. Built for a strictly vegetarian kitchen (no meat, fish, or eggs — tofu scramble ftw).

## What's inside

| Component | Description |
|---|---|
| `schema.sql` | SQLite database schema |
| `core.py` | Core library — recipes, plans, pantry, shopping logic |
| `telegram_bot.py` | CLI that outputs Telegram-ready Markdown |
| `seed_vegetarian.py` | Seeder for 37 vegetarian recipes (21 dinners, 16 lunches) |
| `export_spreadsheet.py` | Export meal plans + ingredients to CSV or Excel |

## Quick start

```bash
# 1. Set up the database
python3 seed_vegetarian.py

# 2. View this week's menu
python3 telegram_bot.py menu --week 1

# 3. Generate a shopping list
python3 telegram_bot.py shopping

# 4. Check what's expiring
python3 telegram_bot.py pantry --expiring

# 5. Export everything to a spreadsheet
python3 export_spreadsheet.py --format xlsx --output meal_plan.xlsx
```

## Database tables

- `recipes` — recipe cards with cuisine, timing, difficulty
- `ingredients` — canonical ingredient list (categories, shelf life)
- `recipe_ingredients` — what goes into what
- `meal_plans` / `meal_plan_weeks` / `meal_plan_meals` — the 12-week schedule
- `pantry_items` — what's actually in your fridge/pantry/freezer
- `shopping_lists` / `shopping_list_items` — auto-generated shopping lists
- `meal_history` — what you actually ate

## Key features

- **Pantry-aware shopping lists** — subtracts what you already have
- **Expiry alerts** — flags items expiring in the next few days
- **Meal logging** — mark meals as cooked, track what you really ate
- **Vegetarian by default** — all 37 recipes are meat-free, egg-free (tofu scramble replaces eggs)
- **Telegram formatted** — all output is MarkdownV2-ready for your kitchen bot

## License

MIT — use it, fork it, feed your family.
