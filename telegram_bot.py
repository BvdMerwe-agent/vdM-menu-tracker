#!/usr/bin/env python3
"""
Telegram bot script for Floor's kitchen commands.
Called by the Hermes gateway cron or manually for quick testing.
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_HOME_CHANNEL from environment.
Outputs MarkdownV2 formatted messages to stdout (Hermes picks these up via cron deliver=origin).
Also provides direct-send mode.
"""
import os
import sys
import sqlite3
import random
from pathlib import Path

# Ensure imports work when run from any cwd
sys.path.insert(0, str(Path(__file__).parent))
from core import (
    get_conn, get_active_plan, get_current_week_number, get_plan_week,
    get_week_menu, generate_shopping_list, fmt_week_menu, fmt_shopping_list,
    fmt_expiring, fmt_pantry_summary, get_recipe, list_expiring,
    add_pantry_item, log_meal,
    # New curated week functions
    get_collecting_week, add_meal_to_collection, remove_meal_from_collection,
    get_curated_pool, shuffle_and_schedule, get_curated_schedule,
    fmt_curated_pool, fmt_curated_schedule, advance_week,
    list_all_recipes_for_selection,
)
import datetime


def send(msg: str, chat_id: str = None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.getenv("TELEGRAM_HOME_CHANNEL")
    if not token:
        print(msg, flush=True)
        return
    import urllib.request, urllib.parse
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": msg,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": "True"
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")
        print(msg, flush=True)


def escape_md(text: str) -> str:
    for ch in "_-[]()~`>#+=|{}.!\\":
        text = text.replace(ch, "\\" + ch)
    return text


def remind():
    """Daily menu reminder — shows today's curated meals OR old plan fallback."""
    # Try curated schedule first
    schedule = get_curated_schedule()
    today = datetime.date.today().weekday()  # Monday=0
    
    if schedule:
        day_meals = [m for m in schedule if m.get("scheduled_day") == today]
        if day_meals:
            DAYS = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
            lines = [f"📆 *Vandaag ({DAYS[today]})*\n"]
            for m in day_meals:
                icon = "🥪" if m["meal_type"] == "lunch" else "🍽"
                status = " ✅" if m.get("cooked") else ""
                name = escape_md(m.get("recipe_name") or "TBD")
                lines.append(f"{icon} *{name}*{status}")
            
            # Expiry alert
            exp = list_expiring(2)
            if exp:
                lines.append(f"\n⚠️ *Pas op:*")
                for item in exp:
                    lines.append(f"  • {escape_md(item['ingredient_name'])} — nog {int(item['days_left'])} dag{'en' if item['days_left'] != 1 else ''}")
            
            msg = "\n".join(lines)
            print(msg)
            return
    
    # Fallback to old 12-week plan
    plan = get_active_plan()
    if not plan:
        print("Geen actief weekmenu gevonden.")
        return
    week = get_current_week_number(plan["id"])
    msg = fmt_week_menu(week, plan["id"])
    # Crop to just today
    for day_label in ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]:
        if day_label in msg:
            today_idx = msg.index(day_label)
            end = msg.find("\n\n", today_idx)
            if end == -1:
                end = len(msg)
            print(msg[today_idx:end])
            return
    print(msg)


def weekly():
    """Weekly overview — shows full week menu OR pool status."""
    # Try curated first
    schedule = get_curated_schedule()
    if schedule:
        print(fmt_curated_schedule())
        return
    
    # Fallback to old plan
    plan = get_active_plan()
    if not plan:
        print("Geen actief weekmenu gevonden.")
        return
    week = get_current_week_number(plan["id"])
    print(fmt_week_menu(week, plan["id"]))


def shopping():
    """Generate shopping list from old plan."""
    plan = get_active_plan()
    if not plan:
        print("Geen actief weekmenu gevonden.")
        return
    week = get_current_week_number(plan["id"])
    week_id = get_plan_week(plan["id"], week)
    lid = generate_shopping_list(week_id)
    print(fmt_shopping_list(lid))


def collect():
    """Show the current curated pool status — what's collected so far."""
    print(fmt_curated_pool())


def suggest(meal_type: str = None, cuisine: str = None):
    """Suggest recipes for collection."""
    recipes = list_all_recipes_for_selection(meal_type=meal_type, tag_filter=cuisine)
    if not recipes:
        print(f"Geen recepten gevonden voor {meal_type or 'alle'}.")
        return
    
    lines = [f"🍳 *Kies een {meal_type or 'gerecht'}*\n"]
    for i, r in enumerate(recipes[:15], 1):
        tags = f" ({r['tags']})" if r['tags'] else ""
        lines.append(f"  {i}. {escape_md(r['name'])}{escape_md(tags)}")
    
    lines.append(f"\n_Je hebt nu {len(recipes)} opties. Zeg het nummer of de naam om toe te voegen._")
    print("\n".join(lines))


def add_to_pool(recipe_id: int, meal_type: str):
    """Add a specific recipe to the collecting pool."""
    result = add_meal_to_collection(recipe_id, meal_type)
    if result["success"]:
        # Get recipe name
        r = get_recipe(recipe_id)
        name = r["name"] if r else f"recept #{recipe_id}"
        print(f"✅ *{escape_md(name)}* toegevoegd als {meal_type}.")
        print(f"{result['total']}/14 maaltijden verzameld.")
        if result["total"] >= 14:
            print("\n📦 *Pool vol!* Zeg 'shuffle' om de maaltijden over de dagen te verdelen.")
    else:
        print(f"⚠️ {escape_md(result['error'])}")


def remove_from_pool(slot_index: int):
    """Remove a meal from the collecting pool by slot number."""
    result = remove_meal_from_collection(slot_index)
    print(result.get("message", "Verwijderd"))


def shuffle():
    """Shuffle collected meals into day assignments."""
    result = shuffle_and_schedule()
    if result["success"]:
        print(result["message"])
        print("\n")
        print(fmt_curated_schedule())
    else:
        print(f"⚠️ {escape_md(result['error'])}")


def show_schedule():
    """Show current active curated schedule."""
    print(fmt_curated_schedule())


def sunday_prompt():
    """The Sunday collection prompt — triggered by cron."""
    cw = get_collecting_week()
    if not cw:
        # Auto-start new week
        next_monday = datetime.date.today() + datetime.timedelta(days=(7 - datetime.date.today().weekday()))
        from core import start_curated_week
        wid = start_curated_week(next_monday.isoformat())
        cw = get_collecting_week()
    
    week_start = cw["week_start"]
    pool = get_curated_pool(cw["id"])
    
    lines = [
        f"📅 *Zondag is plandag*",
        f"",
        f"Week van {escape_md(week_start)} — wat eten we?",
        f"",
        f"Verzamel {7 - sum(1 for p in pool if p['meal_type']=='lunch')} lunches en {7 - sum(1 for p in pool if p['meal_type']=='dinner')} diners.",
        f"",
        f"Typ een nummer of naam, of zeg 'suggestie lunch' voor ideeën.",
    ]
    print("\n".join(lines))


# --- Pantry helpers -------------------------------------------------------

def pantry_cmd(expiring_only: bool = False):
    if expiring_only:
        print(fmt_expiring())
    else:
        print(fmt_pantry_summary())


def recipe_card(recipe_id: int):
    r = get_recipe(recipe_id)
    if not r:
        print(f"Recept niet gevonden: {recipe_id}")
        return
    lines = [
        f"*🍳 {escape_md(r['name'])}*\n",
        f"Type: {r['type']} | Keuken: {r['cuisine']}\n",
        f"Bereidingstijd: {r['prep_time']} + {r['cook_time']} min | Porties: {r['servings']}\n",
    ]
    ings = r.get("ingredients", [])
    if ings:
        lines.append("\n*Ingrediënten:*")
        for i in ings:
            note = f" ({i['prep_note']})" if i.get('prep_note') else ""
            lines.append(f"  • {i['quantity']}{i['unit']} {escape_md(i['name'])}{note}")
    print("\n".join(lines))


# --- History --------------------------------------------------------------

def ate_cmd(recipe_id: int, servings: int = 4, note: str = ""):
    log_meal(
        date=str(datetime.date.today()),
        meal_type="dinner",
        recipe_id=recipe_id,
        servings_eaten=servings,
        notes=note,
        logged_by="user"
    )
    print("✅ Geregistreerd.")


# --- argparse glue --------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Floor's Kitchen Bot")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("remind", help="Today's menu + expiry alert")
    sub.add_parser("weekly", help="Full week overview")
    sub.add_parser("shopping", help="Generate shopping list")
    sub.add_parser("collect", help="Show curated collection pool status")
    sub.add_parser("shuffle", help="Shuffle collected meals into week schedule")
    sub.add_parser("schedule", help="Show active week schedule")
    sub.add_parser("sunday-prompt", help="Sunday collection prompt (cron)")
    
    p_suggest = sub.add_parser("suggest", help="Suggest recipes for collection")
    p_suggest.add_argument("--type", choices=["lunch", "dinner"], help="Meal type filter")
    p_suggest.add_argument("--cuisine", help="Cuisine filter")
    
    p_add = sub.add_parser("add", help="Add recipe to collection pool")
    p_add.add_argument("recipe_id", type=int, help="Recipe ID")
    p_add.add_argument("--type", choices=["lunch", "dinner"], required=True, help="Meal type")
    
    p_remove = sub.add_parser("remove", help="Remove recipe from pool by slot")
    p_remove.add_argument("slot", type=int, help="Slot index (0-13)")
    
    p_menu = sub.add_parser("menu", help="Legacy: show old plan week menu")
    p_menu.add_argument("--week", type=int, help="Week 1-12")
    
    p_pantry = sub.add_parser("pantry", help="Pantry summary")
    p_pantry.add_argument("--expiring", action="store_true", help="Only expiring items")
    
    p_recipe = sub.add_parser("recipe", help="Show recipe card")
    p_recipe.add_argument("--id", type=int, required=True, help="Recipe ID")
    
    p_ate = sub.add_parser("ate", help="Log a cooked meal")
    p_ate.add_argument("--recipe-id", type=int, required=True)
    p_ate.add_argument("--servings", type=int, default=4)
    p_ate.add_argument("--note", default="")

    args = parser.parse_args()

    if args.cmd == "remind":
        remind()
    elif args.cmd == "weekly":
        weekly()
    elif args.cmd == "shopping":
        shopping()
    elif args.cmd == "collect":
        collect()
    elif args.cmd == "suggest":
        suggest(args.type, args.cuisine)
    elif args.cmd == "add":
        add_to_pool(args.recipe_id, args.type)
    elif args.cmd == "remove":
        remove_from_pool(args.slot)
    elif args.cmd == "shuffle":
        shuffle()
    elif args.cmd == "schedule":
        show_schedule()
    elif args.cmd == "sunday-prompt":
        sunday_prompt()
    elif args.cmd == "menu":
        plan = get_active_plan()
        week = args.week or (get_current_week_number(plan["id"]) if plan else 1)
        print(fmt_week_menu(week, plan["id"]))
    elif args.cmd == "pantry":
        pantry_cmd(args.expiring)
    elif args.cmd == "recipe":
        recipe_card(args.id)
    elif args.cmd == "ate":
        ate_cmd(args.recipe_id, args.servings, args.note)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
