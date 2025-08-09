from enum import Enum, auto

item_templates = {
    "rfx":        {
      "name": "RFx",
      "type": "rfx",
      "description": "An RFX envelope.",
      "icon": "icons_set/icons_32/mail.png"
    },

    "healing_potion": {
      "name": "Healing Potion",
      "description": "A potion that restores a small amount of health.",
      "icon": "rpg/tiles1600.png", #3050 sword
      "type": "potion",
      "subType": "healing",
      "rarity": "common",
      "weight": 0.5,
      "usable": True,
      "fungible": False,
      "effects": [
        {
          "type": "heal",
          "amount": 50
        }
      ]
    },
    "meat": {
      "name": "Meat",
      "description": "Meat",
      "icon": "rpg/tiles1509.png", #3050 sword
      "type": "food",
      "rarity": "common",
      "weight": .5,
      "usable": False,
      "fungible": True
    },
    "fictional_coin": {
      "name": "Fictional Coin",
      "description": "Fictional Coin",
      "icon": "rpg/tiles1532.png", #3050 sword
      "type": "currency",
      "rarity": "common",
      "weight": .01,
      "usable": False,
      "fungible": True
      },
    "bronze_coin": {
      "name": "coin",
      "description": "Bronze Coin",
      "icon": "rpg/tiles1532.png", #3050 sword
      "type": "currency",
      "subType": "sword",
      "rarity": "common",
      "weight": .01,
      "usable": False,
      "fungible": False
      },
    "short_sword":{
      "name": "Short Sword",
      "description": "A sturdy sword made of iron.",
      "icon": "rpg/tiles3050.png",
      "type": "weapon",
      "rarity": "common",
      "weight": 2.0,
      "usable": False,
      "subType": "sword",
      "weaponClass": "melee",
      "damage": {
        "dice": {
          "sides": 6,
          "count": 1
          },
        "type": "Piercing",
        "properties": ["finesse", "light"]
      },
   },
    "badass_sword":{
      "name": "Badass Sword",
      "description": "Badass",
      "icon": "rpg/tiles3050.png",
      "type": "weapon",
      "rarity": "common",
      "weight": 1.0,
      "usable": False,
      "subType": "sword",
      "weaponClass": "melee",
      "damage": {
        "dice": {
          "sides": 20,
          "count": 2,
          "count": 1
          },
        "type": "Piercing",
        "properties": ["finesse", "light", "thrown"]
      },
   },
  "arrow":{
        "name": "Arrow",
        "type": "ammo",
        "subType": "arrow",
        "icon": "rpg/tiles652.png",
        "weight": 0.05,
        "attributes": {
          "length": "32 inches",
          "shaftMaterial": "Carbon fiber",
          "fletchingType": "Feather",
          "fletchingColor": "Red",
          "tipType": "Steel broadhead",
        },
        "performance": {
          "range": "Up to 300 yards",
          "precision": "High",
          "penetration": "Moderate to high"
        },
        "specialProperties": {
          "weatherResistance": "High",
          "suitableForHunting": True,
          "suitableForTargetPractice": True
        }
      },
  "longbow": {
      "name": "Longbow",
      "description": "A sturdy longbow capable of firing arrows over great distances",
      "icon": "rpg/tiles3060.png",
      "type": "weapon",
      "rarity": "uncommon",
      "weight": 2.0,
      "usable": True,
      "subType": "bow",
      "weaponClass": "ranged",
      "damage": {
          "dice": {
              "sides": 8,
              "count": 1
          },
          "type": "Piercing",
          "properties": ["two-handed", "long range"]
      },
      "range": {
          "normal": 150,
          "maximum": 320
      },
      "ammunition": "arrow"
  },
    "dagger":{
      "name": "Dagger",
      "description": "A dagger is a small, lightweight weapon with a pointed, typically double-edged blade. It is easy to conceal and quick to draw, making it a favored weapon for rogues and also a useful tool for adventurers of all kinds. Daggers can be thrown, making them versatile for both melee and ranged combat.",
      "icon": "rpg/tiles3050.png",
      "type": "weapon",
      "rarity": "common",
      "weight": 1.0,
      "usable": False,
      "subType": "dagger",
      "damage": {
        "dice": {
          "sides": 4,
          "count": 1
          },
        "type": "Piercing",
        "properties": ["finesse", "light", "thrown"]
      },
   },
    "leather_armor":{
      "name": "Leather Armor",
      "description": "This armor is made from tough but flexible leather. It is light and allows for considerable ease of movement, making it a popular choice among rogues, rangers, and some spellcasters. While it offers less protection than metal armors, it is more discreet and less cumbersome, which can be beneficial for tasks requiring stealth and agility.",
      "icon": "rpg/tiles1367.png",
      "type": "armor",
      "rarity": "common",
      "weight": 10.0,
      "usable": False,
      "armor_class": {
        "value": 11,
        "description": "leather armor"
      }
   },
     "armor_of_invulnerability":{
      "name": "Armor of Invulnerability",
      "description": "This armor is made from tough but flexible leather. It is light and allows for considerable ease of movement, making it a popular choice among rogues, rangers, and some spellcasters. While it offers less protection than metal armors, it is more discreet and less cumbersome, which can be beneficial for tasks requiring stealth and agility.",
      "icon": "rpg/tiles1367.png",
      "type": "armor",
      "rarity": "common",
      "weight": 10.0,
      "usable": False,
      "armor_class": {
        "value": 18,
        "description": "leather armor"
      }
   },}


class ItemProperty(Enum):
    NAME = 'name'
    ITEM_TYPE = 'item_type'
    EFFECT_TYPE = 'effect_type'
    EFFECT_VALUE = 'effect_value'
    TEMPLATE = 'template'

DEFAULT_ITEM_TYPE = "unknown_type"

class EffectType(Enum):
    HEAL = auto()
    DAMAGE = auto()

class ItemType (Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    AMMO = "ammo"

# Maybe replacing with item_templates
ITEM_TYPES_OLD = {
  "items": [
     {
      "name": "Healing Potion",
      "description": "A potion that restores a small amount of health.",
      "icon": "healing_potion_icon.png",
      "type": "potion",
      "subType": "healing",
      "rarity": "common",
      "value": 50,
      "weight": 0.5,
      "usable": True,
      "effects": [
        {
          "type": "heal",
          "amount": 50
        }
      ]
    },
    {
      "name": "coin",
      "description": "Bronze Coin",
      "icon": "coin.png",
      "type": "currency",
      "subType": "sword",
      "rarity": "common",
      "value": 1,
      "weight": .01,
      "usable": False
    },
    {
      "type": "armor",
      "description": "A prestigious medal.",
      "icon": "assets/icons_set/icons_32/question.png"
    },
    {
      "type": "arrow",
      "description": "A prestigious medal.",
      "icon": "assets/icons_set/icons_32/question.png"
    },
     {
      "name": "Iron Sword",
      "description": "A sturdy sword made of iron.",
      "icon": "iron_sword_icon.png",
      "type": "weapon",
      "subType": "sword",
      "rarity": "common",
      "value": 100,
      "weight": 3.0,
      "usable": False
    },
    {
      "type": "medal",
      "description": "A prestigious medal.",
      "icon": "assets/icons_set/icons_32/medal.png"
    },
    {
      "type": "dollar_sign",
      "description": "A dollar sign symbol.",
      "icon": "assets/icons_set/icons_32/dollar.png"
    },
    {
      "type": "award",
      "description": "An award trophy.",
      "icon": "assets/icons_set/icons_32/trophy.png"
    },
    {
      "type": "award_signed",
      "description": "A signed award trophy.",
      "icon": "assets/icons_set/icons_32/trophy.png"
    },
    {
      "type": "certificate",
      "description": "A certificate.",
      "icon": "assets/icons_set/icons_32/medal.png"
    },
    {
      "type": "shopping_cart",
      "description": "A shopping cart icon.",
      "icon": "assets/icons_set/icons_32/energy.png"
    },
    {
      "type": "submission",
      "description": "A submission envelope.",
      "icon": "assets/icons_set/icons_32/mail.png"
    },
    {
      "type": "bid_eval",
      "description": "A podium for bid evaluation.",
      "icon": "assets/icons_set/icons_32/podium.png"
    },
    {
      "type": "contract",
      "description": "A contract medal.",
      "icon": "assets/icons_set/icons_32/frilly_medal.png"
    },
    {
      "type": "contract_draft",
      "description": "A draft contract medal.",
      "icon": "assets/icons_set/icons_32/frilly_medal.png"
    },
    {
      "type": "requisition",
      "description": "A requisition document.",
      "icon": "assets/MDF/icons/requisition.png"
    },
    {
      "type": "approval",
      "description": "An approval document.",
      "icon": "assets/MDF/icons/approval.png"
    },
    {
      "type": "po",
      "description": "A purchase order document.",
      "icon": "assets/MDF/icons/po.png"
    },
    {
      "type": "receipt",
      "description": "A receipt document.",
      "icon": "assets/MDF/icons/receipt.png"
    },
    {
      "type": "performance",
      "description": "A performance document.",
      "icon": "assets/MDF/icons/performance.png"
    },
    {
      "type": "invoice",
      "description": "An invoice document.",
      "icon": "assets/MDF/icons/invoice.png"
    },
    {
      "type": "reconcile",
      "description": "A reconciliation document.",
      "icon": "assets/MDF/icons/reconcile.png"
    },
    {
      "type": "pay",
      "description": "A payment document.",
      "icon": "assets/MDF/icons/pay.png"
    },
    {
      "type": "find_contracts",
      "description": "Search for contracts.",
      "icon": "assets/MDF/icons/find_contracts.png"
    },
    {
      "type": "shop_items",
      "description": "Shop for items.",
      "icon": "assets/MDF/icons/shop_items.png"
    },
    {
      "type": "punchouts",
      "description": "Punchouts.",
      "icon": "assets/MDF/icons/punchouts.png"
    },
    {
      "type": "epro_registration",
      "description": "E-procurement registration.",
      "icon": "assets/MDF/icons/register.png"
    },
    {
      "type": "s2g_registration",
      "description": "S2G registration.",
      "icon": "assets/MDF/icons/register.png"
    },
    {
      "type": "source_registration",
      "description": "Source registration.",
      "icon": "MDF/icons/register.png"
    },
    {
      "type": "epro_rfx",
      "description": "E-procurement RFX.",
      "icon": "assets/icons_set/icons_32/mail.png"
    },
    {
      "type": "source_rfx",
      "description": "Source RFX.",
      "icon": "assets/icons_set/icons_32/mail.png"
    },
    {
      "type": "s2g_rfx",
      "description": "S2G RFX.",
      "icon": "assets/icons_set/icons_32/mail.png"
    }
  ]
}

RESOURCE_TYPES_JSON = {
  "resources": [
    {
      "name": "Food",
      "description": "Nourishing sustenance for your character.",
      "icon": "food_icon.png",
      "max_quantity": 1000,
      "family": "Consumables",
      "tags": ["edible", "consumable"]
    },
    {
      "name": "Wood",
      "description": "A versatile building material.",
      "icon": "wood_icon.png",
      "max_quantity": 800,
      "family": "Materials",
      "tags": ["construction", "crafting"]
    },
    {
      "name": "Gold",
      "description": "Shiny and valuable currency.",
      "icon": "gold_icon.png",
      "max_quantity": 10000,
      "family": "Currency",
      "tags": ["currency", "valuable"]
    },
    {
      "name": "Iron Ore",
      "description": "Raw iron for crafting weapons and armor.",
      "icon": "iron_ore_icon.png",
      "max_quantity": 500,
      "family": "Materials",
      "tags": ["mining", "crafting"]
    },
    {
      "name": "Healing Herb",
      "description": "A medicinal herb used for healing potions.",
      "icon": "healing_herb_icon.png",
      "max_quantity": 200,
      "family": "Consumables",
      "tags": ["healing", "consumable"]
    }  ],
  "resourceFamilies": [
    {
      "name": "Consumables",
      "description": "Resources that can be consumed or used for healing and buffs."
    },
    {
      "name": "Materials",
      "description": "Resources used for crafting and construction."
    },
    {
      "name": "Currency",
      "description": "Various forms of in-game currency."
    }]}

