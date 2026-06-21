#!/usr/bin/env python3
"""
Vegetarian seed for vdM Home — no meat, fish, or eggs.
Dairy is fine. Soya/meat substitutes are fine.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from core import init_db, add_recipe, add_ingredient, add_recipe_ingredient, create_plan, generate_12_week_plan

RECIPES = [
    # ====================== DINNERS (20) ======================
    {
        "name": "Vegetarische linzenstoofschotel",
        "type": "dinner", "cuisine": "Middle Eastern",
        "prep_time": 10, "cook_time": 40, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,comfort,healthy",
        "ingredients": [
            ("groene linzen", 250, "g", "pantry", ""),
            ("passata", 400, "ml", "pantry", ""),
            ("wortel", 2, "stuk", "produce", "in blokjes"),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 3, "teen", "produce", "geperst"),
            ("spinazie", 200, "g", "produce", "verse"),
            ("feta kaas", 100, "g", "dairy", "in kruimels"),
            ("komijn", 1, "tl", "pantry", ""),
            ("aardappel", 600, "g", "produce", ""),
            ("citroen", 1, "stuk", "produce", ""),
            ("olijfolie", 15, "ml", "pantry", ""),
        ],
    },
    {
        "name": "Pasta pesto met gegrilde groente",
        "type": "dinner", "cuisine": "Italian",
        "prep_time": 15, "cook_time": 20, "servings": 4,
        "difficulty": "easy", "tags": "pasta,vegetarian,quick",
        "ingredients": [
            ("pasta", 300, "g", "pantry", "penne"),
            ("pestosaus", 150, "g", "pantry", ""),
            ("courgette", 2, "stuk", "produce", "in plakjes"),
            ("paprika", 2, "stuk", "produce", "in reepjes"),
            ("cherrytomaat", 200, "g", "produce", ""),
            ("parmezaanse kaas", 50, "g", "dairy", ""),
            ("pijnboompit", 20, "g", "pantry", ""),
            ("olijfolie", 15, "ml", "pantry", ""),
        ],
    },
    {
        "name": "Griekse moussaka met aubergine",
        "type": "dinner", "cuisine": "Greek",
        "prep_time": 30, "cook_time": 60, "servings": 4,
        "difficulty": "medium", "tags": "vegetarian,comfort,baked",
        "ingredients": [
            ("aubergine", 2, "stuk", "produce", "in plakken"),
            ("linzen", 200, "g", "pantry", "gekookt"),
            ("aardappel", 400, "g", "produce", "in plakjes"),
            ("griekse yoghurt", 200, "g", "dairy", ""),
            ("ei", 2, "stuk", "dairy", ""),
            ("tomatensaus", 300, "ml", "pantry", ""),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 2, "teen", "produce", "geperst"),
            ("cinnamon", 1, "snuf", "pantry", ""),
            ("parmezaanse kaas", 50, "g", "dairy", ""),
        ],
    },
    {
        "name": "Thaise groene curry met tofu",
        "type": "dinner", "cuisine": "Thai",
        "prep_time": 10, "cook_time": 25, "servings": 4,
        "difficulty": "medium", "tags": "spicy,coconut,asian",
        "ingredients": [
            ("tofu", 400, "g", "produce", "vast, in blokjes"),
            ("kokosmelk", 400, "ml", "pantry", ""),
            ("groene curry pasta", 50, "g", "pantry", ""),
            ("babymais", 150, "g", "produce", ""),
            ("snijbonen", 150, "g", "produce", ""),
            ("thaise basilicum", 10, "g", "produce", "optioneel"),
            ("aubergine", 1, "stuk", "produce", "in blokjes"),
            ("rijst", 300, "g", "pantry", ""),
            ("limoen", 1, "stuk", "produce", ""),
        ],
    },
    {
        "name": "Mexicaanse burrito bowl",
        "type": "dinner", "cuisine": "Mexican",
        "prep_time": 20, "cook_time": 20, "servings": 4,
        "difficulty": "easy", "tags": "tex-mex,healthy,vegetarian",
        "ingredients": [
            ("rijst", 300, "g", "pantry", ""),
            ("zwarte bonen", 400, "g", "pantry", ""),
            ("mais", 200, "g", "pantry", ""),
            ("paprika", 2, "stuk", "produce", "in blokjes"),
            ("avocado", 2, "stuk", "produce", ""),
            ("limoen", 1, "stuk", "produce", ""),
            ("jalapeño", 1, "stuk", "produce", "optioneel"),
            ("salsa", 100, "g", "pantry", ""),
            ("cumin", 1, "tl", "pantry", ""),
            ("griekse yoghurt", 100, "g", "dairy", "als topping"),
        ],
    },
    {
        "name": "Geroosterde groentes met hummus",
        "type": "dinner", "cuisine": "Mediterranean",
        "prep_time": 15, "cook_time": 35, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,healthy,one-pan",
        "ingredients": [
            ("aubergine", 1, "stuk", "produce", "in blokjes"),
            ("courgette", 2, "stuk", "produce", "in plakjes"),
            ("paprika", 2, "stuk", "produce", "in reepjes"),
            ("ui", 1, "stuk", "produce", "in parten"),
            ("cherrytomaat", 200, "g", "produce", ""),
            ("hummus", 200, "g", "pantry", ""),
            ("olijfolie", 30, "ml", "pantry", ""),
            ("pitabroodje", 4, "stuk", "bakery", ""),
            ("komkommer", 1, "stuk", "produce", ""),
            ("knoflook", 2, "teen", "produce", "geperst"),
        ],
    },
    {
        "name": "Indische dal met spinazie",
        "type": "dinner", "cuisine": "Indian",
        "prep_time": 10, "cook_time": 40, "servings": 4,
        "difficulty": "easy", "tags": "spicy,lentils,comfort",
        "ingredients": [
            ("rode linzen", 300, "g", "pantry", ""),
            ("tomatenblokjes", 400, "g", "pantry", ""),
            ("kokosmelk", 250, "ml", "pantry", ""),
            ("spinazie", 300, "g", "produce", ""),
            ("garam masala", 15, "g", "pantry", ""),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 3, "teen", "produce", "geperst"),
            ("gember", 20, "g", "produce", "geperst"),
            ("rijst", 300, "g", "pantry", ""),
            ("coriander", 10, "g", "produce", "vers"),
        ],
    },
    {
        "name": "Quiche met spinazie en feta",
        "type": "dinner", "cuisine": "French",
        "prep_time": 20, "cook_time": 50, "servings": 4,
        "difficulty": "medium", "tags": "vegetarian,comfort,baked",
        "ingredients": [
            ("spinazie", 400, "g", "produce", "verse"),
            ("ei", 4, "stuk", "dairy", ""),
            ("creme fraiche", 200, "ml", "dairy", ""),
            ("feta kaas", 150, "g", "dairy", "in kruimels"),
            ("boter", 50, "g", "dairy", ""),
            ("tomaat", 2, "stuk", "produce", "in plakjes"),
            ("zout", 1, "snuf", "pantry", ""),
            ("peper", 1, "snuf", "pantry", ""),
        ],
    },
    {
        "name": "Japanse groentecurry",
        "type": "dinner", "cuisine": "Japanese",
        "prep_time": 15, "cook_time": 30, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,comfort,asian",
        "ingredients": [
            ("aardappel", 400, "g", "produce", "in blokjes"),
            ("wortel", 2, "stuk", "produce", "in stukjes"),
            ("ui", 1, "stuk", "produce", ""),
            ("courgette", 1, "stuk", "produce", "in stukken"),
            ("japanse curry blokjes", 100, "g", "pantry", ""),
            ("rijst", 300, "g", "pantry", ""),
            ("sla", 100, "g", "produce", ""),
            ("sesam zaadjes", 10, "g", "pantry", ""),
        ],
    },
    {
        "name": "Falafel met bulgur en salade",
        "type": "dinner", "cuisine": "Levantine",
        "prep_time": 10, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,quick,middle-eastern",
        "ingredients": [
            ("falafelballetjes", 300, "g", "frozen", "of vers"),
            ("bulgur", 200, "g", "pantry", "gekookt"),
            ("komkommer", 1, "stuk", "produce", ""),
            ("tomaat", 3, "stuk", "produce", ""),
            ("rode ui", 0.5, "stuk", "produce", ""),
            ("tahini", 30, "ml", "pantry", ""),
            ("citroen", 1, "stuk", "produce", ""),
            ("knoflook", 1, "teen", "produce", ""),
            ("chili vlokken", 1, "snuf", "pantry", ""),
            ("peterselie", 10, "g", "produce", ""),
        ],
    },
    {
        "name": "Risotto met paddenstoelen",
        "type": "dinner", "cuisine": "Italian",
        "prep_time": 10, "cook_time": 35, "servings": 4,
        "difficulty": "medium", "tags": "vegetarian,comfort,italian",
        "ingredients": [
            ("risottorijst", 300, "g", "pantry", ""),
            ("gemengde paddenstoelen", 400, "g", "produce", ""),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 2, "teen", "produce", "geperst"),
            ("vegetarische bouillon", 800, "ml", "pantry", ""),
            ("parmezaanse kaas", 60, "g", "dairy", "geraspt"),
            ("boter", 30, "g", "dairy", ""),
            ("witte wijn", 100, "ml", "pantry", "optioneel"),
            ("tijm", 3, "takje", "produce", ""),
        ],
    },
    {
        "name": "Bonenschotel uit de oven",
        "type": "dinner", "cuisine": "Tex-Mex",
        "prep_time": 15, "cook_time": 30, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,comfort,baked",
        "ingredients": [
            ("kidney bonen", 400, "g", "pantry", ""),
            ("mais", 200, "g", "pantry", ""),
            ("paprika", 2, "stuk", "produce", "in blokjes"),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("tomatenblokjes", 400, "g", "pantry", ""),
            ("geraspte kaas", 150, "g", "dairy", ""),
            ("tortilla", 4, "stuk", "bakery", "als bodem"),
            ("cumin", 1, "tl", "pantry", ""),
            ("paprikapoeder", 10, "g", "pantry", ""),
            ("griekse yoghurt", 100, "g", "dairy", "als topping"),
        ],
    },
    {
        "name": "Gado-gado met pindasaus",
        "type": "dinner", "cuisine": "Indonesian",
        "prep_time": 20, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,asian,salad",
        "ingredients": [
            ("aardappel", 400, "g", "produce", "gekookt in schil"),
            ("boontjes", 200, "g", "produce", "gekookt"),
            ("taugé", 100, "g", "produce", ""),
            ("spinazie", 200, "g", "produce", ""),
            ("tempeh", 200, "g", "produce", "gebakken plakjes"),
            ("pindasaus", 200, "g", "pantry", ""),
            ("ei", 2, "stuk", "dairy", "gekookt"),
            ("ui", 0.5, "stuk", "produce", ""),
            ("kroepoek", 50, "g", "pantry", ""),
        ],
    },
    {
        "name": "Nasi goreng met tofu",
        "type": "dinner", "cuisine": "Indonesian",
        "prep_time": 15, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,asian,rice",
        "ingredients": [
            ("rijst", 300, "g", "pantry", "gekookt"),
            ("tofu", 300, "g", "produce", "in blokjes"),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 2, "teen", "produce", "geperst"),
            ("taugé", 100, "g", "produce", ""),
            ("boontjes", 100, "g", "produce", "in stukjes"),
            ("ketjap manis", 30, "ml", "pantry", ""),
            ("sambal", 1, "tl", "pantry", ""),
            ("ui prei", 1, "stuk", "produce", "in ringen"),
        ],
    },
    {
        "name": "Paella met paddenstoelen",
        "type": "dinner", "cuisine": "Spanish",
        "prep_time": 20, "cook_time": 40, "servings": 4,
        "difficulty": "medium", "tags": "vegetarian,rice,spanish",
        "ingredients": [
            ("rijst", 300, "g", "pantry", ""),
            ("gemengde paddenstoelen", 400, "g", "produce", ""),
            ("paprika", 2, "stuk", "produce", "in reepjes"),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 3, "teen", "produce", "geperst"),
            ("vegetarische bouillon", 750, "ml", "pantry", ""),
            ("safran", 1, "snuf", "pantry", ""),
            ("erwtjes", 100, "g", "frozen", ""),
            ("citroen", 1, "stuk", "produce", "plakjes"),
        ],
    },
    {
        "name": "Soya kip teriyaki met groente",
        "type": "dinner", "cuisine": "Japanese",
        "prep_time": 10, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,soya,quick",
        "ingredients": [
            ("soya kip", 400, "g", "frozen", "in reepjes"),
            ("paksoi", 200, "g", "produce", ""),
            ("paprika", 2, "stuk", "produce", "in reepjes"),
            ("wortel", 2, "stuk", "produce", "julienne"),
            ("teriyaki saus", 60, "ml", "pantry", ""),
            ("rijst", 300, "g", "pantry", ""),
            ("sesam zaadjes", 10, "g", "pantry", ""),
            ("bosui", 2, "stuk", "produce", ""),
        ],
    },
    {
        "name": "Vegetarische hachee met rode kool",
        "type": "dinner", "cuisine": "Dutch",
        "prep_time": 15, "cook_time": 60, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,comfort,dutch",
        "ingredients": [
            ("vegetarisch gehakt", 500, "g", "frozen", ""),
            ("aardappel", 800, "g", "produce", "puree"),
            ("melk", 200, "ml", "dairy", ""),
            ("boter", 50, "g", "dairy", ""),
            ("rode kool", 500, "g", "produce", "kant-en-klaar"),
            ("ui", 2, "stuk", "produce", "gesnipperd"),
            ("laurel", 2, "blad", "pantry", ""),
            ("appelstroop", 15, "ml", "pantry", ""),
            ("peper", 1, "snuf", "pantry", ""),
            ("zout", 1, "snuf", "pantry", ""),
        ],
    },
    {
        "name": "Pizza margherita",
        "type": "dinner", "cuisine": "Italian",
        "prep_time": 10, "cook_time": 15, "servings": 2,
        "difficulty": "easy", "tags": "vegetarian,quick,comfort",
        "ingredients": [
            ("diepvries pizza", 1, "stuk", "frozen", ""),
            ("sla", 100, "g", "produce", "als bijgerecht"),
            ("cherrytomaat", 100, "g", "produce", ""),
            ("olijfolie", 10, "ml", "pantry", ""),
        ],
    },
    {
        "name": "Gevulde paprika's met rijst",
        "type": "dinner", "cuisine": "Mediterranean",
        "prep_time": 20, "cook_time": 45, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,comfort,baked",
        "ingredients": [
            ("paprika", 4, "stuk", "produce", "groot"),
            ("rijst", 200, "g", "pantry", "gekookt"),
            ("tomatenblokjes", 400, "g", "pantry", ""),
            ("kidney bonen", 200, "g", "pantry", ""),
            ("mais", 100, "g", "pantry", ""),
            ("geraspte kaas", 100, "g", "dairy", ""),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("komijn", 1, "tl", "pantry", ""),
            ("peterselie", 10, "g", "produce", ""),
        ],
    },
    {
        "name": "Hollandse erwtensoep vegetarisch",
        "type": "dinner", "cuisine": "Dutch",
        "prep_time": 15, "cook_time": 90, "servings": 6,
        "difficulty": "easy", "tags": "soup,winter,comfort,vegetarian",
        "ingredients": [
            ("spliterwten", 300, "g", "pantry", "gedroogd"),
            ("vegetarische rookworst", 300, "g", "frozen", ""),
            ("wortel", 2, "stuk", "produce", "in blokjes"),
            ("knolselderij", 200, "g", "produce", "in blokjes"),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("knoflook", 2, "teen", "produce", "geperst"),
            ("laurel", 2, "blad", "pantry", ""),
            ("peper", 1, "snuf", "pantry", ""),
            ("zout", 1, "snuf", "pantry", ""),
        ],
    },
    {
        "name": "Pad thai met tofu",
        "type": "dinner", "cuisine": "Thai",
        "prep_time": 20, "cook_time": 15, "servings": 4,
        "difficulty": "medium", "tags": "vegetarian,noodles,spicy",
        "ingredients": [
            ("rijstnoedels", 250, "g", "pantry", ""),
            ("tofu", 300, "g", "produce", "in blokjes"),
            ("ei", 2, "stuk", "dairy", ""),
            ("tamarinde pasta", 30, "g", "pantry", ""),
            ("bosui", 3, "stuk", "produce", ""),
            ("taugé", 100, "g", "produce", ""),
            ("limoen", 1, "stuk", "produce", ""),
            ("pinda's", 30, "g", "pantry", "gehakt"),
            ("palm suiker", 15, "g", "pantry", ""),
            ("olijfolie", 15, "ml", "pantry", ""),
        ],
    },

    # ====================== LUNCHES (16) ======================
    {
        "name": "Wrap met hummus en gegrilde groente",
        "type": "lunch", "cuisine": "Mediterranean",
        "prep_time": 10, "cook_time": 10, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,wrap,quick",
        "ingredients": [
            ("wraps", 4, "stuk", "bakery", ""),
            ("hummus", 200, "g", "pantry", ""),
            ("paprika", 2, "stuk", "produce", "in reepjes"),
            ("courgette", 1, "stuk", "produce", "in plakjes"),
            ("rode ui", 0.5, "stuk", "produce", ""),
            ("feta kaas", 50, "g", "dairy", ""),
            ("rucola", 50, "g", "produce", ""),
            ("olijfolie", 15, "ml", "pantry", ""),
        ],
    },
    {
        "name": "Griekse salade met feta",
        "type": "lunch", "cuisine": "Greek",
        "prep_time": 10, "cook_time": 0, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,salad,cold",
        "ingredients": [
            ("tomaat", 4, "stuk", "produce", ""),
            ("komkommer", 2, "stuk", "produce", ""),
            ("rode ui", 0.5, "stuk", "produce", ""),
            ("olijven", 50, "g", "pantry", ""),
            ("feta kaas", 150, "g", "dairy", ""),
            ("olijfolie", 30, "ml", "pantry", ""),
            ("oregano", 1, "snuf", "pantry", ""),
            ("pitabroodje", 2, "stuk", "bakery", ""),
        ],
    },
    {
        "name": "Avocado toast deluxe",
        "type": "lunch", "cuisine": "Modern",
        "prep_time": 10, "cook_time": 0, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,healthy,no-cook",
        "ingredients": [
            ("volkoren brood", 4, "stuk", "bakery", "gesneden"),
            ("avocado", 2, "stuk", "produce", "prak"),
            ("citroensap", 15, "ml", "pantry", ""),
            ("bosui", 1, "stuk", "produce", ""),
            ("chili vlokken", 1, "snuf", "pantry", ""),
            ("peper", 1, "snuf", "pantry", ""),
        ],
    },
    {
        "name": "Broodje balletjes in tomatensaus",
        "type": "lunch", "cuisine": "Dutch",
        "prep_time": 5, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,sandwich,comfort",
        "ingredients": [
            ("vegetarische balletjes", 400, "g", "frozen", ""),
            ("tomatensaus", 300, "ml", "pantry", ""),
            ("pitabroodje", 4, "stuk", "bakery", ""),
            ("kaas", 80, "g", "dairy", "gesneden"),
            ("sla", 50, "g", "produce", ""),
        ],
    },
    {
        "name": "Quinoa salade met gegrilde groente",
        "type": "lunch", "cuisine": "Modern",
        "prep_time": 15, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,salad,healthy",
        "ingredients": [
            ("quinoa", 200, "g", "pantry", "gekookt"),
            ("paprika", 1, "stuk", "produce", "in blokjes"),
            ("mais", 100, "g", "pantry", ""),
            ("spinazie", 100, "g", "produce", ""),
            ("limoen", 1, "stuk", "produce", ""),
            ("olijfolie", 15, "ml", "pantry", ""),
            ("komkommer", 1, "stuk", "produce", ""),
            ("feta kaas", 50, "g", "dairy", ""),
        ],
    },
    {
        "name": "Toast Hawaii vegetarisch",
        "type": "lunch", "cuisine": "Dutch",
        "prep_time": 5, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,toast,comfort",
        "ingredients": [
            ("wit brood", 4, "stuk", "bakery", ""),
            ("vegetarische ham", 200, "g", "frozen", ""),
            ("kaas", 120, "g", "dairy", ""),
            ("ananas uit blik", 4, "ring", "pantry", ""),
            ("zoete chili saus", 30, "ml", "pantry", "optioneel"),
        ],
    },
    {
        "name": "Tomatensoep met kaasbroodjes",
        "type": "lunch", "cuisine": "Dutch",
        "prep_time": 5, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "soup,comfort,vegetarian",
        "ingredients": [
            ("tomatensoep", 1, "liter", "pantry", "vers"),
            ("baguette", 1, "stuk", "bakery", ""),
            ("geraspte kaas", 100, "g", "dairy", ""),
            ("bosui", 2, "stuk", "produce", ""),
            ("creme fraiche", 50, "g", "dairy", "dollop"),
        ],
    },
    {
        "name": "Pastasalade pesto",
        "type": "lunch", "cuisine": "Italian",
        "prep_time": 10, "cook_time": 15, "servings": 4,
        "difficulty": "easy", "tags": "pasta,cold,comfort",
        "ingredients": [
            ("fusilli pasta", 300, "g", "pantry", ""),
            ("pestosaus", 100, "g", "pantry", ""),
            ("pijnboompit", 20, "g", "pantry", ""),
            ("cherrytomaat", 200, "g", "produce", ""),
            ("mozzarella bolletjes", 125, "g", "dairy", ""),
            ("peper", 1, "snuf", "pantry", ""),
        ],
    },
    {
        "name": "Taco bowl vegetarisch",
        "type": "lunch", "cuisine": "Mexican",
        "prep_time": 15, "cook_time": 10, "servings": 4,
        "difficulty": "easy", "tags": "vegetarian,spicy,healthy",
        "ingredients": [
            ("rijst", 200, "g", "pantry", ""),
            ("zwarte bonen", 250, "g", "pantry", ""),
            ("salsa", 100, "g", "pantry", ""),
            ("mais", 100, "g", "pantry", ""),
            ("tomaat", 2, "stuk", "produce", ""),
            ("avocado", 1, "stuk", "produce", ""),
            ("cheddar", 50, "g", "dairy", "geraspt"),
            ("sla", 100, "g", "produce", ""),
            ("tortilla", 4, "stuk", "bakery", ""),
            ("guacamole", 100, "g", "pantry", ""),
        ],
    },
    {
        "name": "Spaanse tortilla",
        "type": "lunch", "cuisine": "Spanish",
        "prep_time": 10, "cook_time": 20, "servings": 4,
        "difficulty": "easy", "tags": "eggs,vegetarian,comfort",
        "ingredients": [
            ("aardappel", 400, "g", "produce", "in plakjes"),
            ("ei", 5, "stuk", "dairy", ""),
            ("ui", 1, "stuk", "produce", "gesnipperd"),
            ("olijfolie", 30, "ml", "pantry", ""),
            ("zout", 1, "snuf", "pantry", ""),
            ("peper", 1, "snuf", "pantry", ""),
        ],
    },
    {
        "name": "Zuurkoolsalade vegetarisch",
        "type": "lunch", "cuisine": "Dutch",
        "prep_time": 10, "cook_time": 0, "servings": 4,
        "difficulty": "easy", "tags": "cold,salad,dutch",
        "ingredients": [
            ("zuurkool", 200, "g", "pantry", "uitgeknepen"),
            ("mandarijn", 2, "stuk", "produce", "in stukjes"),
            ("spekjes", 100, "g", "frozen", "vegetarisch, gebakken"),
            ("walnoten", 30, "g", "pantry", ""),
            ("dijon mosterd", 15, "g", "pantry", ""),
            ("mayonaise", 30, "g", "pantry", ""),
            ("sla", 100, "g", "produce", ""),
        ],
    },
    {
        "name": "Japanse koude soba noodles",
        "type": "lunch", "cuisine": "Japanese",
        "prep_time": 10, "cook_time": 10, "servings": 4,
        "difficulty": "easy", "tags": "noodles,cold,asian",
        "ingredients": [
            ("soba noodles", 250, "g", "pantry", ""),
            ("sojasaus", 30, "ml", "pantry", ""),
            ("mirin", 15, "ml", "pantry", ""),
            ("sesamolie", 10, "ml", "pantry", ""),
            ("komkommer", 1, "stuk", "produce", "julienne"),
            ("taugé", 50, "g", "produce", ""),
            ("bosui", 2, "stuk", "produce", ""),
            ("wasabi", 5, "g", "pantry", ""),
            ("sesam zaadjes", 10, "g", "pantry", ""),
        ],
    },
    {
        "name": "Rijsttafel salade Indonesisch",
        "type": "lunch", "cuisine": "Indonesian",
        "prep_time": 15, "cook_time": 10, "servings": 4,
        "difficulty": "easy", "tags": "cold,salad,asian",
        "ingredients": [
            ("rijst", 200, "g", "pantry", "gekookt en afgekoeld"),
            ("saté saus", 100, "ml", "pantry", ""),
            ("gurkensalade", 100, "g", "pantry", ""),
            ("bamba", 50, "g", "pantry", ""),
            ("gekookt ei", 2, "stuk", "dairy", ""),
            ("sla", 100, "g", "produce", ""),
            ("ui", 0.5, "stuk", "produce", ""),
            ("komkommer", 0.5, "stuk", "produce", ""),
        ],
    },
    {
        "name": "Broodje Surinaamse tofu kerrie",
        "type": "lunch", "cuisine": "Surinamese",
        "prep_time": 10, "cook_time": 10, "servings": 4,
        "difficulty": "easy", "tags": "spicy,sandwich,vegetarian",
        "ingredients": [
            ("tofu", 300, "g", "produce", "in reepjes"),
            ("kerriepoeder", 10, "g", "pantry", ""),
            ("ui", 0.5, "stuk", "produce", ""),
            ("knoflook", 1, "teen", "produce", ""),
            ("broodje", 4, "stuk", "bakery", ""),
            ("sla", 50, "g", "produce", ""),
            ("tomaat", 1, "stuk", "produce", ""),
            ("taugé", 50, "g", "produce", "optioneel"),
            ("madame jeanette peper", 1, "stuk", "produce", "optioneel"),
        ],
    },
    {
        "name": "Wrap met rosbief vegetarisch",
        "type": "lunch", "cuisine": "Dutch",
        "prep_time": 5, "cook_time": 0, "servings": 4,
        "difficulty": "easy", "tags": "cold,sandwich,quick",
        "ingredients": [
            ("wraps", 4, "stuk", "bakery", ""),
            ("vegetarische rosbief", 200, "g", "frozen", "gesneden"),
            ("rucola", 50, "g", "produce", ""),
            ("tomaat", 1, "stuk", "produce", ""),
            ("mosterd dressing", 30, "ml", "pantry", ""),
            ("mais", 50, "g", "pantry", ""),
            ("komkommer", 0.5, "stuk", "produce", ""),
        ],
    },
    {
        "name": "Aardappel-prei soep",
        "type": "lunch", "cuisine": "Dutch",
        "prep_time": 10, "cook_time": 25, "servings": 4,
        "difficulty": "easy", "tags": "soup,comfort,winter",
        "ingredients": [
            ("aardappel", 500, "g", "produce", "in blokjes"),
            ("prei", 2, "stuk", "produce", "in ringen"),
            ("vegetarische bouillon", 750, "ml", "pantry", ""),
            ("room", 100, "ml", "dairy", ""),
            ("peterselie", 10, "g", "produce", ""),
            ("peper", 1, "snuf", "pantry", ""),
            ("zout", 1, "snuf", "pantry", ""),
        ],
    },
]

STAPLES = [
    ("olijfolie", "pantry", "ml", None, 1, "olijfolie"),
    ("boter", "dairy", "g", 30, 1, "zuivel"),
    ("melk", "dairy", "ml", 7, 1, "zuivel"),
    ("zout", "pantry", "g", None, 1, "kruiden"),
    ("peper", "pantry", "g", None, 1, "kruiden"),
    ("bloem", "pantry", "g", None, 0, "bakproducten"),
    ("paprikapoeder", "pantry", "g", None, 1, "kruiden"),
    ("cumin", "pantry", "g", None, 1, "kruiden"),
]


def seed():
    init_db()
    print("Seeding ingredients...")
    ing_map = {}
    seen = set()
    for r in RECIPES:
        for (iname, _, unit, cat, _) in r["ingredients"]:
            key = iname.lower()
            if key in seen:
                continue
            seen.add(key)
            iid = add_ingredient(
                name=iname,
                category=cat,
                default_unit=unit,
                store_section=cat or "overig",
            )
            ing_map[key] = iid

    for name, cat, unit, shelf, staple, section in STAPLES:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        add_ingredient(name=name, category=cat, default_unit=unit, shelf_life_days=shelf, staple=staple, store_section=section)

    print("Seeding recipes...")
    recipe_ids = {"dinner": [], "lunch": []}
    for r in RECIPES:
        rid = add_recipe(
            name=r["name"],
            type_=r["type"],
            cuisine=r["cuisine"],
            prep_time=r["prep_time"],
            cook_time=r["cook_time"],
            servings=r["servings"],
            difficulty=r["difficulty"],
            tags=r["tags"],
        )
        recipe_ids[r["type"]].append(rid)
        for (iname, qty, unit, _, prep) in r["ingredients"]:
            iid = ing_map[iname.lower()]
            add_recipe_ingredient(rid, iid, qty, unit, prep)

    print(f"Seeded {len(recipe_ids['dinner'])} dinners, {len(recipe_ids['lunch'])} lunches.")

    print("Creating 12-week meal plan...")
    plan_id = create_plan("vdM Home — 12 Week Vegetarian Rotation")
    generate_12_week_plan(plan_id, recipe_ids["dinner"], recipe_ids["lunch"], strategy="rotation")
    print(f"Plan {plan_id} ready.")


if __name__ == "__main__":
    seed()
