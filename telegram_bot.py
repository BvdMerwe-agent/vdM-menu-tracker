#!/usr/bin/env python3
"""
Floor Telegram Menu Bot — standalone handler for /menu, /shopping, /pantry, /recipe, /ate
Runs via cron or can be triggered by the Hermes gateway webhook system.
"""
import os
import sys
import json
import sqlite3
import argparse
import datetime
from pathlib import Path

# --- locate the menu tracker DB ----
TRACKER_DIR = Path(__file__).parent
DB_PATH = TRACKER_DIR / "menu.db"
CORE_PATH = TRACKER_DIR / "core.py"

if CORE_PATH.exists():
    sys.path.insert(0, str(TRACKER_DIR))
    from core import (
        get_active_plan, get_current_week_number, get_plan_week,
        get_week_menu, generate_shopping_list, get_shopping_list,
        fmt_week_menu, fmt_shopping_list, fmt_pantry_summary, fmt_expiring,
        mark_bought, mark_shopped, mark_meal_cooked, log_meal, list_expiring,
        get_recipe, list_recipes, add_pantry_item,
        DB_PATH as CORE_DB_PATH,
    )
else:
    raise RuntimeError("core.py not found")

# ---- telegram util -------------------------------------------------------------
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN_FLOOR")
CHAT = os.getenv("TELEGRAM_HOME_CHANNEL")

def send_msg(text: str, chat_id: str = None) -> dict:
    import urllib.request, urllib.parse
    cid = chat_id or CHAT
    if not TOKEN or not cid:
        print("Missing token or chat id")
        return {}
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": cid,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Send failed: {e}")
        return {}

# ---- commands -------------------------------------------------------------
def cmd_menu(args):
    plan = get_active_plan()
    if not plan:
        return "❌ No active meal plan."
    week = args.week or get_current_week_number(plan["id"])
    return fmt_week_menu(week, plan["id"])

def cmd_shopping(args):
    plan = get_active_plan()
    if not plan:
        return "❌ No active meal plan."
    if args.list_id:
        # Show existing list
        return fmt_shopping_list(args.list_id)
    week = args.week or get_current_week_number(plan["id"])
    week_id = get_plan_week(plan["id"], week)
    lid = generate_shopping_list(week_id)
    return f"🛒 *Shopping List for Week {week}* (ID: `{lid}`)\n\n" + fmt_shopping_list(lid)

def cmd_pantry(args):
    if args.expiring:
        return fmt_expiring()
    return fmt_pantry_summary()

def cmd_recipe(args):
    if args.query:
        results = list_recipes(tags=args.query)
        if not results:
            return f"🔍 No recipes found for '{args.query}'."
        lines = [f"🔍 *Recipes matching '{args.query}'*", ""]
        for r in results:
            tags = f" ({r['tags']})" if r["tags"] else ""
            lines.append(f"• [{r['id']}] {r['name']}{tags} — {r['type']}")
        return "\n".join(lines)
    if args.id:
        r = get_recipe(args.id)
        if not r:
            return "❌ Recipe not found."
        lines = [f"🍳 *{r.name}* ({r.cuisine})", f"_{r.tags}_" if r.tags else "", "",
                 f"⏱ Prep: {r.prep_time}m | Cook: {r.cook_time}m | Servings: {r.servings}",
                 f"🥗 {r.type.title()} | Difficulty: {r.difficulty}", ""]
        if r.ingredients:
            lines.append("*Ingredients:*")
            for ing in r.ingredients:
                opt = " _(optional)_" if ing["optional"] else ""
                note = f" — {ing['prep_note']}" if ing.get("prep_note") else ""
                lines.append(f"• {ing['quantity']:.1f} {ing['unit']} {ing['ingredient_name']}{opt}{note}")
        if r.notes:
            lines.append(f"\n📝 {r.notes}")
        return "\n".join(lines)
    # List all
    results = list_recipes(type_=args.type) if args.type else list_recipes()
    lines = ["📖 *Recipes:*", ""]
    for r in results:
        lines.append(f"[{r['id']}] {r['name']} ({r['type']})")
    return "\n".join(lines)

def cmd_ate(args):
    date = args.date or datetime.date.today().isoformat()
    meal_type = args.meal or "dinner"
    if args.recipe_id:
        r = get_recipe(args.recipe_id)
        if r:
            log_meal(date, meal_type, recipe_id=r.id, servings_eaten=args.servings or 1, rating=args.rating)
            return f"✅ Logged {r.name} for {meal_type} on {date}."
    return "Usage: ate --recipe-id <id> [--meal lunch|dinner] [--date YYYY-MM-DD] [--servings N] [--rating 1-5]"

def cmd_buy(args):
    if args.list_id and args.mark_done:
        mark_shopped(args.list_id)
        return f"✅ Shopping list {args.list_id} marked as done. Items added to pantry."
    if args.item_id:
        mark_bought(args.item_id)
        return f"☑️ Item {args.item_id} marked bought."
    return "Usage: buy --item-id <id> | --list-id <id> --mark-done"

def cmd_remind(args):
    """Daily meal reminder — sends upcoming meals for today."""
    plan = get_active_plan()
    if not plan:
        return "❌ No active meal plan."
    week = get_current_week_number(plan["id"])
    menu = get_week_menu(plan["id"], week)
    today = datetime.date.today()
    dow_map = {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}
    day_name = dow_map[today.weekday()]
    dm = menu.get(day_name, {})
    lines = [f"📆 *Vandaag ({day_name} — Week {week})*", ""]
    if dm.get("lunch"):
        l = dm["lunch"]
        cooked = " ✅" if l.get("cooked") else ""
        lines.append(f"🥪 Lunch: *{l['recipe_name']}*{cooked}")
    if dm.get("dinner"):
        d = dm["dinner"]
        cooked = " ✅" if d.get("cooked") else ""
        lines.append(f"🍽 Dinner: *{d['recipe_name']}*{cooked}")
    if not dm.get("lunch") and not dm.get("dinner"):
        lines.append("Nothing planned today.")
    # Expiry alert inline
    exp = list_expiring(2)
    if exp:
        lines.append("")
        lines.append("⚠️ *Expiring in 2 days:*")
        for e in exp:
            lines.append(f"• {e['ingredient_name']} ({e['days_left']}d left)")
    return "\n".join(lines)

def cmd_weekly(args):
    """Generate and send the weekly shopping list + menu overview."""
    plan = get_active_plan()
    if not plan:
        return "❌ No active meal plan."
    week = args.week or get_current_week_number(plan["id"])
    week_id = get_plan_week(plan["id"], week)
    lid = generate_shopping_list(week_id)
    msg = f"🛒 *Week {week} Shopping List*\n\n"
    msg += fmt_week_menu(week, plan["id"]) + "\n"
    msg += "━"*30 + "\n\n"
    msg += fmt_shopping_list(lid)
    msg += f"\n\n_List ID: `{lid}` — reply with_ `/buy --list-id {lid} --mark-done` _when shopped._"
    return msg

# ---- main ------------------------------------------------------------------
COMMANDS = {
    "menu": cmd_menu,
    "shopping": cmd_shopping,
    "pantry": cmd_pantry,
    "recipe": cmd_recipe,
    "ate": cmd_ate,
    "buy": cmd_buy,
    "remind": cmd_remind,
    "weekly": cmd_weekly,
}

def main(argv=None):
    parser = argparse.ArgumentParser(description="Floor Menu Tracker CLI / Telegram backend")
    sub = parser.add_subparsers(dest="cmd")

    p_menu = sub.add_parser("menu", help="Show week menu")
    p_menu.add_argument("--week", type=int, help="Week 1-12")

    p_shop = sub.add_parser("shopping", help="Generate or show shopping list")
    p_shop.add_argument("--week", type=int, help="Week number")
    p_shop.add_argument("--list-id", type=int, help="Show existing list")

    p_pantry = sub.add_parser("pantry", help="Show pantry")
    p_pantry.add_argument("--expiring", action="store_true", help="Show expiring items")

    p_recipe = sub.add_parser("recipe", help="Search or show recipes")
    p_recipe.add_argument("--query", type=str, help="Search by tag/name")
    p_recipe.add_argument("--id", type=int, help="Show recipe by ID")
    p_recipe.add_argument("--type", type=str, choices=["lunch","dinner"], help="Filter by type")

    p_ate = sub.add_parser("ate", help="Log a meal")
    p_ate.add_argument("--recipe-id", type=int, required=True)
    p_ate.add_argument("--meal", type=str, default="dinner", choices=["lunch","dinner"])
    p_ate.add_argument("--date", type=str)
    p_ate.add_argument("--servings", type=int, default=1)
    p_ate.add_argument("--rating", type=int)

    p_buy = sub.add_parser("buy", help="Mark items bought")
    p_buy.add_argument("--item-id", type=int)
    p_buy.add_argument("--list-id", type=int)
    p_buy.add_argument("--mark-done", action="store_true")

    p_remind = sub.add_parser("remind", help="Today's meal reminder")
    p_weekly = sub.add_parser("weekly", help="Weekly shopping + menu")
    p_weekly.add_argument("--week", type=int)

    args = parser.parse_args(argv)
    if not args.cmd or args.cmd not in COMMANDS:
        parser.print_help()
        sys.exit(1)

    output = COMMANDS[args.cmd](args)

    # If TELEGRAM_OUTPUT=1, send to Telegram. Otherwise print.
    if os.getenv("TELEGRAM_OUTPUT") == "1" and args.cmd in ("remind", "weekly", "menu", "shopping", "pantry"):
        send_msg(output)
    else:
        print(output)

if __name__ == "__main__":
    main()
