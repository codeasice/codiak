import streamlit as st
import json
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import re

def load_json_file(file_path: str) -> Optional[Dict]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {file_path}: {str(e)}")
        return None

def save_json_file(file_path: str, data: Dict) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving {file_path}: {str(e)}")
        return False

def validate_ability_score(value: int) -> bool:
    """Validate that an ability score is within D&D 5e bounds."""
    return 1 <= value <= 30

def validate_hit_points(value: int) -> bool:
    """Validate hit points are reasonable."""
    return 1 <= value <= 1000

def validate_armor_class(value: int) -> bool:
    """Validate armor class is reasonable."""
    return 1 <= value <= 30

def get_ability_modifier(score: int) -> int:
    """Calculate ability modifier from ability score."""
    return (score - 10) // 2

def format_ability_modifier(score: int) -> str:
    """Format ability modifier with + or - sign."""
    modifier = get_ability_modifier(score)
    return f"+{modifier}" if modifier >= 0 else str(modifier)

def render_ability_scores_editor(ability_scores: Dict[str, int], key_prefix: str = ""):
    """Render ability scores editor with modifiers."""
    st.subheader("Ability Scores")

    col1, col2, col3 = st.columns(3)

    abilities = ["str", "dex", "con", "int", "wis", "cha"]
    ability_names = {
        "str": "Strength", "dex": "Dexterity", "con": "Constitution",
        "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"
    }

    for i, ability in enumerate(abilities):
        col = col1 if i < 2 else col2 if i < 4 else col3

        with col:
            current_value = ability_scores.get(ability, 10)
            new_value = st.number_input(
                f"{ability_names[ability]} ({ability.upper()})",
                min_value=1,
                max_value=30,
                value=current_value,
                key=f"{key_prefix}ability_{ability}"
            )

            if not validate_ability_score(new_value):
                st.error(f"Invalid {ability_names[ability]} score")

            modifier = format_ability_modifier(new_value)
            st.caption(f"Modifier: {modifier}")

            ability_scores[ability] = new_value

def render_hit_points_editor(hit_points: Dict[str, int], key_prefix: str = ""):
    """Render hit points editor."""
    st.subheader("Hit Points")

    col1, col2 = st.columns(2)

    with col1:
        max_hp = st.number_input(
            "Maximum Hit Points",
            min_value=1,
            max_value=1000,
            value=hit_points.get("max", 10),
            key=f"{key_prefix}max_hp"
        )

    with col2:
        current_hp = st.number_input(
            "Current Hit Points",
            min_value=0,
            max_value=max_hp,
            value=hit_points.get("current", max_hp),
            key=f"{key_prefix}current_hp"
        )

    hit_points["max"] = max_hp
    hit_points["current"] = current_hp

def render_armor_class_editor(armor_class: Dict[str, Any], key_prefix: str = ""):
    """Render armor class editor."""
    st.subheader("Armor Class")

    col1, col2 = st.columns(2)

    with col1:
        ac_value = st.number_input(
            "Armor Class Value",
            min_value=1,
            max_value=30,
            value=armor_class.get("value", 10),
            key=f"{key_prefix}ac_value"
        )

    with col2:
        ac_description = st.text_input(
            "Description (e.g., 'natural armor', 'leather armor')",
            value=armor_class.get("description", ""),
            key=f"{key_prefix}ac_description"
        )

    armor_class["value"] = ac_value
    armor_class["description"] = ac_description

def render_speed_editor(speed: Dict[str, Any], key_prefix: str = ""):
    """Render speed editor."""
    st.subheader("Speed")

    col1, col2, col3 = st.columns(3)

    with col1:
        walk_speed = st.number_input(
            "Walk Speed (ft.)",
            min_value=0,
            max_value=200,
            value=speed.get("walk", 30),
            key=f"{key_prefix}walk_speed"
        )

    with col2:
        fly_speed = st.number_input(
            "Fly Speed (ft.)",
            min_value=0,
            max_value=200,
            value=speed.get("fly", 0),
            key=f"{key_prefix}fly_speed"
        )

    with col3:
        swim_speed = st.number_input(
            "Swim Speed (ft.)",
            min_value=0,
            max_value=200,
            value=speed.get("swim", 0),
            key=f"{key_prefix}swim_speed"
        )

    speed["walk"] = walk_speed
    speed["fly"] = fly_speed
    speed["swim"] = swim_speed

def render_skills_editor(skills: Dict[str, bool], key_prefix: str = ""):
    """Render skills editor."""
    st.subheader("Skills")

    skill_categories = {
        "Strength": ["Athletics"],
        "Dexterity": ["Acrobatics", "Sleight of Hand", "Stealth"],
        "Intelligence": ["Arcana", "History", "Investigation", "Nature", "Religion"],
        "Wisdom": ["Animal Handling", "Insight", "Medicine", "Perception", "Survival"],
        "Charisma": ["Deception", "Intimidation", "Performance", "Persuasion"]
    }

    for category, skill_list in skill_categories.items():
        st.write(f"**{category} Skills:**")

        cols = st.columns(len(skill_list))
        for i, skill in enumerate(skill_list):
            with cols[i]:
                is_proficient = st.checkbox(
                    skill,
                    value=skills.get(skill, False),
                    key=f"{key_prefix}skill_{skill}"
                )
                skills[skill] = is_proficient

def render_saving_throws_editor(saving_throws: Dict[str, bool], key_prefix: str = ""):
    """Render saving throws editor."""
    st.subheader("Saving Throw Proficiencies")

    abilities = ["str", "dex", "con", "int", "wis", "cha"]
    ability_names = {
        "str": "Strength", "dex": "Dexterity", "con": "Constitution",
        "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"
    }

    cols = st.columns(3)
    for i, ability in enumerate(abilities):
        with cols[i % 3]:  # Use modulo to cycle through the 3 columns
            is_proficient = st.checkbox(
                ability_names[ability],
                value=saving_throws.get(ability, False),
                key=f"{key_prefix}saving_{ability}"
            )
            saving_throws[ability] = is_proficient

def render_languages_editor(languages: List[str], key_prefix: str = ""):
    """Render languages editor."""
    st.subheader("Languages")

    common_languages = [
        "Common", "Dwarvish", "Elvish", "Giant", "Gnomish", "Goblin", "Halfling",
        "Orc", "Abyssal", "Celestial", "Deep Speech", "Draconic", "Infernal",
        "Primordial", "Sylvan", "Undercommon"
    ]

    # Add custom languages
    custom_language = st.text_input(
        "Add Custom Language",
        key=f"{key_prefix}custom_language"
    )

    if custom_language and custom_language not in languages:
        languages.append(custom_language)

    # Display current languages with remove option
    if languages:
        st.write("**Current Languages:**")
        for i, language in enumerate(languages):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {language}")
            with col2:
                if st.button("Remove", key=f"{key_prefix}remove_lang_{i}"):
                    languages.remove(language)
                    st.rerun()

    # Add from common languages
    st.write("**Add Common Languages:**")
    cols = st.columns(4)
    for i, language in enumerate(common_languages):
        if language not in languages:
            with cols[i % 4]:
                if st.button(language, key=f"{key_prefix}add_lang_{i}"):
                    languages.append(language)
                    st.rerun()

def render_weapons_editor(weapons: List[Dict[str, Any]], key_prefix: str = ""):
    """Render weapons editor."""
    st.subheader("Weapons")

    if st.button("Add New Weapon", key=f"{key_prefix}add_weapon"):
        weapons.append({
            "name": "New Weapon",
            "damage": {"dice": {"sides": 6, "count": 1}, "type": "Bludgeoning"},
            "equipped": False,
            "properties": {}
        })
        st.rerun()

    for i, weapon in enumerate(weapons):
        with st.expander(f"Weapon: {weapon.get('name', 'Unnamed')}"):
            col1, col2 = st.columns(2)

            with col1:
                weapon["name"] = st.text_input(
                    "Weapon Name",
                    value=weapon.get("name", ""),
                    key=f"{key_prefix}weapon_name_{i}"
                )

                weapon["equipped"] = st.checkbox(
                    "Equipped",
                    value=weapon.get("equipped", False),
                    key=f"{key_prefix}weapon_equipped_{i}"
                )

            with col2:
                if st.button("Remove Weapon", key=f"{key_prefix}remove_weapon_{i}"):
                    weapons.pop(i)
                    st.rerun()

            # Damage dice - handle different weapon formats
            st.write("**Damage:**")

            # Ensure damage structure exists
            if "damage" not in weapon:
                weapon["damage"] = {}

            # Handle both damage.dice and damage_dice formats
            if "damage_dice" in weapon:
                # Convert damage_dice format to damage.dice format
                weapon["damage"]["dice"] = weapon.pop("damage_dice")

            damage = weapon["damage"]
            dice = damage.get("dice", {"sides": 6, "count": 1})

            col1, col2, col3 = st.columns(3)
            with col1:
                dice["count"] = st.number_input(
                    "Number of Dice",
                    min_value=1,
                    max_value=20,
                    value=dice.get("count", 1),
                    key=f"{key_prefix}weapon_dice_count_{i}"
                )

            with col2:
                dice["sides"] = st.number_input(
                    "Dice Sides",
                    min_value=2,
                    max_value=20,
                    value=dice.get("sides", 6),
                    key=f"{key_prefix}weapon_dice_sides_{i}"
                )

            with col3:
                damage["type"] = st.selectbox(
                    "Damage Type",
                    options=["Bludgeoning", "Piercing", "Slashing", "Fire", "Cold", "Lightning", "Thunder", "Acid", "Poison", "Radiant", "Necrotic", "Psychic", "Force"],
                    index=["Bludgeoning", "Piercing", "Slashing", "Fire", "Cold", "Lightning", "Thunder", "Acid", "Poison", "Radiant", "Necrotic", "Psychic", "Force"].index(damage.get("type", "Bludgeoning")),
                    key=f"{key_prefix}weapon_damage_type_{i}"
                )

            # Ensure the dice structure is properly set
            damage["dice"] = dice

def render_spells_editor(spells: List[Dict[str, Any]], key_prefix: str = ""):
    """Render spells editor."""
    st.subheader("Spells")

    if st.button("Add New Spell", key=f"{key_prefix}add_spell"):
        spells.append({
            "name": "New Spell",
            "level": "Cantrip",
            "casting_time": "1 Action",
            "range_area": "Self",
            "duration": "Instantaneous",
            "components": ["V", "S"]
        })
        st.rerun()

    for i, spell in enumerate(spells):
        with st.expander(f"Spell: {spell.get('name', 'Unnamed')}"):
            col1, col2 = st.columns(2)

            with col1:
                spell["name"] = st.text_input(
                    "Spell Name",
                    value=spell.get("name", ""),
                    key=f"{key_prefix}spell_name_{i}"
                )

                spell["level"] = st.selectbox(
                    "Spell Level",
                    options=["Cantrip", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"],
                    index=["Cantrip", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"].index(spell.get("level", "Cantrip")),
                    key=f"{key_prefix}spell_level_{i}"
                )

            with col2:
                spell["casting_time"] = st.text_input(
                    "Casting Time",
                    value=spell.get("casting_time", "1 Action"),
                    key=f"{key_prefix}spell_casting_time_{i}"
                )

                if st.button("Remove Spell", key=f"{key_prefix}remove_spell_{i}"):
                    spells.pop(i)
                    st.rerun()

            spell["range_area"] = st.text_input(
                "Range/Area",
                value=spell.get("range_area", "Self"),
                key=f"{key_prefix}spell_range_{i}"
            )

            spell["duration"] = st.text_input(
                "Duration",
                value=spell.get("duration", "Instantaneous"),
                key=f"{key_prefix}spell_duration_{i}"
            )

            spell["description"] = st.text_area(
                "Description",
                value=spell.get("description", ""),
                key=f"{key_prefix}spell_description_{i}"
            )

def render_monster_editor(monster_data: Dict[str, Any]):
    """Render monster-specific editor."""
    st.header("Monster Editor")

    # Basic info
    st.subheader("Basic Information")
    col1, col2, col3 = st.columns(3)

    with col1:
        monster_data["name"] = st.text_input("Name", value=monster_data.get("name", ""))
        monster_data["size"] = st.selectbox(
            "Size",
            options=["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"],
            index=["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"].index(monster_data.get("size", "Medium"))
        )

    with col2:
        monster_data["type"] = st.text_input("Type", value=monster_data.get("type", ""))
        monster_data["alignment"] = st.text_input("Alignment", value=monster_data.get("alignment", ""))

    with col3:
        monster_data["challenge_rating"] = st.number_input(
            "Challenge Rating",
            min_value=0.0,
            max_value=30.0,
            value=float(monster_data.get("challenge_rating", 1)),
            step=0.25
        )

    # Hit points
    if "hit_points" in monster_data:
        render_hit_points_editor(monster_data["hit_points"], "monster_")

    # Armor class
    if "armor_class" in monster_data:
        render_armor_class_editor(monster_data["armor_class"], "monster_")

    # Speed
    if "speed" in monster_data:
        render_speed_editor(monster_data["speed"], "monster_")

    # Ability scores
    if "ability_scores" in monster_data:
        render_ability_scores_editor(monster_data["ability_scores"], "monster_")

    # Saving throws
    if "saving_throws" in monster_data:
        render_saving_throws_editor(monster_data["saving_throws"], "monster_")

    # Skills
    if "properties" in monster_data:
        render_skills_editor(monster_data["properties"], "monster_")

    # Languages
    if "languages" in monster_data:
        render_languages_editor(monster_data["languages"], "monster_")

def render_character_editor(character_data: Dict[str, Any]):
    """Render character-specific editor."""
    st.header("Character Editor")

    # Basic info
    st.subheader("Basic Information")
    col1, col2, col3 = st.columns(3)

    with col1:
        character_data["name"] = st.text_input("Name", value=character_data.get("name", ""))
        if "player" in character_data:
            character_data["player"]["name"] = st.text_input(
                "Player Name",
                value=character_data["player"].get("name", ""),
                key="player_name"
            )

    with col2:
        if "race" in character_data:
            character_data["race"]["name"] = st.text_input(
                "Race",
                value=character_data["race"].get("name", ""),
                key="race_name"
            )
            character_data["race"]["subtype"] = st.text_input(
                "Subtype",
                value=character_data["race"].get("subtype", ""),
                key="race_subtype"
            )

    with col3:
        # Handle alignment case-insensitively
        alignment_options = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]
        current_alignment = character_data.get("alignment", "Neutral")

        # Find the correct index, handling case differences
        try:
            alignment_index = next(i for i, opt in enumerate(alignment_options)
                                 if opt.lower() == current_alignment.lower())
        except StopIteration:
            alignment_index = 4  # Default to "Neutral"

        character_data["alignment"] = st.selectbox(
            "Alignment",
            options=alignment_options,
            index=alignment_index
        )

    # Hit points
    if "hit_points" in character_data:
        render_hit_points_editor(character_data["hit_points"], "char_")

    # Armor class
    if "armor_class" in character_data:
        render_armor_class_editor(character_data["armor_class"], "char_")

    # Speed
    if "speed" in character_data:
        render_speed_editor(character_data["speed"], "char_")

    # Ability scores
    if "ability_scores" in character_data:
        render_ability_scores_editor(character_data["ability_scores"], "char_")

    # Skills
    if "skills" in character_data:
        render_skills_editor(character_data["skills"], "char_")

    # Saving throws
    if "saving_throws" in character_data:
        render_saving_throws_editor(character_data["saving_throws"], "char_")

    # Languages
    if "languages" in character_data:
        render_languages_editor(character_data["languages"], "char_")

    # Weapons
    if "weapons" in character_data:
        render_weapons_editor(character_data["weapons"], "char_")

    # Spells
    if "spells" in character_data:
        render_spells_editor(character_data["spells"], "char_")

def render():
    """Main render function for the D&D Character Editor."""
    # Do NOT include title/description here - the app handles this automatically

    # File selection
    st.sidebar.header("File Selection")
    file_options = {
        "Hero (hero.json)": "hero.json",
        "NPC (npc.json)": "npc.json",
        "Monster (monster.json)": "monster.json"
    }

    selected_file = st.sidebar.selectbox(
        "Select file to edit:",
        list(file_options.keys()),
        key="file_selector"
    )

    file_path = file_options[selected_file]

    # Load file
    data = load_json_file(file_path)
    if not data:
        st.error(f"Could not load {file_path}")
        return

    # Character management
    st.sidebar.header("Character Management")

    # Initialize variables
    characters_list = []
    current_character_index = 0

    # Show character info
    if characters_list:
        st.sidebar.info(f"📊 **{len(characters_list)} character(s)** in this file")

    # Determine if this is a single character or multiple characters
    is_multiple_characters = False

    if file_path == "monster.json":
        # Monster file already has multiple characters
        is_multiple_characters = True
        characters_list = data.get("monsters", [])
        if characters_list:
            current_character_index = st.sidebar.selectbox(
                "Select monster:",
                range(len(characters_list)),
                format_func=lambda x: characters_list[x].get("name", f"Monster {x+1}")
            )
    else:
        # For hero.json and npc.json, check if it's a single character or list
        if isinstance(data, list):
            # Multiple characters format
            is_multiple_characters = True
            characters_list = data
            if characters_list:
                current_character_index = st.sidebar.selectbox(
                    "Select character:",
                    range(len(characters_list)),
                    format_func=lambda x: characters_list[x].get("name", f"Character {x+1}")
                )
        else:
            # Single character format - convert to list for consistency
            is_multiple_characters = True
            characters_list = [data]
            current_character_index = 0

    # Add new character button
    if st.sidebar.button("➕ Add New Character"):
        new_character = {
            "name": "New Character",
            "player": {"name": ""},
            "race": {"name": "", "subtype": ""},
            "alignment": "Neutral",
            "speed": {"walk": 30},
            "hit_points": {"max": 10, "current": 10},
            "ability_scores": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "skills": {},
            "armor_class": {"value": 10, "description": ""},
            "saving_throws": {},
            "languages": ["Common"],
            "weapons": [],
            "spells": []
        }
        characters_list.append(new_character)
        current_character_index = len(characters_list) - 1
        st.rerun()

    # Get current character data
    if characters_list and current_character_index < len(characters_list):
        current_character = characters_list[current_character_index]
    else:
        st.error("No characters found in the selected file.")
        return

    # Character actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Delete Character", disabled=len(characters_list) <= 1):
            if len(characters_list) > 1:
                characters_list.pop(current_character_index)
                if current_character_index >= len(characters_list):
                    current_character_index = len(characters_list) - 1
                st.rerun()

    with col2:
        if st.button("📋 Duplicate Character"):
            import copy
            duplicated_character = copy.deepcopy(current_character)
            duplicated_character["name"] = f"{current_character['name']} (Copy)"
            characters_list.append(duplicated_character)
            current_character_index = len(characters_list) - 1
            st.rerun()

    # Handle different file structures
    if file_path == "monster.json":
        # Monster file has a different structure
        render_monster_editor(current_character)
    else:
        # Character files (hero.json, npc.json)
        render_character_editor(current_character)

    # Save button
    st.sidebar.header("Actions")
    if st.sidebar.button("💾 Save Changes"):
        # Update the data structure based on file type
        if file_path == "monster.json":
            data["monsters"] = characters_list
        else:
            # For hero.json and npc.json, save as single character if only one, otherwise as list
            if len(characters_list) == 1:
                data = characters_list[0]
            else:
                data = characters_list

        if save_json_file(file_path, data):
            st.sidebar.success("✅ Changes saved successfully!")
        else:
            st.sidebar.error("❌ Failed to save changes")

    # Export button
    if st.sidebar.button("📤 Export JSON"):
        export_data = current_character
        st.download_button(
            label="Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"{current_character.get('name', 'character')}_export.json",
            mime="application/json"
        )

    # Display current data
    st.sidebar.header("Current Data")
    if st.sidebar.checkbox("Show JSON"):
        st.json(current_character)

if __name__ == "__main__":
    render()