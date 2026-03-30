

from __future__ import annotations

import json, math, os, random, re, sys, time, urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageOps, ImageTk
    PIL_AVAILABLE = True
except Exception:
    Image = ImageTk = ImageOps = None
    PIL_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class Theme:
    BG_DEEP    = "#0a0c10"
    BG         = "#10131a"
    BG_CARD    = "#171c26"
    BG_INSET   = "#0d1018"
    BG_HOVER   = "#1e2433"

    BORDER     = "#2a3040"
    BORDER_LT  = "#353d50"
    RULE       = "#1e2430"

    TEXT       = "#d4c5a0"
    TEXT_DIM   = "#8a7e66"
    TEXT_BRIGHT= "#f0e6cc"
    TEXT_DARK  = "#0a0c10"

    GOLD       = "#c8a44e"
    GOLD_LT    = "#e0c06a"
    GOLD_DK    = "#8a7030"

    RED        = "#8c3838"
    RED_LT     = "#a84848"
    RED_DK     = "#5c2020"

    BLUE       = "#5090c8"
    BLUE_LT    = "#70b0e0"

    SILVER     = "#8898a8"   # dull white - healing spells accent
    SILVER_LT  = "#b0c2ce"   # light silver for headers/labels
    SILVER_DK  = "#4a5868"   # dark silver for frame borders
    GREEN      = "#50a870"
    GREEN_LT   = "#70c890"
    PURPLE     = "#8060b0"
    PURPLE_LT  = "#a080d0"
    WHITE      = "#ffffff"

    DESENS_LT  = "#6abcd8"

    BLOOD      = "#9c2020"
    BLOOD_LT   = "#c03030"
    BLOOD_DK   = "#5a1010"

    WOUND_MIN    = "#4a8878"   
    WOUND_MIN_DK = "#2a5050"

    STAGE_1    = "#50a870"
    STAGE_2    = "#c8a44e"
    STAGE_3    = "#d08040"
    STAGE_4    = "#c44040"

    M_STABLE   = "#3a5a70"
    M_SHORT    = "#c8a44e"
    M_LONG     = "#c07838"
    M_INDEF    = "#8c3838"
    M_ZERO     = "#2a0808"

    FONT_FAMILY = "Segoe UI"
    FONT_UI     = "Segoe UI"
    F_TITLE     = (FONT_FAMILY, 18, "bold")
    F_SECTION   = (FONT_FAMILY, 13, "bold")
    F_BODY      = (FONT_UI, 10)
    F_BODY_B    = (FONT_UI, 10, "bold")
    F_SMALL     = (FONT_UI, 9)
    F_SMALL_B   = (FONT_UI, 9, "bold")
    F_TINY      = (FONT_UI, 8)
    F_BIG_NUM   = (FONT_FAMILY, 24, "bold")
    F_MED_NUM   = (FONT_FAMILY, 16, "bold")

    PAD        = 14
    PAD_SM     = 8
    CARD_BD    = 1

T = Theme

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

APP_TITLE = "Sanity, Fear & Madness"
APP_MIN_SIZE = (1200, 800)
APP_DEFAULT_SIZE = "1440x960"
CREDITS = "Created by _Chimpman"

WIS_MIN, WIS_MAX = 1, 30
CON_MIN, CON_MAX = 1, 30
SANITY_BASE = 15
MAX_FEAR_STAGE = 4
D4_SIDES = 4
UNDO_STACK_LIMIT = 50
MAX_EXHAUSTION = 6

EXHAUSTION_EFFECTS: Dict[int, str] = {
    1: "Disadvantage on ability checks",
    2: "Speed halved",
    3: "Disadvantage on attack rolls and saving throws",
    4: "Hit point maximum halved",
    5: "Speed reduced to 0",
    6: "Death",
}

OPENMOJI_SKULL_URL = (
    "https://raw.githubusercontent.com/hfg-gmuend/openmoji"
    "/master/color/618x618/2620.png"
)
OPENMOJI_SWORDS_URL = (
    "https://raw.githubusercontent.com/hfg-gmuend/openmoji"
    "/master/color/618x618/2694.png"
)
OPENMOJI_BLOOD_URL = (
    "https://raw.githubusercontent.com/hfg-gmuend/openmoji"
    "/master/color/618x618/1FA78.png"
)

SAVE_FOLDER_NAME = "SanityFearMadnessTrackerAppData"
SAVE_FILE_NAME = "save_v6.json"

THRESHOLDS: List[Tuple[str, float, str]] = [
    ("Crossed below 75%", 0.75, "short"),
    ("Crossed below 50%", 0.50, "long"),
    ("Crossed below 25%", 0.25, "indefinite"),
    ("Reached 0 - DM controls character", 0.00, "zero"),
]

SIMPLE_FEAR_POOL: List[str] = [
    "Heights", "Spiders", "Numbers", "Food", "Confined Spaces",
    "Madness", "Night", "Sleep", "Blood", "The Dark", "The Mists",
    "Wolves", "Graveyards", "Mirrors", "Dolls", "Bells", "Storms",
    "Empty Houses", "Being Watched", "Fire", "Water", "Snakes",
    "Silence", "Crowds", "Being Alone", "Thunder", "Fog",
]

# ═══════════════════════════════════════════════════════════════════════════
# MADNESS TABLES
# ═══════════════════════════════════════════════════════════════════════════

SHORT_TERM_MADNESS_TABLE: List[Tuple[str, str, str]] = [
    ("D20-1",  "Black Out",             "The afflicted's vision gutters out, and they collapse. They fall unconscious, but do not lose hit points and are stable. Another creature can use an action to shake them awake, ending the effect."),
    ("D20-2",  "Tell-Tale Heart",       "The afflicted hears a loud, relentless heartbeat drowning out all other sound. They are deafened, and have disadvantage on attack rolls made against creatures behind them."),
    ("D20-3",  "Pyric Delusion",        "The afflicted is certain their clothes and gear are burning their skin. On their turn, they use their action to doff their clothing and armour down to underclothes, believing it is the source of the pain. They refuse to don the removed clothing or armour until the madness ends."),
    ("D20-4",  "Tremors",               "The afflicted develops uncontrollable tremors and tics that ruin precision and leverage. They have disadvantage on Strength and Dexterity ability checks, and disadvantage on attack rolls."),
    ("D20-5",  "Pica",                  "The afflicted is seized by an overpowering craving to eat something unnatural - dirt, slime, wax, hair, or worse. If such a substance is within reach, they must use their action to consume it (or try to), unless physically prevented."),
    ("D20-6",  "Formication",           "The afflicted feels insects crawling beneath their skin, scratching and tunnelling. At the end of each of their turns in which they did not take damage, they take 1d4 slashing damage as they claw at themself to dig the 'bugs' out. This continues until the madness ends or until they have lost half of their current hit points (from the moment the madness began) from this effect."),
    ("D20-7",  "Separation Anxiety",    "The afflicted becomes convinced they will die if left alone. Choose a random ally the afflicted can see when the madness begins. The afflicted is compelled to remain within 5 feet of that ally. While farther than 5 feet from that ally, the afflicted has disadvantage on all rolls."),
    ("D20-8",  "Fear",                  "The afflicted's mind latches onto a nearby omen of doom. The DM chooses a nearby trigger. The afflicted becomes frightened of that trigger. Add that trigger to the afflicted's Fear List."),
    ("D20-9",  "Safe Space",            "The afflicted fixates on a 15-foot by 15-foot area as the only place they can survive. They believe they will die if they leave it. They become fiercely territorial: if another creature enters the area, the afflicted attacks any creature in the area (prioritizing those who entered the 'safe zone')."),
    ("D20-10", "Frenzied",              "The afflicted froths at the mouth as panic and violence take over reason. Each round, they must use their action to attack the nearest creature."),
    ("D20-11", "Babbling",              "The afflicted's thoughts spill out in tangled, feverish nonsense. They are incapable of normal speech and cannot form the focus needed for magic. They cannot speak coherently or cast spells."),
    ("D20-12", "Hysterical Weeping",    "The afflicted begins uncontrollably weeping - shaking breaths, blurred vision, tears they cannot stop - yet can otherwise act normally. They have disadvantage on Perception checks that rely on sight."),
    ("D20-13", "No Truce with the Furies", "The afflicted is convinced unseen adversaries are chasing them. They cannot end their turn within 20 feet of where they began it. If they would end their turn within 20 feet of where they began, they must use their reaction (if available) to move until they end their turn outside that boundary."),
    ("D20-14", "Phantom Infant",        "The afflicted becomes absolutely convinced they are holding a baby in their off-hand. If they were holding something in that hand, they drop it as the 'baby' takes its place. They behave as though that hand is occupied for the duration."),
    ("D20-15", "Gold Purge",            "The afflicted becomes convinced their gold is trying to kill them. While affected, they must use their bonus action each turn to remove 1d20 gp from wherever they store it and throw it on the ground."),
    ("D20-16", "Hallucinations",        "The afflicted experiences vivid hallucinations - faces in fog, movement at the edge of vision, whispers in another voice. They have disadvantage on ability checks."),
    ("D20-17", "Startled",              "The afflicted is wound so tight that any sudden movement snaps their body into reflex. Whenever a creature moves within 5 feet of the afflicted, they must succeed on a DC 10 Dexterity saving throw or drop what they're holding as a reaction (if they have one). On a failed save, their speed becomes 0 until the start of their next turn."),
    ("D20-18", "Hypersensitive",        "Every wound affects not only the body but the mind. Whenever the afflicted takes damage, they take 1 additional psychic damage per die rolled as part of that damage."),
    ("D20-19", "Emotional Numbness",    "The afflicted goes cold inside. They are immune to being charmed, but they have disadvantage on Charisma ability checks."),
    ("D20-20", "Adrenaline",            "The afflicted becomes suffused with adrenaline. They gain advantage on all attack rolls. When the madness ends, they gain 1 level of exhaustion."),
]

LONG_TERM_MADNESS_TABLE: List[Tuple[str, str, str]] = [
    ("D20-1",  "Object Deification",    "The afflicted becomes convinced an object they can see is a god. They must keep it in their possession at all times. Before making any meaningful decision (attacks, spell targets, skill checks, movement choices), they must consult the object aloud. If they do not, they have disadvantage on the roll."),
    ("D20-2",  "Yellow Wallpaper",      "Patterns crawl and shift in walls and floors, revealing imagined figures watching from within. The afflicted has disadvantage on Investigation checks. The first time each combat they target a creature, they roll a d6; on a 1-3, they instead target an illusory space and automatically miss."),
    ("D20-3",  "Verbal Disinhibition",  "The afflicted verbalizes their internal thoughts unless they make a concerted effort not to. While suppressing this, they have disadvantage on skill checks and saving throws, cannot cast concentration spells, and speak in strained, broken sentences."),
    ("D20-4",  "Identity Delusion",     "The afflicted adopts the personality of another character or NPC the DM decides, and fully believes they are that person. They speak, react, and make choices as that identity would, including using names and memories that aren't theirs."),
    ("D20-5",  "Insomnia",              "Sleep refuses to hold the afflicted, and night terrors plague the mind. After a long rest, they must succeed on a DC 13 Constitution saving throw. On a failure, they still gain the long rest, but gain 1 level of exhaustion and regain only half their hit dice."),
    ("D20-6",  "Hypervigilant",         "The afflicted's nerves never stop scanning; every creak is a threat, every shadow a knife. They cannot be surprised, but they have disadvantage on Stealth checks."),
    ("D20-7",  "Shared Suffering",      "The afflicted feels pain they witness as if it is their own. Any damage dealt to any creature within 15 feet of the afflicted is halved, and the afflicted takes the other half as non-lethal psychic damage."),
    ("D20-8",  "Amnesia",               "The afflicted remembers who they are and retains racial traits and class features, but they do not recognize other people or remember anything that happened before the madness took hold."),
    ("D20-9",  "Potion Delusion",       "The afflicted clings to a powerful delusion that they drank an alchemical draught. The DM chooses a potion. The afflicted imagines they are under its effects and behaves accordingly."),
    ("D20-10", "Kleptomania",           "The afflicted has an itch in the hands and a hunger in the eyes. They feel compelled to steal, even when doing so is foolish, impossible, or dangerous. They repeatedly attempt to take objects when an opportunity presents itself."),
    ("D20-11", "Flowers for Algernon",  "The afflicted's mind blooms and then collapses. For the first half of the duration, they have advantage on Intelligence ability checks and advantage on Intelligence saving throws. For the remaining duration, they have disadvantage on Intelligence ability checks and disadvantage on Intelligence saving throws."),
    ("D20-12", "Derealization",         "The world feels distant and unreal, as though the afflicted is walking through a dream. They have resistance to psychic damage. Whenever they roll a d20, on an odd result they resolve the roll normally, but are stunned until the end of their next turn."),
    ("D20-13", "Depersonalization",     "The afflicted no longer believes they exist in the way others do. They think others cannot truly notice, perceive, or interact with them. Whenever they roll a d20, on an even result, until the end of their next turn they cannot willingly target themself with attacks, abilities, or effects."),
    ("D20-14", "Confused",              "The afflicted's thoughts scatter like frightened birds. Whenever they take damage, they must succeed on a DC 13 Wisdom saving throw or be affected as though they failed a saving throw against the confusion spell. The confusion effect lasts for 1 minute."),
    ("D20-15", "Hyperreactive Terror",  "Fear breeds fear. Whenever the afflicted becomes frightened, they immediately gain another fear determined by the DM."),
    ("D20-16", "The Grand Conspiracy",  "The afflicted becomes certain that every event and every person is part of Strahd's design; nothing is coincidence. They have advantage on Investigation and Perception checks, and disadvantage on all other ability checks."),
    ("D20-17", "Tunnel Vision",         "The afflicted's sight narrows into a single harsh beam. They can only see clearly in a 30-foot line directly ahead. Creatures outside this line have advantage on attack rolls against the afflicted. The afflicted gains a +2 bonus to ranged attack rolls against targets directly in front of them."),
    ("D20-18", "Tourettes",             "The afflicted develops involuntary tics and vocalizations. Whenever they roll a d20, on an even result their speed becomes 0 until the start of their next turn."),
    ("D20-19", "Paranoia",              "The afflicted's trust rots away. They become highly distrustful of others. They have disadvantage on Insight checks, and if they fail an Insight check they always assume the other creature is lying."),
    ("D20-20", "Unbreakable",           "Something inside the afflicted has calcified into iron. Once per long rest, when they would be reduced to 0 hit points but not killed outright, they instead drop to 1 hit point and remain standing. When this triggers, they gain 1 level of exhaustion."),
]

INDEFINITE_MADNESS_TABLE: List[Tuple[str, str, str]] = [
    ("D20-1",  "Out, Damned Spot!",              "The afflicted is convinced their hands are stained with blood no one else can see. They must spend every short rest attempting to wash their hands and gain no benefits from that short rest. Alternatively, they may suppress the compulsion and gain the benefits of the short rest, but they must immediately increase all entries on their Fear List by one stage."),
    ("D20-2",  "Inferiority Complex",             "The afflicted is consumed by the certainty that they are inadequate and will be exposed. They have disadvantage on ability checks using skills they are proficient in."),
    ("D20-3",  "Apathy",                          "The afflicted has lost interest in something they once cared about deeply; the spark simply isn't there anymore. They are no longer proficient in a skill of the DM's choice."),
    ("D20-4",  "Personality Split",               "The afflicted fractures into multiple distinct selves. They gain a new personality and believe it is a separate person who has always been that way since birth. After each long rest, roll a d20. On a result of 9 or lower, the new personality is dominant. On a result of 10 or higher, the original personality is dominant."),
    ("D20-5",  "Nihilism",                        "Nothing is real; the afflicted believes there is no inherent meaning, value, or purpose in life. They cannot benefit from Hope, Inspiration, Bardic Inspiration, guidance, bless, heroism, or any other morale or hope bonuses or spells."),
    ("D20-6",  "Despair",                         "Something in the afflicted breaks and does not cleanly mend. Roll a d6 (1=STR, 2=DEX, 3=CON, 4=INT, 5=WIS, 6=CHA). The rolled ability score is permanently reduced by 1."),
    ("D20-7",  "Homicidal",                       "The afflicted develops a need to kill. They must make a DC 15 Wisdom saving throw at the end of each 24-hour period. On a success, they suppress the urge for another 24 hours. On a failure, they become fixated on killing a creature the DM decides. They have disadvantage on all rolls until they kill that creature. If they cannot reach it within 24 hours, they gain 1 level of exhaustion."),
    ("D20-8",  "Relentless Exhaustion",           "The afflicted's body never truly recovers from the mental strain. They permanently have 1 level of exhaustion."),
    ("D20-9",  "Demoralizing Aura",               "The afflicted becomes unpleasant to be around; people recoil without knowing why. Allies within 10 feet of the afflicted take a −1 penalty to all dice rolls."),
    ("D20-10", "Whom the Gods Would Destroy",     "The afflicted mind is broken; they are in a perpetual state of madness. They can no longer rise above 75% of their sanity, and they permanently have a short-term madness effect active."),
    ("D20-11", "Masochist",                       "The afflicted seeks pain as proof they are still real. Each day, they cause themself harm and inflict a minor injury (as determined by the DM)."),
    ("D20-12", "Dead Soul",                       "Something inside has gone, as if the afflicted's spirit refuses to knit back together. Magical healing restores only half the normal number of hit points to them."),
    ("D20-13", "Age Regression",                  "The afflicted reverts backward into childhood. Their mannerisms change; their voice, posture, and personality shift to reflect a younger self. They behave as a young child would, responding to situations as they once did in earlier life."),
    ("D20-14", "Suicidal Ideation",               "The afflicted is haunted by a persistent desire to die. When they reach 0 hit points, they automatically fail all death saving throws."),
    ("D20-15", "Death Dread",                     "The afflicted is deathly afraid to die. When reduced below half their hit points, they become frightened of all hostile creatures until the end of their next turn. They have disadvantage on death saving throws. Add Death to their Fear List."),
    ("D20-16", "Self-Sabotage",                   "The afflicted cannot bear the weight of success and will always try to stop themselves from succeeding. Whenever they roll a natural 20, they must reroll it."),
    ("D20-17", "The Metamorphosis",               "The afflicted is convinced their body is no longer their own - something chitinous, crawling, and shameful has replaced it. They believe they are a bug. Their speed is halved, and they have disadvantage on Charisma checks. When they are hit, they must succeed on a DC 15 Wisdom saving throw or fall prone."),
    ("D20-18", "Martyr",                          "The afflicted believes suffering makes them virtuous, and that their pain redeems others. When they could avoid damage with a reaction, they must succeed on a DC 15 Wisdom saving throw or choose not to use it. When a party member within 30 feet would be reduced to 0 hit points, the afflicted uses a free action to prevent that damage entirely, but they immediately fall unconscious."),
    ("D20-19", "Corruption",                      "The afflicted's will bends toward the vampire, and they desire to become one. Whenever they see a vampire, they are automatically charmed by it for 1 minute. They have disadvantage on saving throws to resist a vampire's attempts to turn them."),
    ("D20-20", "Fearless",                        "The afflicted does not fear. Fear is the mind-killer. Fear is the little-death that brings total obliteration. The afflicted will face their fear. They will permit it to pass over them and through them. And when it has gone past, they will turn the inner eye to see its path. Where the fear has gone there will be nothing. Only they will remain. They are immune to being frightened. The Fear system no longer applies to them: they cannot gain new fears, and all entries on their Fear List are permanently erased"),
]

# ═══════════════════════════════════════════════════════════════════════════
# WOUND TABLES
# ═══════════════════════════════════════════════════════════════════════════

MINOR_WOUND_TABLE: List[Tuple[int, str, str]] = [
    (1,  "Shell Shocked",
         "The afflicted has been violently rattled by trauma, their senses overwhelmed and their judgment clouded. "
         "They have disadvantage on Wisdom-based checks, saving throws, and attack rolls."),
    (2,  "Concussed",
         "A heavy blow to the head leaves the afflicted dazed and struggling to think clearly. "
         "They have disadvantage on Intelligence-based checks, saving throws, and attack rolls."),
    (3,  "Ringing Blow",
         "A sharp strike to the head leaves the afflicted's ears ringing and their hearing distorted. "
         "They are temporarily Deafened."),
    (4,  "Hobbled",
         "The afflicted's leg is injured, forcing them to limp and shift their weight painfully. "
         "Their speed is reduced by 10 feet."),
    (5,  "Blood Loss",
         "The afflicted is bleeding internally or externally, their strength steadily draining from the wound. "
         "Reduce their maximum hit points by 2d6."),
    (6,  "Infected Injury",
         "The afflicted's wound festers with sickness and inflammation, weakening their resilience. "
         "They gain the Poisoned condition."),
    (7,  "Broken Bone",
         "A fracture splinters beneath the afflicted's skin, making forceful movement agonizing. "
         "They have disadvantage on Strength-based checks, saving throws, and attack rolls."),
    (8,  "Internal Injuries",
         "The blow has caused the afflicted deep internal damage, making every breath and movement painful. "
         "They have disadvantage on Constitution-based checks and saving throws."),
    (9,  "Blurred Vision",
         "The afflicted's vision swims with pain and disorientation. "
         "They are temporarily Blinded."),
    (10, "Minor Scar",
         "The wound leaves a visible mark on the afflicted, altering how others perceive them. "
         "They have disadvantage on Charisma-based skill checks, except Intimidation, which they make with advantage."),
    (11, "Staggered",
         "Pain and imbalance disrupt the afflicted's coordination in the heat of battle. "
         "They cannot take Bonus Actions."),
    (12, "Whiplash",
         "The afflicted's neck and head snap violently, leaving their senses unfocused. "
         "They suffer \u22125 to Perception checks and Passive Perception."),
    (13, "Nerve Damage",
         "Trauma to the afflicted's nervous system dulls their reflexes. "
         "They cannot take reactions."),
    (14, "Muscle Spasms",
         "The afflicted's muscles twitch and seize unpredictably, disrupting their movements. "
         "They have disadvantage on Dexterity-based checks, saving throws, and attack rolls."),
    (15, "Unsteady",
         "The afflicted's footing falters and their balance is compromised. "
         "They have disadvantage on Initiative rolls."),
    (16, "Chronic Pain",
         "Lingering agony from the afflicted's injury saps their energy and focus. "
         "They gain one level of exhaustion."),
    (17, "Arm Injury",
         "An injury renders one of the afflicted's arms unusable and painfully stiff. "
         "The limb is rendered useless."),
    (18, "Shaken",
         "The afflicted's confidence falters and their presence weakens. "
         "They have disadvantage on Charisma-based checks, saving throws, and attack rolls."),
    (19, "Off Balance",
         "The afflicted's posture and stance are thrown off by injury, leaving them exposed. "
         "They suffer \u22121 to AC until a Long Rest."),
    (20, "Seared Synapses",
         "The strike fried something inside the afflicted, they smell burning toast. "
         "It left their synapses misfiring and pain signals no longer register correctly. "
         "They gain resistance to bludgeoning, piercing, and slashing damage from non-magical attacks."),
]

MAJOR_WOUND_TABLE: List[Tuple[int, str, str]] = [
    (1,  "Mortal Wound",
         "A catastrophic blow tears through a vital organ, and death closes in fast. The afflicted suffers a mortal wound, "
         "such as a slashed jugular or punctured lung, and will quickly perish. Unless they are stabilized by an ally "
         "(DC 15 Medicine check) or receive magical healing, they bleed out and die within 3 rounds, automatically "
         "failing their death saving throws."),
    (2,  "Lose an Eye",
         "A brutal strike destroys one of the afflicted's eyes in a flash of blood and darkness. "
         "(Roll a d20, Even = Right, Odd = Left). The afflicted has disadvantage on Wisdom (Perception) checks that rely "
         "on sight and on ranged attack rolls. Magic such as Major Restoration can restore the lost eye. If they have no "
         "eyes left after sustaining this injury, they are blinded."),
    (3,  "Lose Both Eyes",
         "The world goes black as both eyes are ruined beyond saving. The afflicted is blinded. Magic such as Major "
         "Restoration can restore one lost eye; if this happens, change the effect to Lose an Eye."),
    (4,  "Lose Fingers",
         "A savage attack shears away several fingers. The afflicted loses 1d3 fingers on one hand (Roll a d20, "
         "Even = Right, Odd = Left), and they have disadvantage on checks involving items held by that hand. "
         "Magic such as Major Restoration can restore the fingers."),
    (5,  "Lose Hand",
         "Their hand is severed in a sudden, irreversible stroke. The afflicted loses a hand (Roll a d20, "
         "Even = Right, Odd = Left). They can no longer hold anything with two hands and can only hold a single object "
         "at a time. Magic such as Major Restoration can restore the hand."),
    (6,  "Lose Arm",
         "The limb is violently removed, leaving the afflicted maimed and off-balance. The afflicted loses an arm "
         "(Roll a d20, Even = Right, Odd = Left). They can no longer hold anything with two hands, can only hold a "
         "single object at a time, and they have disadvantage on Strength checks. "
         "Magic such as Major Restoration can restore the arm."),
    (7,  "Lame",
         "A shattered joint or torn tendon leaves one leg permanently weakened. (Roll a d20, Even = Right Leg, "
         "Odd = Left Leg). The afflicted's speed is reduced by 10 feet. They must make a DC 15 Dexterity saving throw "
         "after using the Dash action or fall prone."),
    (8,  "Lose a Foot",
         "A devastating injury removes the afflicted's foot at the ankle. (Roll a d20, Even = Right, Odd = Left). "
         "The afflicted's speed is reduced by 15 feet, and they must use a cane or crutch to move unless they have a "
         "peg leg or prosthesis. They fall prone after making the Dash action."),
    (9,  "Lose a Leg",
         "A catastrophic blow takes the afflicted's leg entirely, forever altering their mobility. (Roll a d20, "
         "Even = Right, Odd = Left). The afflicted's speed is halved, and they must use a cane or crutch to move "
         "unless they have a peg leg or prosthesis. They fall prone after making the Dash action. "
         "They have disadvantage on all Dexterity checks."),
    (10, "Emotional Trauma",
         "The horrors the afflicted has endured fracture something deep within their psyche. "
         "The afflicted gains one Indefinite Madness."),
    (11, "Major Scar",
         "A terrible wound leaves the afflicted permanently disfigured in body and spirit. The wound has left them "
         "visibly and psychologically disfigured. It reshapes not only their appearance, but their sense of self. "
         "Others see the damage before they see them, and they feel it in every interaction. "
         "They have disadvantage on all Charisma rolls."),
    (12, "Deaf",
         "A thunderous impact steals the afflicted's hearing in an instant. "
         "They become permanently deaf."),
    (13, "Organ Failure",
         "Internal damage festers quietly, weakening the afflicted from within. When they complete a long rest, they "
         "must succeed at a DC 15 Constitution saving throw or gain the poisoned condition until they complete a long "
         "rest. Magic such as Major Restoration can cure their Organ Failure."),
    (14, "Brain Damage",
         "A traumatic head injury scrambles the afflicted's thoughts and dulls their awareness. They have disadvantage "
         "on Intelligence, Wisdom, and Charisma checks, as well as Intelligence, Wisdom, and Charisma saving throws. "
         "If they fail a DC 15 saving throw against bludgeoning, force, or psychic damage, they are stunned until the "
         "end of their next turn."),
    (15, "Systemic Damage",
         "Widespread trauma leaves the afflicted's entire body compromised. They have disadvantage on Strength, "
         "Dexterity, and Constitution ability checks and Strength, Dexterity, and Constitution saving throws."),
    (16, "Neurotmesis",
         "Severe nerve trauma disrupts the signals between mind and body. Whenever the afflicted attempts an action in "
         "combat, they must make a DC 15 Constitution saving throw. On a failed save, they lose their bonus action and "
         "can't use reactions until the start of their next turn."),
    (17, "Cardiac Injury",
         "The afflicted's heart struggles under strain, especially when gripped by fear. If the afflicted fails a "
         "saving throw against fear effects or the Fear System, they gain a level of exhaustion."),
    (18, "Intellectual Disability",
         "A lasting cognitive injury diminishes the afflicted's mental acuity. They lose 2 points from one mental "
         "ability. Roll a d6: 1\u20132 Intelligence, 3\u20134 Wisdom, 5\u20136 Charisma."),
    (19, "Physical Disability",
         "A physical injury permanently weakens the afflicted's body. They lose 2 points from one physical ability. "
         "Roll a d6: 1\u20132 Strength, 3\u20134 Dexterity, 5\u20136 Constitution."),
    (20, "Knocked Loose",
         "My head keeps spinnin', I go to sleep and keep grinnin'. If this is just the beginnin', my life is gonna be "
         "beautiful, I've sunshine enough to spread \u2014 it's just like the fella said, tell me quick, ain't that a "
         "kick in the head! Something struck the afflicted hard enough to send stars shimmering across their vision. "
         "And somehow, some of that light stayed behind. Because their brain damage was so severe that it paradoxically "
         "came back to become stable, and the part of their mind that once understood hopelessness no longer functions. "
         "At the start of each session, they gain 1 Hope."),
]

# ═══════════════════════════════════════════════════════════════════════════
# RULES TEXT
# ═══════════════════════════════════════════════════════════════════════════

FEAR_RULES_TEXT = (
    "FEAR ENCOUNTER SYSTEM\n"
    "─────────────────────\n"
    "\n"
    "SANITY POOL\n"
    "  Your maximum Sanity equals 15 + your Wisdom score. It represents\n"
    "  mental fortitude, losing too much triggers madness thresholds.\n"
    "\n"
    "HOW AN ENCOUNTER WORKS\n"
    "  1.  Select an active fear and press ENCOUNTER.\n"
    "  2.  Severity effects apply immediately (see below).\n"
    "  3.  Roll a Wisdom saving throw: d20 + WIS modifier vs the DC.\n"
    "      The DC field defaults to your fear's current Desensitization\n"
    "      DC but can be adjusted manually before triggering.\n"
    "  4.  On a PASS - the encounter ends cleanly. No sanity change.\n"
    "  5.  On a FAIL - roll Xd4 sanity dice (X = severity level),\n"
    "      then choose Confront or Avoid.\n"
    "\n"
    "CONFRONT - Face the fear head-on\n"
    "  • Lose the rolled sanity.\n"
    "  • Desensitization rung +1. The DC decreases next encounter.\n"
    "    Every confrontation makes the fear fractionally easier to face.\n"
    "\n"
    "AVOID - Flee the fear\n"
    "  • Regain the rolled sanity.\n"
    "  • Fear Severity +1. The fear grows stronger.\n"
    "  • Desensitization rung −1. The DC increases next encounter.\n"
    "    Avoidance grants short-term relief but feeds the fear over time.\n"
    "\n"
    "EXTREME SEVERITY - SPECIAL RULES\n"
    "  • +1 Exhaustion is applied automatically when the encounter begins,\n"
    "    before the saving throw is even made.\n"
    "  • Choosing Avoid at Extreme Severity causes the panic response to\n"
    "    generate one new random fear, added immediately to your list.\n"
    "\n"
    "FEAR SEVERITY LEVELS\n"
    "  Low Severity (1d4 sanity on fail)\n"
    "    Disadvantage on all ability checks that involve the fear.\n"
    "\n"
    "  Moderate Severity (2d4 sanity on fail)\n"
    "    You gain the Frightened condition. You cannot take bonus actions\n"
    "    for the duration of the encounter.\n"
    "\n"
    "  High Severity (3d4 sanity on fail)\n"
    "    Frightened and Incapacitated until the end of your next turn.\n"
    "    After recovering: Disadvantage on attack rolls, ability checks,\n"
    "    and saving throws for the remainder of the encounter.\n"
    "\n"
    "  Extreme Severity (4d4 sanity on fail)\n"
    "    Frightened. You fall Prone and become Unconscious (stable).\n"
    "    You remain unconscious for 1 minute or until an ally wakes you.\n"
    "    +1 Exhaustion is applied at the start of the encounter.\n"
    "    Choosing Avoid adds one random new fear to your list.\n"
    "\n"
    "DESENSITIZATION\n"
    "  Desensitization tracks how deeply you have been exposed to a fear.\n"
    "  Higher rungs reflect more confrontations - the DC is lower because\n"
    "  familiarity erodes the fear's grip. All fears begin at Rung 1.\n"
    "\n"
    "  Low Desensitization      Rung 1 - DC 16\n"
    "    Minimal exposure. The fear is at its most potent and raw.\n"
    "\n"
    "  Moderate Desensitization Rung 2 - DC 14\n"
    "    Some exposure. You have faced it, but it still has teeth.\n"
    "\n"
    "  High Desensitization     Rung 3 - DC 12\n"
    "    Significant exposure. The fear is familiar, if not conquered.\n"
    "\n"
    "  Extreme Desensitization  Rung 4 - DC 10\n"
    "    Deep exposure. The fear has largely lost its grip on you.\n"
    "\n"
    "  Confront → rung +1 (DC decreases - you grow more resilient)\n"
    "  Avoid    → rung −1 (DC increases - the fear regains its power)\n"
)

MADNESS_RULES_TEXT = (
    "SANITY & MADNESS SYSTEM\n"
    "───────────────────────\n"
    "\n"
    "SANITY THRESHOLDS\n"
    "  As your sanity falls, crossing a threshold downward triggers a\n"
    "  madness effect automatically. Each threshold fires only once per\n"
    "  descent, you won't be hit again for the same line until your\n"
    "  sanity recovers above it and falls below it again.\n"
    "\n"
    "  Below 75%  →  Short-Term Madness   (1d10 minutes)\n"
    "  Below 50%  →  Long-Term Madness    (1d10 × 10 hours)\n"
    "  Below 25%  →  Indefinite Madness   (until magically cured)\n"
    "  At 0       →  Insanity - the DM takes full control.\n"
    "                The character's mind has completely shattered.\n"
    "\n"
    "ON THRESHOLD TRIGGER\n"
    "  The app prompts you to auto-roll a random madness effect from\n"
    "  the appropriate table (Short-Term, Long-Term, or Indefinite).\n"
    "  Decline the prompt if you prefer to choose the specific effect\n"
    "  manually using the Add Madness panel on this tab.\n"
    "\n"
    "MADNESS DURATIONS\n"
    "  Short-Term:  1d10 minutes."
    "\n"
    "  Long-Term:   1d10 × 10 hours. A deeper, more persistent shift"
    "\n"
    "  Indefinite:  Permanent until removed. Cannot time out naturally.\n"
    "\n"
    "RECOVERY - CLEARING MADNESS\n"
    "  Sanity can be regained through Avoid choices in fear encounters,\n"
    "  rest, spells, or other in-world effects.\n"
    "\n"
    "  Rise above 75%  →  All Short-Term madness entries are cleared.\n"
    "  Rise above 50%  →  All Long-Term madness entries are cleared.\n"
    "  Indefinite madness is NEVER auto-cleared. It must be cured\n"
    "  manually or via Major Restoration (see Healing Spells tab).\n"
    "\n"
    "ADDING & REMOVING MADNESS MANUALLY\n"
    "  Use the Add Madness panel to select a type and a specific named\n"
    "  effect from the table. Active madness entries appear in the list\n"
    "  and can be removed at any time using the Remove button.\n"
    "\n"
    "CURING WITH SPELLS (Healing Spells tab)\n"
    "  Minor Restoration  →  Removes one Short-Term or Long-Term entry.\n"
    "  Major Restoration  →  Removes one Indefinite madness entry.\n"
    "  See the Healing Spells tab for casting time, components,\n"
    "  and Constitution save requirements.\n"
    "\n"
    "EXHAUSTION\n"
    "  Exhaustion is tracked separately and accumulates from multiple\n"
    "  sources: Extreme Severity fear encounters (+1 at encounter start),\n"
    "  Wound check failures by 5 or more (+1), and certain madness effects.\n"
    "  All levels are cumulative - each adds to the ones before it.\n"
    "\n"
    "  Level 1  -  Disadvantage on ability checks\n"
    "  Level 2  -  Speed halved\n"
    "  Level 3  -  Disadvantage on attack rolls and saving throws\n"
    "  Level 4  -  Hit point maximum halved\n"
    "  Level 5  -  Speed reduced to 0\n"
    "  Level 6  -  Death\n"
    "\n"
    "  Hover over each pip on the exhaustion tracker to see the effect\n"
    "  for that level. Click a pip to set exhaustion manually.\n"
    "  Reduce exhaustion through long rests or restorative magic.\n"
)

WOUND_RULES_TEXT = (
    "LINGERING WOUNDS SYSTEM\n"
    "───────────────────────\n"
    "\n"
    "WHEN TO MAKE A WOUND CHECK\n"
    "  A Constitution saving throw is required when a character:\n"
    "  • Is reduced to 0 Hit Points, OR\n"
    "  • Takes a critical hit in combat.\n"
    "\n"
    "  DC = 10, or half the damage dealt - whichever is higher.\n"
    "  Apply your Constitution modifier to this saving throw.\n"
    "\n"
    "WOUND CHECK OUTCOMES\n"
    "  Pass by 5+    No wound. You shrug off the trauma entirely.\n"
    "  Pass          Minor Wound - roll d20 on the Minor Wound table.\n"
    "  Fail          Major Wound - roll d20 on the Major Wound table.\n"
    "  Fail by 5+    Major Wound + 1 level of Exhaustion.\n"
    "\n"
    "MINOR WOUNDS\n"
    "  Minor wounds represent lasting but treatable injuries - shell\n"
    "  shock, concussions, broken bones, lacerations, and similar\n"
    "  trauma. They impose disadvantage on specific ability checks,\n"
    "  saving throws, or attack rolls until cured.\n"
    "  Examples: Concussed (INT checks), Broken Bone (STR checks),\n"
    "  Nerve Damage (DEX checks), Rattled (WIS saves).\n"
    "\n"
    "MAJOR WOUNDS\n"
    "  Major wounds are severe or potentially permanent injuries -\n"
    "  mortal wounds, lost limbs, destroyed senses, and catastrophic\n"
    "  physical trauma. They impose significant ongoing penalties.\n"
    "  Major Restoration can regenerate lost body parts when removing\n"
    "  a Major Wound entry.\n"
    "  Examples: Lost Eye, Lost Arm, Severed Tendons, Mortal Wound.\n"
    "\n"
    "EXHAUSTION FROM WOUNDS\n"
    "  Failing a Wound Check by 5 or more adds 1 Exhaustion level in\n"
    "  addition to the Major Wound rolled. Exhaustion has 6 levels;\n"
    "  reaching 6 is fatal. Manage it carefully alongside wounds.\n"
    "\n"
    "CURING WOUNDS\n"
    "  Minor Wound  →  Minor Restoration or manual removal.\n"
    "  Major Wound  →  Major Restoration or manual removal.\n"
    "                  Major Restoration also regenerates lost body\n"
    "                  parts when it removes the wound entry.\n"
    "\n"
    "  Wounds can be removed manually at any time from this tab.\n"
    "  See the Healing Spells tab for full casting rules, component\n"
    "  costs, and the post-cast Constitution saving throw.\n"
)

# --- Enums & data ────────────────────────────────────────────────────────

class MadnessStage(Enum):
    STABLE = auto(); SHORT_TERM = auto(); LONG_TERM = auto()
    INDEFINITE = auto(); ZERO = auto()

    @staticmethod
    def from_state(pct: float, current: int) -> MadnessStage:
        if current == 0:     return MadnessStage.ZERO
        if pct < 0.25:       return MadnessStage.INDEFINITE
        if pct < 0.50:       return MadnessStage.LONG_TERM
        if pct < 0.75:       return MadnessStage.SHORT_TERM
        return MadnessStage.STABLE

@dataclass
class MadnessInfo:
    title: str; desc: str; color: str; bar_dark: str; bar_light: str

MADNESS: Dict[MadnessStage, MadnessInfo] = {
    MadnessStage.STABLE: MadnessInfo(
        "STABLE", "No madness effects.", T.PURPLE, "#5a4480", T.PURPLE_LT),
    MadnessStage.SHORT_TERM: MadnessInfo(
        "SHORT-TERM MADNESS",
        "Effect lasts 1d10 minutes.",
        T.M_SHORT, "#9e7a28", "#d4b04a"),
    MadnessStage.LONG_TERM: MadnessInfo(
        "LONG-TERM MADNESS",
        "Effect lasts 1d10 × 10 hours.",
        T.M_LONG, "#9a5e28", "#c88a48"),
    MadnessStage.INDEFINITE: MadnessInfo(
        "INDEFINITE MADNESS",
        "Lasts until cured.",
        T.M_INDEF, "#7a2828", "#a84848"),
    MadnessStage.ZERO: MadnessInfo(
        "INSANITY",
        "DM takes full control of the character.\nThe mind is shattered.",
        T.M_ZERO, "#1a0808", "#3a1818"),
}

class EncounterPhase(Enum):
    IDLE = auto(); AWAITING_SAVE = auto(); AWAITING_CHOICE = auto()

@dataclass
class FearStageInfo:
    name: str; desc: str; dice: int; color: str

FEAR_STAGES: Dict[int, FearStageInfo] = {
    1: FearStageInfo("Low Severity",
        "Disadvantage on ability checks involving the fear.", 1, T.STAGE_1),
    2: FearStageInfo("Moderate Severity",
        "Frightened Condition.\n"
        "Cannot take bonus actions.",
        2, T.STAGE_2),
    3: FearStageInfo("High Severity",
        "Frightened + Incapacitated until end of next turn.\n"
        "Then: disadv. on attacks, checks, saves for encounter.",
        3, T.STAGE_3),
    4: FearStageInfo("Extreme Severity",
        "Frightened. Fall Prone & Unconscious (stable).\n"
        "Unconscious 1 min or until ally snaps you out.\n"
        "+1 Exhaustion on encounter.\n"
        "AVOID at Extreme Severity → auto-adds 1 new random fear.",
        4, T.STAGE_4),
}

FEAR_ENC_DC = 12

# Desensitization rungs: rung 1-4 with DC 16/14/12/10 (Low→Extreme)
DESENS_DC: Dict[int, int] = {1: 16, 2: 14, 3: 12, 4: 10}
DESENS_NAMES: Dict[int, str] = {
    1: "Low Desensitization",
    2: "Moderate Desensitization",
    3: "High Desensitization",
    4: "Extreme Desensitization",
}

DESENS_DESCS: Dict[int, str] = {
    1: "Encounter DC 16. Rung 1 of 4.\nMinimal exposure - the fear feels distant.\nConfront raises rung; Avoid lowers rung.",
    2: "Encounter DC 14. Rung 2 of 4.\nSome exposure - the fear is familiar but raw.\nConfront raises rung; Avoid lowers rung.",
    3: "Encounter DC 12. Rung 3 of 4.\nSignificant exposure - the fear is internalised.\nConfront raises rung; Avoid lowers rung.",
    4: "Encounter DC 10. Rung 4 of 4.\nDeep exposure - the fear is part of you now.\nConfront maintains rung; Avoid lowers rung.",
}

# Teal accent used for all desensitization UI elements
DESENS_COLOR    = "#4a9ab8"
DESENS_COLOR_DK = "#2a5870"

# Per-rung blues - increasing luminosity from dim to bright
DESENS_RUNG_COLORS: Dict[int, str] = {
    1: "#2a5f8a",   # Low      - dim steel-blue
    2: "#2d85c0",   # Moderate - medium blue
    3: "#3aabdc",   # High     - bright blue
    4: "#5ad0f8",   # Extreme  - vivid cyan-blue
}

class WoundEncPhase(Enum):
    IDLE = auto(); AWAITING_SAVE = auto(); RESOLVED = auto()


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════

def clamp(x, lo, hi): return max(lo, min(hi, x))
def lerp(a, b, t):    return a + (b - a) * t
def smoothstep(t):
    t = clamp(t, 0.0, 1.0); return t * t * (3.0 - 2.0 * t)
def roll_d(sides: int, n: int = 1) -> List[int]:
    return [random.randint(1, sides) for _ in range(n)]
def safe_int(raw: str, *, lo=None, hi=None) -> int:
    v = int(raw.strip())
    if lo is not None and v < lo: raise ValueError
    if hi is not None and v > hi: raise ValueError
    return v
def hex_lerp(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return f"#{int(lerp(r1,r2,t)):02x}{int(lerp(g1,g2,t)):02x}{int(lerp(b1,b2,t)):02x}"
def stat_modifier(score: int) -> int:
    return (score - 10) // 2

def roll_random_madness(kind: str) -> Tuple[str, str, str]:
    if kind == "short":
        entry = random.choice(SHORT_TERM_MADNESS_TABLE)
    elif kind == "long":
        entry = random.choice(LONG_TERM_MADNESS_TABLE)
    elif kind == "indefinite":
        entry = random.choice(INDEFINITE_MADNESS_TABLE)
    else:
        return ("--", "Unknown", "Unknown madness type.")
    if len(entry) == 3:
        return entry
    return (entry[0], "", entry[1])

def roll_random_wound(severity: str) -> Tuple[int, str, str]:
    if severity == "minor":
        return random.choice(MINOR_WOUND_TABLE)
    else:
        return random.choice(MAJOR_WOUND_TABLE)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════

def roll_insanity_duration(kind: str) -> str:
    """Roll a random duration string for a madness entry."""
    if kind == "short":
        mins = random.randint(1, 10)
        return f"{mins} minute{'s' if mins != 1 else ''}"
    if kind == "long":
        hours = random.randint(1, 10) * 10
        return f"{hours} hours"
    return "Until cured"


@dataclass
class MadnessEntry:
    kind: str          # "short", "long", "indefinite"
    roll_range: str
    effect: str
    timestamp: str = ""
    name: str = ""
    duration: str = ""

    def to_dict(self) -> dict:
        return {"kind": self.kind, "roll_range": self.roll_range,
                "effect": self.effect, "timestamp": self.timestamp,
                "name": self.name, "duration": self.duration}

    @staticmethod
    def from_dict(d: dict) -> MadnessEntry:
        return MadnessEntry(
            kind=d.get("kind", "short"),
            roll_range=d.get("roll_range", "--"),
            effect=d.get("effect", "Unknown"),
            timestamp=d.get("timestamp", ""),
            name=d.get("name", ""),
            duration=d.get("duration", ""))

    @property
    def kind_label(self) -> str:
        return {"short": "Short-Term", "long": "Long-Term",
                "indefinite": "Indefinite"}.get(self.kind, "---")

    @property
    def kind_color(self) -> str:
        return {"short": T.M_SHORT, "long": T.M_LONG,
                "indefinite": T.M_INDEF}.get(self.kind, T.TEXT)


@dataclass
class WoundEntry:
    description: str
    effect: str
    severity: str  # "minor" or "major"
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {"description": self.description, "effect": self.effect,
                "severity": self.severity, "timestamp": self.timestamp}

    @staticmethod
    def from_dict(d: dict) -> WoundEntry:
        return WoundEntry(
            description=d.get("description", "Unknown wound"),
            effect=d.get("effect", ""),
            severity=d.get("severity", "minor"),
            timestamp=d.get("timestamp", ""))


@dataclass
class SanityState:
    wis_score: int = 10; con_score: int = 10
    max_sanity: int = 25; current_sanity: int = 25
    exhaustion: int = 0; fired_thresholds: set = field(default_factory=set)
    wounds: List[WoundEntry] = field(default_factory=list)
    madnesses: List[MadnessEntry] = field(default_factory=list)
    hope: bool = False

    @property
    def percent(self) -> float:
        return self.current_sanity / self.max_sanity if self.max_sanity else 0.0
    @property
    def madness(self) -> MadnessStage:
        return MadnessStage.from_state(self.percent, self.current_sanity)
    @property
    def wis_mod(self) -> int:
        return stat_modifier(self.wis_score)
    @property
    def con_mod(self) -> int:
        return stat_modifier(self.con_score)

    @property
    def minor_wounds(self) -> List[WoundEntry]:
        return [w for w in self.wounds if w.severity == "minor"]
    @property
    def major_wounds(self) -> List[WoundEntry]:
        return [w for w in self.wounds if w.severity == "major"]

    def recalc_and_reset(self):
        self.max_sanity = SANITY_BASE + self.wis_score
        self.current_sanity = self.max_sanity; self.fired_thresholds.clear()

    def apply_loss(self, amt: int) -> List[Tuple[str, str]]:
        amt = max(0, amt); old = self.current_sanity
        self.current_sanity = max(0, self.current_sanity - amt)
        return self._check(old, self.current_sanity)

    def apply_recovery(self, amt: int) -> List[Tuple[str, str, int]]:
        """Apply sanity recovery. Returns [(kind, kind_label, count)] for each
        madness kind auto-cleared because sanity crossed back above its threshold.
        Indefinite madness is never auto-removed."""
        old_pct = self.percent
        self.current_sanity = min(self.max_sanity,
                                  self.current_sanity + max(0, amt))
        new_pct = self.percent
        removed: List[Tuple[str, str, int]] = []
        for _, c, kind in THRESHOLDS:
            if kind in ("indefinite", "zero"):
                continue
            # Crossed upward: was at-or-below this threshold, now above it
            if old_pct <= c < new_pct:
                before = len(self.madnesses)
                self.madnesses = [m for m in self.madnesses if m.kind != kind]
                n = before - len(self.madnesses)
                if n > 0:
                    label = {"short": "Short-Term",
                             "long": "Long-Term"}.get(kind, kind)
                    removed.append((kind, label, n))
        self.rebuild_thresholds()
        return removed

    def rebuild_thresholds(self):
        pct = self.percent; self.fired_thresholds.clear()
        for _, c, _ in THRESHOLDS:
            if pct <= c: self.fired_thresholds.add(c)

    def add_wound(self, desc: str, effect: str, severity: str) -> WoundEntry:
        w = WoundEntry(description=desc, effect=effect, severity=severity,
                       timestamp=datetime.now().strftime("%H:%M"))
        self.wounds.append(w)
        return w

    def add_madness(self, kind: str, custom_effect: str = "") -> MadnessEntry:
        if custom_effect:
            roll_range = "Custom"
            effect = custom_effect
            name = self._next_madness_name(kind, effect, "Custom")
        else:
            result = roll_random_madness(kind)
            roll_range, tbl_name, effect = result
            name = tbl_name if tbl_name else self._next_madness_name(kind, effect, roll_range)
        duration = roll_insanity_duration(kind)
        m = MadnessEntry(kind=kind, roll_range=roll_range, effect=effect,
                         timestamp=datetime.now().strftime("%H:%M"),
                         name=name, duration=duration)
        self.madnesses.append(m)
        return m

    def add_madness_specific(self, kind: str, roll_range: str, name: str, effect: str) -> MadnessEntry:
        """Add a specific madness entry (from dropdown selection)."""
        duration = roll_insanity_duration(kind)
        m = MadnessEntry(kind=kind, roll_range=roll_range, effect=effect,
                         timestamp=datetime.now().strftime("%H:%M"),
                         name=name, duration=duration)
        self.madnesses.append(m)
        return m

    def snapshot(self):
        return {"wis": self.wis_score, "con": self.con_score,
                "max": self.max_sanity,
                "cur": self.current_sanity, "exh": self.exhaustion,
                "fired": list(self.fired_thresholds),
                "wounds": [w.to_dict() for w in self.wounds],
                "madnesses": [m.to_dict() for m in self.madnesses],
                "hope": self.hope}

    def restore(self, s):
        self.wis_score = s["wis"]; self.con_score = s.get("con", 10)
        self.max_sanity = s["max"]
        self.current_sanity = s["cur"]; self.exhaustion = s.get("exh", 0)
        self.fired_thresholds = set(s["fired"])
        self.wounds = [WoundEntry.from_dict(w) for w in s.get("wounds", [])]
        self.madnesses = [MadnessEntry.from_dict(m)
                          for m in s.get("madnesses", [])]
        self.hope = s.get("hope", False)
        self._backfill_madness_names()

    def _check(self, old, new) -> List[Tuple[str, str]]:
        msgs = []
        if not self.max_sanity: return msgs
        op, np_ = old / self.max_sanity, new / self.max_sanity
        for label, c, kind in THRESHOLDS:
            if op > c and np_ <= c and c not in self.fired_thresholds:
                self.fired_thresholds.add(c); msgs.append((label, kind))
        return msgs

    def _next_madness_name(self, kind: str, effect: str, roll_range: str = "") -> str:
        base = self._madness_name_base(kind, effect, roll_range)
        existing = {m.name.strip().lower() for m in self.madnesses if m.name.strip()}
        if base.lower() not in existing:
            return base

        n = 2
        while True:
            candidate = f"{base} {n}"
            if candidate.lower() not in existing:
                return candidate
            n += 1

    def _madness_name_base(self, kind: str, effect: str, roll_range: str = "") -> str:
        txt = (effect or "").lower()

        # Cross-stage specific signals first.
        if "paranoia" in txt or "hunting me" in txt or "watching me" in txt:
            return "Paranoia"
        if "hallucination" in txt or "hallucinations" in txt:
            return "Hallucinations"
        if "delusion" in txt or "imagines they are" in txt:
            return "Delusion"
        if "amnesia" in txt or "memory" in txt:
            return "Memory Fracture"
        if "lucky charm" in txt or "attached to" in txt:
            return "Attachment Fixation"
        if "special friend" in txt or "only one person i can trust" in txt:
            return "Imaginary Companion"
        if "bend the truth" in txt or "outright lie" in txt:
            return "Compulsive Lying"
        if "keep whatever i find" in txt:
            return "Hoarding Instinct"
        if "drunk keeps me sane" in txt:
            return "Drunken Reliance"
        if "can't take anything seriously" in txt:
            return "Inappropriate Levity"
        if "like killing people" in txt:
            return "Murderous Urge"
        if "smartest, wisest, strongest" in txt:
            return "Grandiose Delusion"
        if "hard to care" in txt:
            return "Emotional Numbness"
        if "achieving my goal is the only thing" in txt:
            return "Obsessive Drive"

        # Stage-specific tone: short should feel less intense than long/indefinite.
        if kind == "short":
            if "frightened" in txt or "flee" in txt:
                return "Panic Surge"
            if "babbling" in txt or "incapable of normal speech" in txt:
                return "Disordered Speech"
            if "attack the nearest creature" in txt:
                return "Rage Spike"
            if "eat something strange" in txt:
                return "Strange Craving"
            if "stunned" in txt:
                return "Stupor"
            if "unconscious" in txt:
                return "Blackout"
            if "paralyzed" in txt or "retreats into their mind" in txt:
                return "Shock Withdrawal"
            return "Short-Term Distress"

        if kind == "long":
            if "repeat a specific activity" in txt or "washing hands" in txt or "counting coins" in txt:
                return "Compulsive Ritual"
            if "intense revulsion" in txt:
                return "Severe Aversion"
            if "blinded" in txt or "deafened" in txt:
                return "Sensory Collapse"
            if "tremors" in txt or "tics" in txt:
                return "Uncontrolled Tremors"
            if "loses the ability to speak" in txt:
                return "Speech Loss"
            if "confusion spell" in txt:
                return "Confusion Episodes"
            if "falls unconscious" in txt:
                return "Catatonic Collapse"
            return "Long-Term Breakdown"

        if kind == "indefinite":
            if "become more like someone else" in txt:
                return "Identity Erosion"
            if "powerful enemies are hunting me" in txt:
                return "Persecution Delusion"
            return "Indefinite Derangement"

        return "Madness"

    def _is_generic_madness_name(self, name: str) -> bool:
        n = (name or "").strip().lower()
        if not n:
            return True
        return bool(re.fullmatch(r"(short-term|long-term|indefinite) effect \d+", n))

    def _backfill_madness_names(self):
        for m in self.madnesses:
            if self._is_generic_madness_name(m.name):
                m.name = self._next_madness_name(m.kind, m.effect, m.roll_range)


class FearManager:
    def __init__(self):
        self.fears: Dict[str, int] = {}
        self.desens: Dict[str, int] = {}   # fear name → desensitization rung 1-4

    @property
    def sorted_names(self): return sorted(self.fears.keys(), key=str.lower)

    def add(self, name: str, stage=1) -> str | None:
        name = name.strip()
        if not name: return "Enter a fear name."
        low = {k.lower(): k for k in self.fears}
        if name.lower() in low: return f"Already exists: '{low[name.lower()]}'"
        self.fears[name] = int(clamp(stage, 1, 4))
        self.desens[name] = 1
        return None

    def remove(self, n):
        self.desens.pop(n, None)
        return bool(self.fears.pop(n, None))

    def set_stage(self, n, s):
        if n in self.fears: self.fears[n] = int(clamp(s, 1, 4))
    def get_stage(self, n): return self.fears.get(n, 1)
    def increment_stage(self, n):
        old = self.get_stage(n); new = min(4, old + 1)
        self.fears[n] = new; return new

    # Desensitization rung helpers
    def get_desens(self, n): return self.desens.get(n, 1)
    def set_desens(self, n, rung):
        if n in self.fears: self.desens[n] = int(clamp(rung, 1, 4))
    def incr_desens(self, n):
        old = self.get_desens(n); new = min(4, old + 1)
        self.desens[n] = new; return new
    def decr_desens(self, n):
        old = self.get_desens(n); new = max(1, old - 1)
        self.desens[n] = new; return new

    def add_random(self) -> str | None:
        pool = [f for f in SIMPLE_FEAR_POOL
                if f.lower() not in {k.lower() for k in self.fears}]
        if not pool: return None
        n = random.choice(pool); self.fears[n] = 1; self.desens[n] = 1; return n

    def suggest(self) -> str | None:
        pool = [f for f in SIMPLE_FEAR_POOL
                if f.lower() not in {k.lower() for k in self.fears}]
        return random.choice(pool) if pool else None

    def snapshot(self): return {"fears": dict(self.fears), "desens": dict(self.desens)}
    def restore(self, s):
        if isinstance(s, dict) and "fears" in s:
            raw = s["fears"]
            raw_desens = s.get("desens", {})
        elif isinstance(s, dict):
            raw = s
            raw_desens = {}
        else:
            raw = {}; raw_desens = {}
        self.fears  = {str(k): int(clamp(v, 1, 4)) for k, v in raw.items()}
        self.desens = {str(k): int(clamp(v, 1, 4)) for k, v in raw_desens.items()}
        # back-fill desens for any fear that has no rung yet
        for k in self.fears:
            if k not in self.desens:
                self.desens[k] = 1


@dataclass
class EncounterState:
    phase: EncounterPhase = EncounterPhase.IDLE
    fear_name: str | None = None; fear_stage: int | None = None
    roll_total: int | None = None; roll_text: str | None = None
    wis_save_total: int | None = None

    def reset(self):
        self.phase = EncounterPhase.IDLE
        self.fear_name = self.fear_stage = None
        self.roll_total = self.roll_text = self.wis_save_total = None

    @property
    def active(self): return self.phase != EncounterPhase.IDLE


@dataclass
class WoundEncounterState:
    phase: WoundEncPhase = WoundEncPhase.IDLE
    dc: int = 10; damage_taken: int = 0
    roll_total: int | None = None; con_mod_used: int = 0
    result_text: str = ""

    def reset(self):
        self.phase = WoundEncPhase.IDLE
        self.dc = 10; self.damage_taken = 0
        self.roll_total = None; self.con_mod_used = 0
        self.result_text = ""

    @property
    def active(self): return self.phase != WoundEncPhase.IDLE


class SaveManager:
    def __init__(self):
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA",
                        Path.home() / "AppData/Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library/Application Support"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME",
                        Path.home() / ".config"))
        self._path = base / SAVE_FOLDER_NAME / SAVE_FILE_NAME
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, st: SanityState, fm: FearManager, char_name: str,
             enc_history: list) -> str | None:
        data = {"wis": st.wis_score, "con": st.con_score,
                "cur": st.current_sanity,
                "exh": st.exhaustion, "fears": fm.snapshot(),
                "char_name": char_name,
                "enc_history": enc_history[-20:],
                "wounds": [w.to_dict() for w in st.wounds],
                "madnesses": [m.to_dict() for m in st.madnesses],
                "hope": st.hope}
        try:
            self._path.write_text(json.dumps(data, indent=2),
                                  encoding="utf-8")
            return None
        except Exception as e: return str(e)

    def load(self) -> dict | None:
        if not self._path.exists(): return None
        try: return json.loads(self._path.read_text(encoding="utf-8"))
        except: return None


class UndoStack:
    def __init__(self, limit=UNDO_STACK_LIMIT):
        self._s: list = []; self._limit = limit
    def push(self, st: SanityState, fm: FearManager):
        self._s.append((st.snapshot(), fm.snapshot()))
        if len(self._s) > self._limit: self._s.pop(0)
    def pop(self): return self._s.pop() if self._s else None
    @property
    def can_undo(self): return bool(self._s)


# ═══════════════════════════════════════════════════════════════════════════
# TOOLTIP + BAR ANIMATION
# ═══════════════════════════════════════════════════════════════════════════

class ToolTip:
    def __init__(self, w, text):
        self.w, self.text, self._t = w, text, None
        w.bind("<Enter>", self._show); w.bind("<Leave>", self._hide)
    def _show(self, _=None):
        if self._t: return
        try:
            if not self.w.winfo_exists():
                return
            x = self.w.winfo_rootx() + 12
            y = self.w.winfo_rooty() + self.w.winfo_height() + 4
            self._t = t = tk.Toplevel(self.w)
            t.overrideredirect(True); t.attributes("-topmost", True)
            t.geometry(f"+{x}+{y}")
            f = tk.Frame(t, bg=T.BG_CARD, bd=1, relief="solid",
                         highlightbackground=T.GOLD_DK, highlightthickness=1)
            f.pack()
            tk.Label(f, text=self.text, bg=T.BG_CARD, fg=T.TEXT, padx=10,
                     pady=6, font=T.F_SMALL, justify="left",
                     wraplength=360).pack()
        except tk.TclError:
            self._t = None
    def _hide(self, _=None):
        try:
            if self._t:
                self._t.destroy()
        except tk.TclError:
            pass
        self._t = None

class BarAnim:
    def __init__(self, draw, after):
        self._draw, self._after = draw, after
        self.pct = 100.0; self._target = 100.0; self._start = 100.0
        self._t0 = 0.0; self._dur = 0.5; self._tok = 0
    def go(self, target):
        target = clamp(target, 0, 100); self._target = target
        self._start = self.pct; self._t0 = time.perf_counter()
        self._dur = clamp(0.25 + abs(target - self._start) / 100 * 0.8,
                          0.25, 1.0)
        self._tok += 1; self._step(self._tok)
    def snap(self, p):
        self.pct = self._target = clamp(p, 0, 100)
        self._tok += 1; self._draw(self.pct)
    def _step(self, tok):
        if tok != self._tok: return
        t = clamp((time.perf_counter() - self._t0) /
                  max(0.001, self._dur), 0, 1)
        self.pct = lerp(self._start, self._target, smoothstep(t))
        self._draw(self.pct)
        if t < 1: self._after(16, lambda: self._step(tok))


# ═══════════════════════════════════════════════════════════════════════════
# ASSET MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class AssetMixin:
    def _init_assets(self):
        self._skull_ok = False; self._blood_ok = False
        self.skull_btn_img = self.char_icon_img = self.blood_btn_img = None
        if not PIL_AVAILABLE: return
        d = Path(__file__).resolve().parent / "assets"
        d.mkdir(exist_ok=True)
        skull_p = d / "skull_2620.png"
        self._fetch_if_missing(skull_p, OPENMOJI_SKULL_URL)
        self._load_skull(skull_p)
        swords_p = d / "swords_2694.png"
        self._fetch_if_missing(swords_p, OPENMOJI_SWORDS_URL)
        self._load_char_icon(swords_p)
        blood_p = d / "blood_1FA78.png"
        self._fetch_if_missing(blood_p, OPENMOJI_BLOOD_URL)
        self._load_blood(blood_p)

    @staticmethod
    def _fetch_if_missing(path: Path, url: str):
        if path.exists(): return
        try: urllib.request.urlretrieve(url, path.as_posix())
        except Exception as e: print(f"[WARN] Asset download failed ({url}): {e}")

    def _load_skull(self, path: Path):
        try:
            base = Image.open(path).convert("RGBA")
            rs = getattr(Image, "Resampling", Image).LANCZOS
            btn = base.copy(); btn.thumbnail((20, 20), rs)
            self.skull_btn_img = ImageTk.PhotoImage(btn)
            icon = base.copy(); icon.thumbnail((64, 64), rs)
            self._tk_icon = ImageTk.PhotoImage(icon)
            self.iconphoto(True, self._tk_icon)
            b256 = base.resize((256, 256), Image.BILINEAR)
            a = b256.split()[-1]; g = ImageOps.grayscale(b256)
            red = ImageOps.colorize(g, "#200000", "#d64242").convert("RGBA")
            red.putalpha(a); self._sk_base, self._sk_red = b256, red
            self._skull_ok = True
        except Exception: pass

    def _load_char_icon(self, path: Path):
        try:
            img = Image.open(path).convert("RGBA")
            rs = getattr(Image, "Resampling", Image).LANCZOS
            img.thumbnail((28, 28), rs)
            self.char_icon_img = ImageTk.PhotoImage(img)
        except Exception: self.char_icon_img = None

    def _load_blood(self, path: Path):
        try:
            base = Image.open(path).convert("RGBA")
            rs = getattr(Image, "Resampling", Image).LANCZOS
            btn = base.copy(); btn.thumbnail((20, 20), rs)
            self.blood_btn_img = ImageTk.PhotoImage(btn)
            b256 = base.resize((256, 256), Image.BILINEAR)
            a = b256.split()[-1]; g = ImageOps.grayscale(b256)
            red = ImageOps.colorize(g, "#200000", "#c02020").convert("RGBA")
            red.putalpha(a); self._bl_base, self._bl_red = b256, red
            self._blood_ok = True
        except Exception: self._blood_ok = False

    def _generic_overlay(self, base_img, red_img):
        self.update_idletasks()
        W, H = self.winfo_width(), self.winfo_height()
        x, y = self.winfo_rootx(), self.winfo_rooty()
        ov = tk.Toplevel(self); ov.overrideredirect(True)
        ov.attributes("-topmost", True)
        ov.geometry(f"{W}x{H}+{x}+{y}"); ov.configure(bg="#000")
        try: ov.attributes("-alpha", 0.02); can_a = True
        except tk.TclError: can_a = False
        cv = tk.Canvas(ov, bg="#000", highlightthickness=0)
        cv.pack(fill="both", expand=True)
        iid = cv.create_image(W // 2, H // 2, image=None)
        ms_dur, fps = 800, 30; n = max(1, ms_dur * fps // 1000)
        bp = int(min(W, H) * 0.55); frames = [None] * (n + 1)
        ov._refs = []; idx = [0]
        def _frame(sz, ang, ri):
            bl = Image.blend(base_img, red_img, clamp(ri, 0, 1))
            sz = max(24, int(sz))
            if bl.size != (sz, sz): bl = bl.resize((sz, sz), Image.BILINEAR)
            side = int(max(bl.size) * 1.18)
            im = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            w2, h2 = bl.size
            im.paste(bl, ((side - w2) // 2, (side - h2) // 2), bl)
            return im.rotate(ang, resample=Image.BILINEAR, expand=False)
        def render():
            i = idx[0]
            if i > n: play(); return
            t = i / n; r = smoothstep((t - 0.08) / 0.7)
            sc = lerp(0.18, 1.3, smoothstep(t))
            a = math.sin(t * 2.2 * 2 * math.pi) * lerp(3, 10, smoothstep(t))
            frames[i] = ImageTk.PhotoImage(_frame(int(bp * sc), a, r))
            ov._refs.append(frames[i]); idx[0] += 1; ov.after(0, render)
        def play():
            t0 = time.perf_counter()
            def tick():
                t = clamp((time.perf_counter() - t0) * 1000 / ms_dur, 0, 1)
                fi = max(0, min(n, round(t * n)))
                if can_a:
                    al = (lerp(0.02, 0.9, smoothstep(t / 0.5)) if t <= 0.5
                          else lerp(0.9, 0, smoothstep((t - 0.5) / 0.5)))
                    ov.attributes("-alpha", float(al))
                if frames[fi]: cv.itemconfig(iid, image=frames[fi])
                if t >= 1: ov.destroy(); return
                ov.after(max(1, 1000 // fps), tick)
            tick()
        render()

    def skull_overlay(self):
        if PIL_AVAILABLE and self._skull_ok:
            self._generic_overlay(self._sk_base, self._sk_red)

    def blood_overlay(self):
        if PIL_AVAILABLE and self._blood_ok:
            self._generic_overlay(self._bl_base, self._bl_red)


# ═══════════════════════════════════════════════════════════════════════════
# TTK THEME
# ═══════════════════════════════════════════════════════════════════════════

def setup_theme(root: tk.Tk):
    root.configure(bg=T.BG)
    root.option_add("*Font", T.F_BODY)
    s = ttk.Style(root)
    try: s.theme_use("clam")
    except tk.TclError: pass

    s.configure(".", background=T.BG, foreground=T.TEXT)
    s.configure("TFrame", background=T.BG)
    s.configure("Card.TFrame", background=T.BG_CARD,
                borderwidth=0, relief="flat")
    s.configure("Inset.TFrame", background=T.BG_INSET)
    s.configure("TLabel", background=T.BG, foreground=T.TEXT)
    s.configure("Dim.TLabel", background=T.BG, foreground=T.TEXT_DIM,
                font=T.F_SMALL)
    s.configure("CardDim.TLabel", background=T.BG_CARD,
                foreground=T.TEXT_DIM, font=T.F_SMALL)
    s.configure("Gold.TLabel", background=T.BG_CARD, foreground=T.GOLD,
                font=T.F_SECTION)
    s.configure("TEntry", fieldbackground=T.BG_INSET, foreground=T.TEXT,
                insertcolor=T.TEXT, font=T.F_BODY)
    s.configure("TSeparator", background=T.RULE)

    s.configure("Dark.TNotebook", background=T.BG_DEEP, borderwidth=0)
    s.configure("Dark.TNotebook.Tab", background=T.BG_CARD,
                foreground=T.TEXT_DIM, padding=(16, 8),
                font=T.F_SMALL_B, borderwidth=0)
    s.map("Dark.TNotebook.Tab",
          background=[("selected", T.BG_HOVER), ("active", T.BG_HOVER)],
          foreground=[("selected", T.TEXT_BRIGHT), ("active", T.TEXT_BRIGHT)])

    for name, bg, bg_h, bg_d, fg in [
        ("Gold.TButton",   T.GOLD,    T.GOLD_LT,  T.GOLD_DK,  T.TEXT_BRIGHT),
        ("FearOutline.TButton", T.GOLD_DK, T.GOLD, T.BORDER, T.TEXT_BRIGHT),
        ("Red.TButton",    T.RED,     T.RED_LT,   T.RED_DK,   T.TEXT_BRIGHT),
        ("Blue.TButton",   T.BLUE,    T.BLUE_LT,  T.BORDER,   T.TEXT_BRIGHT),
        ("Green.TButton",  T.GREEN,   T.GREEN_LT, T.BORDER,   T.TEXT_BRIGHT),
        ("BrightGreen.TButton", T.GREEN_LT, "#8fd9ac", T.GREEN, T.TEXT_BRIGHT),
        ("DullGreen.TButton",   "#5f7a62", "#76907a", "#455a48", T.TEXT_BRIGHT),
        ("DullRed.TButton",     T.RED, T.RED_LT, T.RED_DK, T.TEXT_BRIGHT),
        ("Ghost.TButton",  T.BG_CARD, T.BG_HOVER, T.BG_INSET, T.TEXT),
        ("Blood.TButton",  T.BLOOD,   T.BLOOD_LT, T.BLOOD_DK, T.TEXT_BRIGHT),
        ("Purple.TButton", T.PURPLE,  T.PURPLE_LT,T.BORDER,   T.TEXT_BRIGHT),
        ("MadShort.TButton", T.M_SHORT, "#d6b05a", "#9e7a28", T.TEXT_BRIGHT),
        ("MadLong.TButton",  T.M_LONG,  "#cc8a4a", "#9a5e28", T.TEXT_BRIGHT),
        ("MadIndef.TButton", T.M_INDEF, "#a84848", "#7a2828", T.TEXT_BRIGHT),
        ("WoundMin.TButton", T.WOUND_MIN, "#6aaa99", T.WOUND_MIN_DK, T.TEXT_BRIGHT),
        ("Silver.TButton",  T.SILVER,    T.SILVER_LT, T.SILVER_DK,  T.TEXT_BRIGHT),
    ]:
        s.configure(name, background=bg, foreground=fg, padding=(12, 9),
                    borderwidth=0, font=T.F_SMALL_B)
        s.map(name, background=[("active", bg_h), ("disabled", bg_d)],
              foreground=[("active", fg), ("pressed", fg), ("disabled", T.TEXT_DIM)])

    s.configure("Sm.Ghost.TButton", background=T.BG_CARD,
                foreground=T.TEXT_DIM, padding=(6, 4),
                borderwidth=0, font=T.F_TINY)
    s.map("Sm.Ghost.TButton", background=[("active", T.BG_HOVER)],
          foreground=[("active", T.TEXT)])

    s.configure("Stage.TRadiobutton", background=T.BG_CARD,
                foreground=T.TEXT, padding=(4, 3), font=T.F_BODY)
    s.map("Stage.TRadiobutton", foreground=[("active", T.GOLD)])

    s.configure("TCombobox",
                fieldbackground=T.BG_DEEP,
                background=T.BG_INSET,
                foreground=T.TEXT,
                selectbackground="#2b3344",
                selectforeground=T.TEXT_BRIGHT,
                arrowcolor=T.PURPLE_LT)
    s.map("TCombobox",
          fieldbackground=[("readonly", T.BG_DEEP)],
          foreground=[("readonly", T.TEXT)])
    root.option_add("*TCombobox*Listbox.background", T.BG_DEEP)
    root.option_add("*TCombobox*Listbox.foreground", T.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", "#2b3344")
    root.option_add("*TCombobox*Listbox.selectForeground", T.TEXT_BRIGHT)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

class App(AssetMixin, tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry(APP_DEFAULT_SIZE)
        self.minsize(*APP_MIN_SIZE)
        try:
            self.attributes("-alpha", 0.0); self.after(10, self._fade)
        except tk.TclError: pass

        self._init_assets()

        self.state = SanityState(); self.state.recalc_and_reset()
        self.fm = FearManager()
        self.enc = EncounterState()
        self.wound_enc = WoundEncounterState()
        self.save_mgr = SaveManager()
        self.undo = UndoStack()
        self.char_name = "Unnamed Adventurer"
        self.enc_history: List[dict] = []
        self._session_t0 = time.time()
        self._log_lines: List[str] = []
        self.selected_stage = tk.IntVar(value=1)
        self._fear_lb_sel: int | None = None
        self._last_selected_fear: str | None = None
        self._tracked_combos: List[ttk.Combobox] = []
        self._combo_popup_was_open = False
        self._combo_popup_cooldown_until = 0.0
        self._mw_remainder = 0
        self._any_combo_open = False
        self.stage_tvars = {s: tk.StringVar() for s in range(1, 5)}
        self._bg_pending = False; self._pulse_tok = 0
        self._stage_fx_tok = 0
        self._desens_fx_tok = 0
        self._desens_ov_tok = 0
        self._refreshing_fear_list = False
        self._enc_panel_visible = False
        self._madness_effect_current_kind = "short"
        self._mad_fx_tok = 0
        self._push_avoid_tok = 0
        self._san_fx_tok = 0
        self._stage_ov_tok = 0
        self._mad_ov_tok = 0
        self._minor_fx_tok = 0
        self._major_fx_tok = 0
        self._minor_ov_tok = 0
        self._major_ov_tok = 0
        self.hope_var = tk.BooleanVar(value=False)
        self.hope_var.trace_add("write",
            lambda *_: setattr(self.state, "hope", self.hope_var.get()))

        setup_theme(self)
        self._build()

        self._bar = BarAnim(self._draw_bar, self.after)
        self._load()
        self._sync_all()
        self._tick_timer()

        self.bind_all("<Control-z>", lambda _: self._do_undo())
        self.bind_all("<Escape>", lambda _: self._cancel_enc())

    def _fade(self, s=0.07):
        try:
            a = min(1.0, float(self.attributes("-alpha")) + s)
            self.attributes("-alpha", a)
            if a < 1: self.after(16, lambda: self._fade(s))
        except tk.TclError: pass

    def _tick_timer(self):
        e = int(time.time() - self._session_t0)
        self._timer_lbl.config(
            text=f"Session  {e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")
        self.after(1000, self._tick_timer)

    # ─── Save / Load / Undo ───────────────────────────────────────────

    def _save(self):
        err = self.save_mgr.save(self.state, self.fm, self.char_name,
                                 self.enc_history)
        if err: self._log(f"âš  Save failed: {err}")

    def _load(self):
        d = self.save_mgr.load()
        if not d: return
        try:
            self.state.wis_score = int(d.get("wis", 10))
            self.state.con_score = int(d.get("con", 10))
            self.wis_var.set(str(self.state.wis_score))
            self.con_var.set(str(self.state.con_score))
            self.state.max_sanity = SANITY_BASE + self.state.wis_score
            self.state.current_sanity = int(
                clamp(d.get("cur", self.state.max_sanity),
                      0, self.state.max_sanity))
            self.state.exhaustion = int(clamp(d.get("exh", 0), 0, MAX_EXHAUSTION))
            self.state.wounds = [WoundEntry.from_dict(w)
                                 for w in d.get("wounds", [])]
            self.state.madnesses = [MadnessEntry.from_dict(m)
                                    for m in d.get("madnesses", [])]
            self.state.rebuild_thresholds()
            self.state.hope = bool(d.get("hope", False))
            self.hope_var.set(self.state.hope)
            self.fm.restore(d.get("fears") or {})
            self.char_name = d.get("char_name", "Unnamed Adventurer")
            self.char_var.set(self.char_name)
            self.enc_history = d.get("enc_history", [])[-20:]
            self._refresh_fears(); self._end_enc()
            self._refresh_wounds_tab(); self._refresh_madness_display()
            self._log("📜 Loaded save data.")
        except Exception as e: self._log(f"âš  Load failed: {e}")

    def _push_undo(self): self.undo.push(self.state, self.fm)

    def _do_undo(self):
        s = self.undo.pop()
        if not s: return
        self.state.restore(s[0]); self.fm.restore(s[1])
        self.wis_var.set(str(self.state.wis_score))
        self.con_var.set(str(self.state.con_score))
        self._end_enc(); self._refresh_fears()
        self._refresh_wounds_tab(); self._refresh_madness_display()
        self._sync_all(); self._save(); self._log("↩ Undo.")

    # ═══════════════════════════════════════════════════════════════════
    # BUILD UI
    # ═══════════════════════════════════════════════════════════════════

    def _build(self):
        bg_cv = tk.Canvas(self, highlightthickness=0, bg=T.BG_DEEP)
        bg_cv.pack(fill="both", expand=True)
        self._bg = bg_cv
        self.bind("<Configure>", lambda _: self._sched_bg())

        scroll_cv = tk.Canvas(bg_cv, bg=T.BG_DEEP, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(bg_cv, orient="vertical", command=scroll_cv.yview,
                           bg=T.BG_CARD, troughcolor=T.BG_DEEP)
        scroll_cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        scroll_cv.pack(side="left", fill="both", expand=True)
        self._scroll_cv = scroll_cv

        self._main_frame = ttk.Frame(scroll_cv, padding=T.PAD)
        self._main_win_id = scroll_cv.create_window(
            (0, 0), window=self._main_frame, anchor="nw")

        def _on_frame_config(_):
            scroll_cv.configure(scrollregion=scroll_cv.bbox("all"))
        def _on_canvas_config(e):
            scroll_cv.itemconfig(self._main_win_id, width=e.width)
        self._main_frame.bind("<Configure>", _on_frame_config)
        scroll_cv.bind("<Configure>", _on_canvas_config)

        def _is_widget_local_scroll(e):
            w = getattr(e, "widget", None)
            if w is None:
                return False
            try:
                cls = w.winfo_class()
            except tk.TclError:
                return False
            if cls == "TCombobox":
                return True
            return ".popdown." in str(w)

        def _is_combo_popup_open():
            # Primary: flag set via postcommand / cleared on select or focus-out
            if self._any_combo_open:
                return True
            # Fallback: Tcl-level popdown check
            any_open = False
            for combo in getattr(self, "_tracked_combos", []):
                try:
                    if not combo.winfo_exists():
                        continue
                    pop = str(combo.tk.call("ttk::combobox::PopdownWindow", str(combo)))
                    if pop and bool(combo.tk.call("winfo", "ismapped", pop)):
                        any_open = True
                        break
                except tk.TclError:
                    continue
            self._combo_popup_was_open = any_open
            return any_open

        def _pointer_in_widget_path(path: str) -> bool:
            try:
                px = int(self.tk.call("winfo", "pointerx", "."))
                py = int(self.tk.call("winfo", "pointery", "."))
                rx = int(self.tk.call("winfo", "rootx", path))
                ry = int(self.tk.call("winfo", "rooty", path))
                ww = int(self.tk.call("winfo", "width", path))
                wh = int(self.tk.call("winfo", "height", path))
            except tk.TclError:
                return False
            return (rx <= px < rx + ww) and (ry <= py < ry + wh)

        def _close_open_combo_popups_if_pointer_elsewhere():
            closed_any = False
            for combo in getattr(self, "_tracked_combos", []):
                try:
                    if not combo.winfo_exists():
                        continue
                    combo_path = str(combo)
                    pop = str(combo.tk.call("ttk::combobox::PopdownWindow", combo_path))
                    if not pop or not bool(combo.tk.call("winfo", "ismapped", pop)):
                        continue
                    if _pointer_in_widget_path(combo_path) or _pointer_in_widget_path(pop):
                        continue
                    combo.tk.call("ttk::combobox::Unpost", combo_path)
                    closed_any = True
                except tk.TclError:
                    continue
            if closed_any:
                self._any_combo_open = False
                self._combo_popup_was_open = False
                self._combo_popup_cooldown_until = 0.0
                self._mw_remainder = 0
            return closed_any

        def _on_mw(e):
            if _is_combo_popup_open():
                _close_open_combo_popups_if_pointer_elsewhere()
                if _is_combo_popup_open():
                    return "break"
            if _is_widget_local_scroll(e):
                return
            self._mw_remainder += int(getattr(e, "delta", 0))
            steps = int(self._mw_remainder / 120)
            if steps != 0:
                scroll_cv.yview_scroll(-steps, "units")
                self._mw_remainder -= steps * 120
            return "break"
        def _on_mw_l(e):
            if _is_combo_popup_open():
                _close_open_combo_popups_if_pointer_elsewhere()
                if _is_combo_popup_open():
                    return "break"
            if _is_widget_local_scroll(e):
                return
            self._mw_remainder = 0
            scroll_cv.yview_scroll(-3 if e.num == 4 else 3, "units")
            return "break"
        def _on_global_motion(_e):
            _close_open_combo_popups_if_pointer_elsewhere()
        scroll_cv.bind_all("<MouseWheel>", _on_mw)
        scroll_cv.bind_all("<Button-4>", _on_mw_l)
        scroll_cv.bind_all("<Button-5>", _on_mw_l)
        scroll_cv.bind_all("<Motion>", _on_global_motion, add="+")

        mf = self._main_frame
        self._build_header(mf)
        self._build_sanity_bar(mf)

        # ── Custom coloured tab system ─────────────────────────────────
        tab_outer = tk.Frame(mf, bg=T.BG_DEEP)
        tab_outer.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))

        # Tab button bar
        tab_bar = tk.Frame(tab_outer, bg=T.BG_DEEP)
        tab_bar.pack(fill="x")

        # Thin separator that changes colour to match the active tab
        self._tab_sep = tk.Frame(tab_outer, height=2, bg=T.GOLD_DK)
        self._tab_sep.pack(fill="x")

        # Content area
        tab_area = tk.Frame(tab_outer, bg=T.BG)
        tab_area.pack(fill="both", expand=True)

        # Build content frames (not yet visible)
        tab1 = tk.Frame(tab_area, bg=T.BG)
        self._build_tab_fears(tab1)
        tab2 = tk.Frame(tab_area, bg=T.BG)
        self._build_tab_sanity_madness(tab2)
        tab3 = tk.Frame(tab_area, bg=T.BG)
        self._build_tab_wounds(tab3)
        tab4 = tk.Frame(tab_area, bg=T.BG)
        self._build_tab_spells(tab4)

        self._tab_frames = [tab1, tab2, tab3, tab4]
        # (active_fg, active_bg, separator_color)
        self._tab_accents = [
            (T.GOLD,      T.GOLD_DK,   T.GOLD_DK),    # Fears - gold
            (T.PURPLE_LT, T.PURPLE,    T.PURPLE),      # Sanity - purple
            (T.BLOOD_LT,  T.BLOOD_DK,  T.BLOOD_DK),   # Wounds - blood
            (T.SILVER_LT, T.SILVER,    T.SILVER),      # Healing Spells - silver
        ]
        _tab_labels = [
            "  \u2620  FEARS  ",
            "  \U0001f9e0  SANITY & MADNESS  ",
            "  \U0001fa78  WOUNDS  ",
            "  \u2728  HEALING SPELLS  ",
        ]
        self._tab_button_widgets = []
        for i, (label, (acc_fg, acc_bg, _)) in enumerate(
                zip(_tab_labels, self._tab_accents)):
            btn = tk.Label(tab_bar, text=label, font=T.F_SMALL_B,
                           bg=T.BG_CARD, fg=acc_fg,
                           padx=18, pady=10, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, idx=i: self._switch_tab(idx))
            btn.bind("<Enter>",
                     lambda e, idx=i: e.widget.config(bg=T.BG_HOVER))
            btn.bind("<Leave>",
                     lambda e, idx=i: self._update_tab_btn_bg(idx))
            self._tab_button_widgets.append(btn)
        # Filler to extend the tab bar background
        tk.Frame(tab_bar, bg=T.BG_CARD).pack(side="left", fill="x",
                                               expand=True)
        self._active_tab = -1
        self._switch_tab(0)

        self._build_log(mf)

        foot = ttk.Frame(mf)
        foot.pack(fill="x", pady=(T.PAD_SM, 0))
        ttk.Label(foot, text=CREDITS, style="Dim.TLabel").pack(side="right")
        self._timer_lbl = ttk.Label(foot, text="Session  00:00:00",
                                    style="Dim.TLabel")
        self._timer_lbl.pack(side="right", padx=(0, 20))
        ttk.Label(foot, text="Ctrl+Z undo  ·  Esc cancel encounter",
                  style="Dim.TLabel").pack(side="left")

    # ─── Background ───────────────────────────────────────────────────

    def _sched_bg(self):
        if self._bg_pending: return
        self._bg_pending = True; self.after(30, self._draw_bg)

    def _draw_bg(self):
        self._bg_pending = False; c = self._bg
        w, h = c.winfo_width(), c.winfo_height(); c.delete("bg"); sp = 48
        for x in range(0, w, sp):
            c.create_line(x, 0, x, h, fill="#12151e", width=1, tags="bg")
        for y in range(0, h, sp):
            c.create_line(0, y, w, y, fill="#12151e", width=1, tags="bg")
        c.create_rectangle(1, 1, w-1, h-1, outline=T.BORDER, width=1, tags="bg")

    # ─── Header with WIS + CON ────────────────────────────────────────

    def _build_header(self, parent):
        hdr = ttk.Frame(parent, style="Card.TFrame", padding=(T.PAD, 12))
        hdr.pack(fill="x")
        left = ttk.Frame(hdr, style="Card.TFrame")
        left.pack(side="left", fill="x", expand=True)
        name_row = ttk.Frame(left, style="Card.TFrame")
        name_row.pack(fill="x")
        if self.char_icon_img:
            tk.Label(name_row, image=self.char_icon_img,
                     bg=T.BG_CARD, bd=0, relief="flat",
                     highlightthickness=0).pack(side="left", padx=(0, 8))
        else:
            tk.Label(name_row, text="*", bg=T.BG_CARD, fg=T.GOLD,
                     font=T.F_TITLE, bd=0, relief="flat",
                     highlightthickness=0).pack(side="left", padx=(0, 8))
        self.char_var = tk.StringVar(value=self.char_name)
        char_e = tk.Entry(name_row, textvariable=self.char_var,
                          bg=T.BG_INSET, fg=T.TEXT_BRIGHT,
                          insertbackground=T.TEXT, font=T.F_TITLE, bd=0,
                          highlightthickness=1,
                          highlightbackground=T.BORDER,
                          highlightcolor=T.GOLD_DK)
        char_e.pack(side="left", fill="x", expand=True)
        char_e.bind("<FocusOut>", lambda _: self._save_char_name())
        char_e.bind("<Return>", lambda _: self._save_char_name())
        ttk.Label(left, text="Sanity, Fear & Madness Tracker",
                  style="Dim.TLabel").pack(anchor="w", pady=(4, 0))

        # ── Strahd Corruption Thermometer ──────────────────────────────

        right = ttk.Frame(hdr, style="Card.TFrame")
        right.pack(side="right")

        self._wis_adv_var = tk.BooleanVar(value=False)
        self._con_adv_var = tk.BooleanVar(value=False)

        for label_txt, var_name, mod_name, setter, lo, hi, adv_var, label_color in [
            ("WIS", "wis_var", "_wis_mod_lbl", "_set_wis", WIS_MIN, WIS_MAX,
             "_wis_adv_var", T.PURPLE_LT),
            ("CON", "con_var", "_con_mod_lbl", "_set_con", CON_MIN, CON_MAX,
             "_con_adv_var", T.RED_LT),
        ]:
            fr = ttk.Frame(right, style="Card.TFrame")
            fr.pack(side="left", padx=(0, 16))
            tk.Label(fr, text=label_txt, bg=T.BG_CARD, fg=label_color,
                     font=T.F_TINY).pack()
            sv = tk.StringVar(value=str(
                self.state.wis_score if label_txt == "WIS"
                else self.state.con_score))
            setattr(self, var_name, sv)
            e = tk.Entry(fr, textvariable=sv, width=4, bg=T.BG_INSET,
                         fg=T.TEXT_BRIGHT, insertbackground=T.TEXT,
                         font=T.F_MED_NUM, bd=0, justify="center",
                         highlightthickness=1,
                         highlightbackground=T.BORDER,
                         highlightcolor=T.GOLD_DK)
            e.pack()
            e.bind("<Return>", lambda _, s=setter: getattr(self, s)())
            mod_val = self.state.wis_mod if label_txt == "WIS" else self.state.con_mod
            ml = tk.Label(fr, text=f"MOD {mod_val:+d}", bg=T.BG_CARD,
                          fg=label_color, font=T.F_TINY)
            ml.pack()
            setattr(self, mod_name, ml)
            av = getattr(self, adv_var)
            adv_btn = tk.Button(
                fr, text="ADV",
                bg=T.BG_CARD, fg=T.TEXT_DIM,
                activebackground=label_color, activeforeground=T.TEXT_DARK,
                relief="flat", bd=0, cursor="hand2",
                font=T.F_TINY,
                highlightthickness=1, highlightbackground=T.BORDER)
            def _make_adv_toggle(btn, var, color):
                def _toggle():
                    var.set(not var.get())
                    if var.get():
                        btn.config(bg=color, fg=T.TEXT_DARK,
                                   highlightbackground=color)
                    else:
                        btn.config(bg=T.BG_CARD, fg=T.TEXT_DIM,
                                   highlightbackground=T.BORDER)
                return _toggle
            adv_btn.config(command=_make_adv_toggle(adv_btn, av, label_color))
            adv_btn.pack(pady=(2, 0), fill="x")
            ttk.Button(fr, text="Set", style="Sm.Ghost.TButton",
                       command=getattr(self, setter)).pack(pady=(2, 0))

        exh_frame = ttk.Frame(right, style="Card.TFrame")
        exh_frame.pack(side="left")
        tk.Label(exh_frame, text="EXHAUSTION", bg=T.BG_CARD,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack()
        self._exh_canvas = tk.Canvas(exh_frame, width=120, height=28,
                                     bg=T.BG_CARD, highlightthickness=0)
        self._exh_canvas.pack()
        self._exh_canvas.bind("<Button-1>", self._on_exh_click)
        self._exh_canvas.bind("<Motion>",   self._on_exh_motion)
        self._exh_canvas.bind("<Leave>",    self._hide_exh_tip)
        self._exh_tip: tk.Toplevel | None = None
        self._exh_tip_level: int = -1

        hope_fr = ttk.Frame(right, style="Card.TFrame")
        hope_fr.pack(side="left", padx=(16, 0))
        tk.Label(hope_fr, text="HOPE", bg=T.BG_CARD,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack()
        tk.Checkbutton(
            hope_fr, variable=self.hope_var,
            bg=T.BG_CARD, fg=T.TEXT_DIM, selectcolor=T.BG_INSET,
            activebackground=T.BG_CARD, activeforeground=T.TEXT,
            highlightthickness=0, bd=0, cursor="hand2"
        ).pack(pady=(4, 0))

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        for i, (frame, btn) in enumerate(
                zip(self._tab_frames, self._tab_button_widgets)):
            acc_fg, acc_bg, sep_col = self._tab_accents[i]
            if i == idx:
                btn.config(bg=acc_bg, fg=T.TEXT_BRIGHT)
                frame.pack(fill="both", expand=True)
            else:
                btn.config(bg=T.BG_CARD, fg=acc_fg)
                frame.pack_forget()
        if hasattr(self, "_tab_sep"):
            self._tab_sep.config(bg=self._tab_accents[idx][2])
        if idx == 0:
            self._refresh_fears()
        elif idx == 3:
            self._refresh_spells_tab()

    def _update_tab_btn_bg(self, idx: int):
        acc_fg, acc_bg, _ = self._tab_accents[idx]
        if getattr(self, "_active_tab", -1) == idx:
            self._tab_button_widgets[idx].config(bg=acc_bg)
        else:
            self._tab_button_widgets[idx].config(bg=T.BG_CARD)

    def _select_stage_btn(self, s: int):
        if not self._sel_fear():
            return
        self.selected_stage.set(s)
        self._on_stage_change()

    def _update_stage_btn_visuals(self):
        if not hasattr(self, "_stage_btn_frames"):
            return
        n = self._sel_fear()
        sel = self.selected_stage.get()
        for s, (btn_inner, accent_bar, text_area, name_lbl, dice_lbl) \
                in self._stage_btn_frames.items():
            info = FEAR_STAGES[s]
            if not n:
                bg = hex_lerp(T.BG_INSET, T.BG_CARD, 0.45)
                accent_bar.config(bg=T.BORDER, width=5)
                name_lbl.config(fg=T.TEXT_DIM)
                dice_lbl.config(fg=T.TEXT_DIM)
            elif s == sel:
                bg = hex_lerp(T.BG_INSET, info.color, 0.18)
                accent_bar.config(bg=info.color, width=6)
                name_lbl.config(fg=info.color)
                dice_lbl.config(fg=hex_lerp(T.TEXT_DIM, info.color, 0.3))
            else:
                bg = T.BG_INSET
                accent_bar.config(bg=info.color, width=5)
                name_lbl.config(fg=info.color)
                dice_lbl.config(fg=T.TEXT_DIM)
            for w in (btn_inner, text_area, name_lbl, dice_lbl):
                w.config(bg=bg)

    def _select_desens_btn(self, rung: int):
        """Manually set desensitization rung for the currently selected fear."""
        n = self._sel_fear()
        if not n: return
        self._push_undo()
        self.fm.set_desens(n, rung)
        self._refresh_desens_tracker()
        self._refresh_fear_encounter_total_dc()
        self._refresh_fears(keep=n)
        self._log(f"  {n}: Desensitization → {DESENS_NAMES[rung]}")
        self._save()

    def _refresh_fear_encounter_total_dc(self):
        """Set the Fear Encounter DC entry to the selected fear's Desensitization DC."""
        if not hasattr(self, "_fear_dc_var"):
            return
        n = getattr(self, "_last_selected_fear", None)
        if not n or n not in self.fm.fears:
            rung = 1
        else:
            rung = self.fm.get_desens(n)
        self._fear_dc_var.set(str(DESENS_DC.get(rung, DESENS_DC[1])))

    def _on_fear_dc_entry_changed(self):
        """Legacy no-op (DC now comes directly from Desensitization)."""
        return

    def _refresh_desens_tracker(self):
        """Update the desensitization tracker buttons for the selected fear."""
        if not hasattr(self, "_desens_btn_frames"):
            return
        n = self._sel_fear()
        cur = self.fm.get_desens(n) if n else 1
        for r, (d_inner, d_accent, d_text, d_name_lbl, d_dc_lbl) \
                in self._desens_btn_frames.items():
            c = DESENS_RUNG_COLORS[r]
            if not n:
                bg = hex_lerp(T.BG_INSET, T.BG_CARD, 0.45)
                d_accent.config(bg=T.BORDER, width=5)
                d_name_lbl.config(fg=T.TEXT_DIM)
                d_dc_lbl.config(fg=T.TEXT_DIM)
            elif r == cur:
                bg = hex_lerp(T.BG_INSET, c, 0.18)
                d_accent.config(bg=c, width=6)
                d_name_lbl.config(fg=c)
                d_dc_lbl.config(fg=hex_lerp(T.TEXT_DIM, c, 0.3))
            else:
                bg = T.BG_INSET
                d_accent.config(bg=c, width=5)
                d_name_lbl.config(fg=c)
                d_dc_lbl.config(fg=T.TEXT_DIM)
            for w in (d_inner, d_text, d_name_lbl, d_dc_lbl):
                w.config(bg=bg)
        self._refresh_desens_effects()

    def _save_char_name(self):
        self.char_name = self.char_var.get().strip() or "Unnamed Adventurer"
        self._save()

    def _draw_exhaustion(self):
        cv = self._exh_canvas; cv.delete("all")
        for i in range(MAX_EXHAUSTION):
            x = i * 20 + 2; filled = i < self.state.exhaustion
            fill = T.RED if filled else T.BG_INSET
            outline = T.RED_LT if filled else T.BORDER
            cv.create_rectangle(x, 4, x+16, 24, fill=fill,
                                outline=outline, width=1)
            cv.create_text(x+8, 14, text=str(i+1),
                           fill=T.TEXT_BRIGHT if filled else T.TEXT_DIM,
                           font=T.F_TINY)

    def _on_exh_click(self, event):
        idx = event.x // 20
        if 0 <= idx < MAX_EXHAUSTION:
            self._push_undo()
            new = idx + 1 if self.state.exhaustion != idx + 1 else idx
            self.state.exhaustion = new
            self._draw_exhaustion()
            self._log(f"Exhaustion → {self.state.exhaustion}")
            self._save()

    def _on_exh_motion(self, event):
        idx = event.x // 20
        if 0 <= idx < MAX_EXHAUSTION:
            level = idx + 1
            if self._exh_tip_level == level:
                return  # already showing the right pip's tip
            self._hide_exh_tip()
            self._exh_tip_level = level
            cv = self._exh_canvas
            # position above the pip
            pip_cx = idx * 20 + 10
            x = cv.winfo_rootx() + pip_cx - 10
            y = cv.winfo_rooty() - 38
            t = tk.Toplevel(cv)
            t.overrideredirect(True)
            t.attributes("-topmost", True)
            t.geometry(f"+{x}+{y}")
            col = T.RED_LT if level <= self.state.exhaustion else T.BORDER
            f = tk.Frame(t, bg=T.BG_CARD, bd=1, relief="solid",
                         highlightbackground=col, highlightthickness=1)
            f.pack()
            tk.Label(f, text=f"Level {level}  -  {EXHAUSTION_EFFECTS[level]}",
                     bg=T.BG_CARD, fg=T.TEXT_BRIGHT if level <= self.state.exhaustion else T.TEXT,
                     padx=10, pady=5, font=T.F_SMALL).pack()
            self._exh_tip = t
        else:
            self._hide_exh_tip()

    def _hide_exh_tip(self, _=None):
        if self._exh_tip:
            try:
                self._exh_tip.destroy()
            except tk.TclError:
                pass
            self._exh_tip = None
        self._exh_tip_level = -1

    # ─── Strahd Corruption Thermometer ───────────────────────────────

    def _build_sanity_bar(self, parent):
        bf = ttk.Frame(parent); bf.pack(fill="x", pady=(T.PAD_SM, 0))
        self._bar_cv = tk.Canvas(bf, height=50, bg=T.BG,
                                 highlightthickness=0, bd=0)
        self._bar_cv.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self._san_chip = tk.Label(bf, text="", bg=T.BG, fg=T.PURPLE,
                                  font=T.F_BODY_B, anchor="e")
        self._san_chip.pack(side="right")
        self._bar_cv.bind("<Configure>", lambda _: self._draw_bar(
            self._bar.pct if hasattr(self, "_bar") else 100))

    def _draw_bar(self, pct_val):
        cv = self._bar_cv
        if not cv.winfo_exists(): return
        cv.delete("all"); w, h = max(1, cv.winfo_width()), max(1, cv.winfo_height())

        LABEL_H = 17          # top zone reserved for percentage labels
        bar_y = LABEL_H       # bar starts here

        # Label zone background
        cv.create_rectangle(0, 0, w, bar_y, outline="", fill=T.BG)
        # Bar zone background
        cv.create_rectangle(0, bar_y, w, h, outline="", fill=T.BG_DEEP)

        pct = clamp(pct_val / 100, 0, 1)
        stage = MadnessStage.from_state(pct, self.state.current_sanity)
        info = MADNESS[stage]; cd, cl = info.bar_dark, info.bar_light
        fw = int(w * pct)
        bar_h = h - bar_y

        if fw > 0:
            # 18-band parabolic gradient: brightest ~30% from top, darkens toward edges
            BANDS = 18; bh = bar_h / BANDS
            peak = 0.30
            for i in range(BANDS):
                t_raw = i / max(1, BANDS - 1)   # 0..1 top→bottom
                t = ((t_raw - peak) / max(peak, 1.0 - peak)) ** 2
                t = clamp(t, 0.0, 1.0)
                color = hex_lerp(cl, cd, t)
                cv.create_rectangle(0, bar_y + int(i * bh), fw,
                                    bar_y + int((i + 1) * bh),
                                    outline="", fill=color)
            # Top highlight (1px bright line)
            cv.create_line(0, bar_y, fw, bar_y, fill=cl, width=1)
            # Bottom shadow (1px dark line)
            cv.create_line(0, h - 1, fw, h - 1, fill=cd, width=1)
            # % indicator floating at fill right edge
            pct_text = f"{int(round(pct_val))}%"
            mid_y = bar_y + bar_h // 2
            if fw >= 36:
                # Draw inside the bar - dark text contrasts against the coloured fill
                cv.create_text(fw - 4, mid_y, text=pct_text,
                               anchor="e", font=(T.FONT_FAMILY, 10, "bold"),
                               fill=T.BG_DEEP)
            else:
                cv.create_text(fw + 4, mid_y, text=pct_text,
                               anchor="w", font=(T.FONT_FAMILY, 10, "bold"),
                               fill=T.TEXT_DIM)

        # Threshold markers - solid line + tick notch + 4×4 square junction marker
        for val, lbl in [(75, "75%"), (50, "50%"), (25, "25%")]:
            x = int(w * val / 100)
            # Solid line through bar zone
            cv.create_line(x, bar_y, x, h, fill=T.TEXT_DIM, width=1)
            # Tick notch above bar
            cv.create_line(x, bar_y - 4, x, bar_y, fill=T.TEXT_DIM, width=1)
            # 4×4 square junction marker at the bar edge
            cv.create_rectangle(x - 2, bar_y - 2, x + 2, bar_y + 2,
                                 outline=T.TEXT_DIM, fill=T.BG_DEEP)
            # Percentage label elevated in the top zone
            cv.create_text(x, 2, text=lbl, anchor="n",
                           font=(T.FONT_FAMILY, 8), fill=T.TEXT_DIM)

    def _scroll_to_widget(self, w: tk.Widget, pad: int = 16):
        if not hasattr(self, "_scroll_cv") or not w.winfo_exists():
            return
        cv = self._scroll_cv
        self.update_idletasks()
        try:
            y = max(0, w.winfo_rooty() - self._main_frame.winfo_rooty() - pad)
        except tk.TclError:
            return
        region = cv.bbox("all")
        if not region:
            return
        total_h = max(1, region[3] - region[1])
        view_h = max(1, cv.winfo_height())
        max_y = max(0, total_h - view_h)
        y = min(y, max_y)
        cv.yview_moveto(0.0 if max_y == 0 else y / max_y)

    def _show_active_overlay(self, box, color, ov_attr, tok_attr):
        """Fade in/out an 'Effect Active' overlay on an effects box."""
        setattr(self, tok_attr, getattr(self, tok_attr, 0) + 1)
        tok = getattr(self, tok_attr)

        # Lazily create the overlay label (child of the effects box)
        if not hasattr(self, ov_attr):
            ov = tk.Label(box, text="Effect Active", font=T.F_TITLE,
                          anchor="center", bd=0, relief="flat",
                          highlightthickness=0, fg=T.TEXT_BRIGHT)
            setattr(self, ov_attr, ov)
        ov = getattr(self, ov_attr)
        ov.config(text="Effect Active")

        # Place over the full box and bring to front
        ov.place(relx=0, rely=0, relwidth=1, relheight=1)
        ov.lift()

        FRAME_MS = 16  # ~60fps for smooth, stable animation
        N_IN, N_HOLD, N_OUT = 18, 12, 28
        total_steps = N_IN + N_HOLD + N_OUT
        base_bg = box.cget("bg") or T.BG_INSET

        def _ease(t):
            # Cosine ease reduces visible stepping/jitter in Tk redraws.
            t = clamp(t, 0.0, 1.0)
            return 0.5 - 0.5 * math.cos(math.pi * t)

        def tick(step):
            if getattr(self, tok_attr) != tok:
                try: ov.place_forget()
                except tk.TclError: pass
                return
            if step >= total_steps:
                try: ov.place_forget()
                except tk.TclError: pass
                return

            if step < N_IN:
                alpha = _ease((step + 1) / N_IN)
            elif step < N_IN + N_HOLD:
                alpha = 1.0
            else:
                out_step = step - (N_IN + N_HOLD) + 1
                alpha = 1.0 - _ease(out_step / N_OUT)

            # Fade both overlay tint and text against the box background.
            bg = hex_lerp(base_bg, color, alpha * 0.42)
            fg = hex_lerp(base_bg, T.TEXT_BRIGHT, alpha)
            try:
                ov.config(bg=bg, fg=fg)
            except tk.TclError:
                return
            self.after(FRAME_MS, lambda: tick(step + 1))

        tick(0)

    def _focus_stage_effects(self, n=6, highlight_actions=False):
        if getattr(self, "_active_tab", -1) != 0:
            return
        if not hasattr(self, "_stage_effect_box"):
            return

        self._stage_fx_tok += 1
        tok = self._stage_fx_tok

        def tick(i):
            if i <= 0 or tok != self._stage_fx_tok:
                self._refresh_stages()
                self._stage_effect_box.config(bg=T.BG_INSET, highlightbackground=T.BORDER)
                if hasattr(self, "_stage_effect_text"):
                    self._stage_effect_text.config(bg=T.BG_INSET)
                if hasattr(self, "_stage_effect_border"):
                    self._stage_effect_border.config(bg=T.GOLD_DK)
                self._stage_effect_title.config(bg=T.BG_INSET)
                self._stage_effect_detail.config(bg=T.BG_INSET)
                return

            s = int(clamp(self.selected_stage.get(), 1, 4))
            base = FEAR_STAGES[s].color
            on = (i % 2 == 0)
            glow = hex_lerp(base, T.TEXT_BRIGHT, 0.55)
            bg = hex_lerp(T.BG_INSET, base, 0.20 if on else 0.0)
            border = glow if on else T.BORDER

            self._stage_effect_box.config(bg=bg, highlightbackground=border)
            if hasattr(self, "_stage_effect_text"):
                self._stage_effect_text.config(bg=bg)
            if hasattr(self, "_stage_effect_border"):
                self._stage_effect_border.config(bg=glow if on else T.GOLD_DK)
            self._stage_effect_accent.config(bg=glow if on else base, width=8 if on else 5)
            self._stage_effect_title.config(bg=bg)
            self._stage_effect_detail.config(bg=bg)
            self.after(100, lambda: tick(i - 1))

        s = int(clamp(self.selected_stage.get(), 1, 4))
        self._show_active_overlay(
            self._stage_effect_box, FEAR_STAGES[s].color,
            "_stage_eff_ov", "_stage_ov_tok")
        tick(n * 2)

    def _focus_desens_effects(self, n=6):
        """Pulse-animate the Desensitization Effects panel (mirror of _focus_stage_effects)."""
        if getattr(self, "_active_tab", -1) != 0:
            return
        if not hasattr(self, "_desens_effect_box"):
            return

        # Capture the current rung's color at the moment the animation fires
        _fear_n = self._sel_fear()
        _rung   = self.fm.get_desens(_fear_n) if _fear_n else 1
        rung_c  = DESENS_RUNG_COLORS[_rung]

        self._desens_fx_tok += 1
        tok = self._desens_fx_tok

        def tick(i):
            if i <= 0 or tok != self._desens_fx_tok:
                self._refresh_desens_effects()
                return

            on   = (i % 2 == 0)
            glow = hex_lerp(rung_c, T.TEXT_BRIGHT, 0.55)
            bg   = hex_lerp(T.BG_INSET, rung_c, 0.22 if on else 0.06)
            border = T.GOLD if on else T.GOLD_DK

            self._desens_effect_box.config(bg=bg, highlightbackground=border)
            if hasattr(self, "_desens_effect_text"):
                self._desens_effect_text.config(bg=bg)
            if hasattr(self, "_desens_effect_border"):
                self._desens_effect_border.config(bg=T.GOLD if on else T.GOLD_DK)
            self._desens_effect_accent.config(bg=glow if on else rung_c, width=8 if on else 5)
            self._desens_effect_title.config(bg=bg)
            self._desens_effect_detail.config(bg=bg)
            self.after(100, lambda: tick(i - 1))

        self._show_active_overlay(
            self._desens_effect_box, rung_c,
            "_desens_eff_ov", "_desens_ov_tok")
        tick(n * 2)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 1: Fears, Sanity & Madness - ALL ON ONE PAGE
    # ═══════════════════════════════════════════════════════════════════

    def _build_tab_fears(self, parent):
        # Gold top band - Fear system
        tk.Frame(parent, bg=T.GOLD_DK, height=3).pack(fill="x")

        content = ttk.Frame(parent)
        content.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))

        # Two columns: LEFT = Fear features (fixed min-width) | RIGHT = Fear Rules (expands)
        left = ttk.Frame(content)
        left.pack(side="left", fill="both", padx=(0, T.PAD_SM))

        right = ttk.Frame(content)
        right.pack(side="right", fill="both", expand=True)

        # ─── LEFT COLUMN: Fears features ──────────────────────────────
        fear_border = tk.Frame(left, bg=T.GOLD_DK, padx=1, pady=1)
        fear_border.pack(fill="both", expand=True)
        fears_card = tk.Frame(fear_border, bg=T.BG_CARD,
                              padx=10, pady=10)
        fears_card.pack(fill="both", expand=True)
        self._build_fears_section(fears_card)

        # ─── RIGHT COLUMN: Stage Effects + Fear Rules ─────────────────
        desc_border = tk.Frame(right, bg=T.BORDER, padx=1, pady=1)
        desc_border.pack(fill="x", pady=(0, T.PAD_SM))
        self._stage_effect_border = desc_border
        desc_card = tk.Frame(desc_border, bg=T.BG_CARD,
                             padx=T.PAD_SM, pady=T.PAD_SM)
        desc_card.pack(fill="both", expand=True)
        tk.Frame(desc_card, bg=T.GOLD_DK, height=2).pack(fill="x", pady=(0, 6))
        desc_hdr = tk.Frame(desc_card, bg=T.BG_CARD)
        desc_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(desc_hdr, text="FEAR SEVERITY EFFECTS", bg=T.BG_CARD, fg=T.GOLD,
                 font=T.F_SECTION).pack(side="left")
        self._stage_effect_box = tk.Frame(
            desc_card, bg=T.BG_INSET, highlightthickness=1,
            highlightbackground=T.BORDER)
        self._stage_effect_box.pack(fill="x")
        self._stage_effect_accent = tk.Frame(self._stage_effect_box,
                                             bg=T.GOLD, width=5)
        self._stage_effect_accent.pack(side="left", fill="y")
        eff_text = tk.Frame(self._stage_effect_box, bg=T.BG_INSET,
                            padx=10, pady=8)
        self._stage_effect_text = eff_text
        eff_text.pack(side="left", fill="both", expand=True)
        self._stage_effect_title = tk.Label(
            eff_text, text="", bg=T.BG_INSET,
            fg=T.GOLD, font=T.F_SMALL_B, anchor="w")
        self._stage_effect_title.pack(fill="x")
        self._stage_effect_detail = tk.Label(
            eff_text, text="", bg=T.BG_INSET,
            fg=T.TEXT, font=T.F_SMALL, anchor="nw",
            wraplength=500, justify="left")
        self._stage_effect_detail.pack(fill="both", expand=True, pady=(4, 0))

        # ─── FEAR DESENSITIZATION EFFECTS panel ───────────────────────
        desens_eff_border = tk.Frame(right, bg=T.GOLD_DK, padx=1, pady=1)
        desens_eff_border.pack(fill="x", pady=(0, T.PAD_SM))
        self._desens_effect_border = desens_eff_border
        desens_eff_card = tk.Frame(desens_eff_border, bg=T.BG_CARD,
                                   padx=T.PAD_SM, pady=T.PAD_SM)
        desens_eff_card.pack(fill="both", expand=True)
        tk.Frame(desens_eff_card, bg=T.GOLD_DK, height=2).pack(fill="x", pady=(0, 6))
        desens_eff_hdr = tk.Frame(desens_eff_card, bg=T.BG_CARD)
        desens_eff_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(desens_eff_hdr, text="FEAR DESENSITIZATION EFFECTS",
                 bg=T.BG_CARD, fg=T.GOLD, font=T.F_SECTION).pack(side="left")
        self._desens_effect_box = tk.Frame(
            desens_eff_card, bg=T.BG_INSET, highlightthickness=1,
            highlightbackground=T.GOLD_DK)
        self._desens_effect_box.pack(fill="x")
        self._desens_effect_accent = tk.Frame(self._desens_effect_box,
                                              bg=DESENS_COLOR, width=5)
        self._desens_effect_accent.pack(side="left", fill="y")
        desens_eff_inner = tk.Frame(self._desens_effect_box, bg=T.BG_INSET,
                                    padx=10, pady=8)
        self._desens_effect_text = desens_eff_inner
        desens_eff_inner.pack(side="left", fill="both", expand=True)
        self._desens_effect_title = tk.Label(
            desens_eff_inner, text="", bg=T.BG_INSET,
            fg=DESENS_COLOR, font=T.F_SMALL_B, anchor="w")
        self._desens_effect_title.pack(fill="x")
        self._desens_effect_detail = tk.Label(
            desens_eff_inner, text="", bg=T.BG_INSET,
            fg=T.TEXT, font=T.F_SMALL, anchor="nw",
            wraplength=500, justify="left")
        self._desens_effect_detail.pack(fill="both", expand=True, pady=(4, 0))

        fear_rules_border = tk.Frame(right, bg=T.GOLD_DK, padx=1, pady=1)
        fear_rules_border.pack(fill="both", expand=True)
        rules_card = tk.Frame(fear_rules_border, bg=T.BG_CARD,
                              padx=T.PAD, pady=T.PAD)
        rules_card.pack(fill="both", expand=True)
        self._build_rules_section(rules_card, FEAR_RULES_TEXT)

    # ─── Fears section with stages, controls, encounter ───────────────

    def _build_fears_section(self, parent):
        # ── FEAR ENCOUNTER - inset panel with gold top accent ──────────
        enc_border = tk.Frame(parent, bg=T.BORDER, padx=1, pady=1)
        enc_border.pack(fill="x", pady=(0, T.PAD_SM))
        enc_card = tk.Frame(enc_border, bg=T.BG_CARD,
                            padx=T.PAD_SM, pady=T.PAD_SM)
        enc_card.pack(fill="both", expand=True)

        # Gold top accent stripe
        tk.Frame(enc_card, bg=T.GOLD_DK, height=2).pack(fill="x", pady=(0, 6))

        enc_hdr = tk.Frame(enc_card, bg=T.BG_CARD)
        enc_hdr.pack(fill="x", pady=(0, 4))
        _fear_enc_icon = tk.Label(enc_hdr, bg=T.BG_CARD, bd=0,
                                   relief="flat", highlightthickness=0)
        if getattr(self, "skull_btn_img", None):
            _fear_enc_icon.config(image=self.skull_btn_img)
        else:
            _fear_enc_icon.config(text="☠", fg=T.GOLD, font=(T.FONT_FAMILY, 13))
        _fear_enc_icon.pack(side="left", padx=(0, 6))
        tk.Label(enc_hdr, text="FEAR ENCOUNTER", bg=T.BG_CARD, fg=T.GOLD,
                 font=T.F_SECTION).pack(side="left")

        tk.Label(enc_card,
                 text="Select a fear below, set DC, then trigger encounter.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_TINY,
                 justify="left").pack(anchor="w", pady=(0, 5))

        # DC + WIS Mod row
        dc_row = ttk.Frame(enc_card, style="Card.TFrame")
        dc_row.pack(fill="x", pady=(0, 8))
        tk.Label(dc_row, text="DC:", bg=T.BG_CARD, fg=T.TEXT_DIM,
                 font=T.F_SMALL_B).pack(side="left")
        self._fear_dc_var = tk.StringVar(value=str(DESENS_DC[1]))
        dc_entry = tk.Entry(dc_row, textvariable=self._fear_dc_var, width=4,
                            bg=T.BG_INSET, fg=T.TEXT, font=T.F_BODY, bd=0,
                            justify="center", highlightthickness=1,
                            highlightbackground=T.BORDER)
        dc_entry.pack(side="left", padx=(6, 12))
        self._refresh_fear_encounter_total_dc()

        self.enc_btn = ttk.Button(enc_card, text="ENCOUNTER",
                                  style="FearOutline.TButton",
                                  command=self._encounter)
        if getattr(self, "skull_btn_img", None):
            try: self.enc_btn.configure(image=self.skull_btn_img, compound="left")
            except: pass
        self.enc_btn.pack(fill="x")

        # Roll panel (hidden until encounter triggered)
        self.roll_panel = ttk.Frame(enc_card, style="Card.TFrame",
                                    padding=T.PAD_SM)
        self.roll_lbl = tk.Label(self.roll_panel, text="N/A", bg=T.BG_CARD,
                                 fg=T.TEXT_DIM, font=T.F_SMALL)
        self.roll_lbl.pack(anchor="w")
        self.roll_big = tk.Label(self.roll_panel, text="", bg=T.BG_CARD,
                                 fg=T.TEXT_BRIGHT, font=T.F_MED_NUM)
        self.roll_big.pack(anchor="w", pady=(4, 6))

        # Auto sanity formula preview (shown after failed save roll)
        self._enc_formula_push_var = tk.StringVar(value="Confront: N/A")
        self._enc_formula_push_stage_var = tk.StringVar(value="")
        self._enc_formula_avoid_var = tk.StringVar(value="Avoid: N/A")
        self._enc_formula_avoid_stage_var = tk.StringVar(value="")

        preview_box = tk.Frame(self.roll_panel, bg=T.BG_INSET,
                               highlightthickness=1,
                               highlightbackground=T.BORDER)
        preview_box.pack(fill="x", pady=(0, 6))
        tk.Label(preview_box, text="Sanity Preview", bg=T.BG_INSET,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack(anchor="w", padx=6, pady=(4, 1))

        push_row = tk.Frame(preview_box, bg=T.BG_INSET)
        push_row.pack(fill="x", padx=6, pady=(0, 1))
        tk.Label(push_row, textvariable=self._enc_formula_push_var,
                 bg=T.BG_INSET, fg=T.TEXT, font=T.F_TINY,
                 anchor="w").pack(side="left")
        self._enc_formula_push_stage_lbl = tk.Label(
            push_row, textvariable=self._enc_formula_push_stage_var,
            bg=T.BG_INSET, fg=T.TEXT_DIM, font=T.F_TINY, anchor="w")
        self._enc_formula_push_stage_lbl.pack(side="left", padx=(6, 0))

        avoid_row = tk.Frame(preview_box, bg=T.BG_INSET)
        avoid_row.pack(fill="x", padx=6, pady=(0, 4))
        tk.Label(avoid_row, textvariable=self._enc_formula_avoid_var,
                 bg=T.BG_INSET, fg=T.TEXT, font=T.F_TINY,
                 anchor="w").pack(side="left")
        self._enc_formula_avoid_stage_lbl = tk.Label(
            avoid_row, textvariable=self._enc_formula_avoid_stage_var,
            bg=T.BG_INSET, fg=T.TEXT_DIM, font=T.F_TINY, anchor="w")
        self._enc_formula_avoid_stage_lbl.pack(side="left", padx=(6, 0))

        # Row 0: Failed Save / Passed buttons
        save_row = ttk.Frame(self.roll_panel, style="Card.TFrame")
        save_row.pack(fill="x", pady=(0, 4))
        save_row.columnconfigure(0, weight=1, uniform="save_actions")
        save_row.columnconfigure(1, weight=1, uniform="save_actions")

        self.fail_btn = ttk.Button(save_row, text="✗ Failed Save",
                                   style="Red.TButton",
                                   command=self._roll_fail, state="disabled")
        self.fail_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.pass_btn = ttk.Button(save_row, text="✓ Passed",
                                   style="DullGreen.TButton",
                                   command=self._passed, state="disabled")
        self.pass_btn.grid(row=0, column=1, sticky="ew")

        # Row 1: Confront / Avoid buttons (with animated border)
        self._push_avoid_border = tk.Frame(self.roll_panel, bg=T.BG_CARD,
                                           padx=1, pady=1)
        self._push_avoid_border.pack(fill="x")
        push_avoid_inner = ttk.Frame(self._push_avoid_border, style="Card.TFrame")
        push_avoid_inner.pack(fill="both", expand=True)
        push_avoid_inner.columnconfigure(0, weight=1, uniform="push_actions")
        push_avoid_inner.columnconfigure(1, weight=1, uniform="push_actions")

        self.push_btn = ttk.Button(push_avoid_inner, text="Confront",
                                   style="Red.TButton",
                                   command=self._push, state="disabled")
        self.push_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.avoid_btn = ttk.Button(push_avoid_inner, text="🛡 Avoid",
                                    style="Green.TButton",
                                    command=self._avoid, state="disabled")
        self.avoid_btn.grid(row=0, column=1, sticky="ew")

        self.pend_lbl = tk.Label(self.roll_panel, text="", bg=T.BG_CARD,
                                 fg=T.TEXT_DIM, font=T.F_TINY)
        self.pend_lbl.pack(anchor="w", pady=(6, 0))

        # Hope row — shown only when save fails and hope is active
        self._fear_hope_row = tk.Frame(self.roll_panel, bg=T.BG_CARD)
        tk.Label(self._fear_hope_row, text="✦ Hope is active",
                 bg=T.BG_CARD, fg=T.GOLD_LT, font=T.F_TINY).pack(
                     side="left", padx=(0, 8))
        self._fear_hope_btn = tk.Button(
            self._fear_hope_row, text="USE HOPE",
            bg=T.GOLD_DK, fg=T.TEXT_BRIGHT,
            activebackground=T.GOLD, activeforeground=T.TEXT_DARK,
            relief="flat", bd=0, cursor="hand2", font=T.F_SMALL_B,
            highlightthickness=1, highlightbackground=T.GOLD,
            command=self._use_hope_fear)
        self._fear_hope_btn.pack(side="left")
        # Hidden by default
        self._fear_hope_row_visible = False

        self._clear_enc_sanity_preview()
        # Hidden by default; shown only during active encounter flow.
        self._enc_panel_visible = False

        # ── ADD FEARS section ─────────────────────────────────────────
        fears_add_border = tk.Frame(parent, bg=T.BORDER, padx=1, pady=1)
        fears_add_border.pack(fill="x", pady=(0, T.PAD_SM))
        fears_add_card = tk.Frame(fears_add_border, bg=T.BG_CARD,
                                  padx=T.PAD_SM, pady=T.PAD_SM)
        fears_add_card.pack(fill="both", expand=True)

        tk.Frame(fears_add_card, bg=T.GOLD_DK, height=2).pack(fill="x", pady=(0, 6))
        fears_hdr = tk.Frame(fears_add_card, bg=T.BG_CARD)
        fears_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(fears_hdr, text="ADD FEARS", bg=T.BG_CARD, fg=T.GOLD,
                 font=T.F_SECTION).pack(side="left")

        # Add fear row
        add = ttk.Frame(fears_add_card, style="Card.TFrame")
        add.pack(fill="x")
        self.fear_var = tk.StringVar()
        e = tk.Entry(add, textvariable=self.fear_var, bg=T.BG_INSET,
                     fg=T.TEXT, insertbackground=T.TEXT, font=T.F_BODY,
                     bd=0, highlightthickness=1,
                     highlightbackground=T.BORDER)
        e.pack(side="left", fill="x", expand=True, padx=(0, 6))
        e.bind("<Return>", lambda _: self._add_fear())
        ttk.Button(add, text="Random", style="Sm.Ghost.TButton",
                   command=self._suggest).pack(side="left", padx=(0, 4))
        ttk.Button(add, text="Add Fear", style="Gold.TButton",
                   command=self._add_fear).pack(side="left")

        # ── ACTIVE FEARS section ──────────────────────────────────────
        active_fears_border = tk.Frame(parent, bg=T.BORDER, padx=1, pady=1)
        active_fears_border.pack(fill="both", expand=True, pady=(0, T.PAD_SM))
        active_fears_card = tk.Frame(active_fears_border, bg=T.BG_CARD,
                                     padx=T.PAD_SM, pady=T.PAD_SM)
        active_fears_card.pack(fill="both", expand=True)

        tk.Frame(active_fears_card, bg=T.GOLD_DK, height=2).pack(fill="x", pady=(0, 6))
        tk.Label(active_fears_card, text="ACTIVE FEARS", bg=T.BG_CARD,
                 fg=T.GOLD, font=T.F_SECTION).pack(anchor="w", pady=(0, 4))

        # Fear list + stage selector side by side
        top_row = tk.Frame(active_fears_card, bg=T.BG_CARD)
        top_row.pack(fill="both", expand=True)

        list_col = tk.Frame(top_row, bg=T.BG_CARD)
        list_col.pack(side="left", fill="both", expand=True, padx=(0, T.PAD_SM))
        self.fear_lb = tk.Text(
            list_col, height=5, width=60, bg=T.BG_INSET, fg=T.TEXT_BRIGHT,
            font=T.F_BODY, bd=0, highlightthickness=1,
            highlightbackground=T.BORDER, relief="flat",
            state="disabled", wrap="none", cursor="arrow",
            spacing1=2, spacing3=2)
        self.fear_lb.pack(fill="both", expand=True, pady=(0, 4))
        self.fear_lb.bind("<Button-1>", self._on_fear_lb_click)
        # Pre-configure the persistent selection highlight tag
        self.fear_lb.tag_configure("_sel", background=T.BG_HOVER)
        fear_btn_row = tk.Frame(list_col, bg=T.BG_CARD)
        fear_btn_row.pack(fill="x")
        ttk.Button(fear_btn_row, text="🗑 Remove", style="Ghost.TButton",
                   command=self._remove_fear).pack(side="left")
        ttk.Button(fear_btn_row, text="🗑 Remove All", style="Ghost.TButton",
                   command=self._remove_all_fears).pack(side="left", padx=(4, 0))

        stage_sel = tk.Frame(top_row, bg=T.BG_INSET,
                             padx=T.PAD_SM, pady=T.PAD_SM)
        stage_sel.pack(side="right", fill="y")
        stage_cols = tk.Frame(stage_sel, bg=T.BG_INSET)
        stage_cols.pack(fill="both", expand=True)

        sev_col = tk.Frame(stage_cols, bg=T.BG_INSET)
        sev_col.pack(side="left", fill="y")
        tk.Frame(stage_cols, bg=T.BORDER, width=1).pack(side="left", fill="y", padx=(8, 8))
        des_col = tk.Frame(stage_cols, bg=T.BG_INSET)
        des_col.pack(side="left", fill="y")

        tk.Label(sev_col, text="SEVERITY", bg=T.BG_INSET, fg=T.GOLD,
                 font=T.F_SMALL_B).pack(anchor="w", pady=(0, 4))
        self._stage_btn_frames = {}
        for s in range(1, 5):
            info = FEAR_STAGES[s]
            btn_outer = tk.Frame(sev_col, bg=T.BORDER, cursor="hand2")
            btn_outer.pack(fill="x", pady=(0, 4))
            btn_inner = tk.Frame(btn_outer, bg=T.BG_INSET)
            btn_inner.pack(fill="both", expand=True, padx=1, pady=1)
            accent_bar = tk.Frame(btn_inner, bg=info.color, width=5)
            accent_bar.pack(side="left", fill="y")
            text_area = tk.Frame(btn_inner, bg=T.BG_INSET, padx=7, pady=5)
            text_area.pack(side="left", fill="both", expand=True)
            name_lbl = tk.Label(text_area, textvariable=self.stage_tvars[s],
                                bg=T.BG_INSET, fg=info.color,
                                font=T.F_SMALL_B, anchor="w")
            name_lbl.pack(anchor="w")
            dice_lbl = tk.Label(text_area, text=f"Roll {info.dice}d4 on fail",
                                bg=T.BG_INSET, fg=T.TEXT_DIM,
                                font=T.F_TINY, anchor="w")
            dice_lbl.pack(anchor="w")
            for w in (btn_outer, btn_inner, accent_bar, text_area, name_lbl, dice_lbl):
                w.bind("<Button-1>", lambda e, ss=s: self._select_stage_btn(ss))
            self._stage_btn_frames[s] = (btn_inner, accent_bar, text_area, name_lbl, dice_lbl)

        # ── DESENSITIZATION tracker ──────────────────────────────────
        tk.Label(des_col, text="DESENSITIZATION", bg=T.BG_INSET, fg=T.GOLD,
                 font=T.F_SMALL_B).pack(anchor="w", pady=(0, 4))
        self._desens_btn_frames = {}
        for r in range(1, 5):
            d_col = DESENS_RUNG_COLORS[r]
            d_outer = tk.Frame(des_col, bg=T.BORDER, cursor="hand2")
            d_outer.pack(fill="x", pady=(0, 4))
            d_inner = tk.Frame(d_outer, bg=T.BG_INSET)
            d_inner.pack(fill="both", expand=True, padx=1, pady=1)
            d_accent = tk.Frame(d_inner, bg=d_col, width=5)
            d_accent.pack(side="left", fill="y")
            d_text = tk.Frame(d_inner, bg=T.BG_INSET, padx=7, pady=5)
            d_text.pack(side="left", fill="both", expand=True)
            d_name_lbl = tk.Label(d_text, text=DESENS_NAMES[r],
                                  bg=T.BG_INSET, fg=d_col,
                                  font=T.F_SMALL_B, anchor="w")
            d_name_lbl.pack(anchor="w")
            d_dc_lbl = tk.Label(d_text, text=f"DC {DESENS_DC[r]}",
                                bg=T.BG_INSET, fg=T.TEXT_DIM,
                                font=T.F_TINY, anchor="w")
            d_dc_lbl.pack(anchor="w")
            for w in (d_outer, d_inner, d_accent, d_text, d_name_lbl, d_dc_lbl):
                w.bind("<Button-1>", lambda e, rr=r: self._select_desens_btn(rr))
            self._desens_btn_frames[r] = (d_inner, d_accent, d_text, d_name_lbl, d_dc_lbl)


    # ═══════════════════════════════════════════════════════════════════
    # TAB 2: Sanity & Madness
    # ═══════════════════════════════════════════════════════════════════

    def _build_tab_sanity_madness(self, parent):
        # Purple top band - Sanity/Madness system
        tk.Frame(parent, bg=T.PURPLE, height=3).pack(fill="x")

        content = ttk.Frame(parent)
        content.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))

        # Two columns: LEFT = Madness+Sanity features | RIGHT = Rules
        left = ttk.Frame(content)
        left.pack(side="left", fill="both", expand=True, padx=(0, T.PAD_SM))

        right = ttk.Frame(content)
        right.pack(side="right", fill="both", expand=True)

        # ─── LEFT: Madness column (includes sanity controls inside) ───
        self._build_madness_column(left, include_rules=False)

        # ─── RIGHT: Madness Effects + Rules ───────────────────────────
        eff_border = tk.Frame(right, bg=T.BORDER, padx=1, pady=1)
        eff_border.pack(fill="x", pady=(0, T.PAD_SM))
        self._madness_effect_border = eff_border
        eff_card = tk.Frame(eff_border, bg=T.BG_CARD,
                            padx=T.PAD_SM, pady=T.PAD_SM)
        eff_card.pack(fill="both", expand=True)
        tk.Frame(eff_card, bg=T.PURPLE, height=2).pack(fill="x", pady=(0, 5))
        eff_hdr = tk.Frame(eff_card, bg=T.BG_CARD)
        eff_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(eff_hdr, text="MADNESS EFFECTS", bg=T.BG_CARD, fg=T.PURPLE,
                 font=T.F_SECTION).pack(side="left")
        self._madness_effect_box = tk.Frame(
            eff_card, bg=T.BG_INSET, highlightthickness=1,
            highlightbackground=T.BORDER)
        self._madness_effect_box.pack(fill="x")
        self._madness_effect_accent = tk.Frame(
            self._madness_effect_box, bg=T.PURPLE, width=5)
        self._madness_effect_accent.pack(side="left", fill="y")
        eff_txt = tk.Frame(self._madness_effect_box, bg=T.BG_INSET,
                           padx=10, pady=8)
        self._madness_effect_text = eff_txt
        eff_txt.pack(side="left", fill="both", expand=True)
        self._madness_effect_title = tk.Label(
            eff_txt, text="Select an effect or madness entry", bg=T.BG_INSET,
            fg=T.PURPLE, font=T.F_SMALL_B, anchor="w")
        self._madness_effect_title.pack(fill="x")
        self._madness_effect_roll = tk.Label(
            eff_txt, text="", bg=T.BG_INSET, fg=T.TEXT_DIM,
            font=T.F_TINY, anchor="w")
        self._madness_effect_roll.pack(fill="x")
        self._madness_effect_duration = tk.Label(
            eff_txt, text="", bg=T.BG_INSET, fg=T.TEXT_DIM,
            font=T.F_TINY, anchor="w")
        self._madness_effect_duration.pack(fill="x")
        self._madness_effect_desc = tk.Label(
            eff_txt, text="", bg=T.BG_INSET, fg=T.TEXT,
            font=T.F_SMALL, anchor="nw", wraplength=500, justify="left")
        self._madness_effect_desc.pack(fill="both", expand=True, pady=(4, 0))

        rules_border = tk.Frame(right, bg=T.PURPLE, padx=1, pady=1)
        rules_border.pack(fill="both", expand=True)
        rules_card = tk.Frame(rules_border, bg=T.BG_CARD,
                              padx=T.PAD, pady=T.PAD)
        rules_card.pack(fill="both", expand=True)
        self._build_rules_section(rules_card, MADNESS_RULES_TEXT,
                                  accent=T.PURPLE)

    def _build_sanity_controls(self, parent):
        """Build compact sanity controls - parent is an already-bordered inner card."""
        tk.Label(parent, text="SANITY", bg=T.BG_CARD, fg=T.PURPLE,
                 font=T.F_SECTION).pack(anchor="w", pady=(0, 6))

        # Lose row
        lose_row = tk.Frame(parent, bg=T.BG_CARD)
        lose_row.pack(fill="x", pady=(0, 3))
        tk.Label(lose_row, text="Lose:", bg=T.BG_CARD, fg=T.TEXT,
                 font=T.F_SMALL_B, width=6, anchor="w").pack(side="left")
        self.loss_var = tk.StringVar(value="1")
        tk.Entry(lose_row, textvariable=self.loss_var, width=4,
                 bg=T.BG_INSET, fg=T.TEXT_BRIGHT, font=T.F_SMALL, bd=0,
                 highlightthickness=1,
                 highlightbackground=T.BORDER).pack(side="left", padx=(2, 4))
        ttk.Button(lose_row, text="− Lose Sanity", style="Red.TButton",
                   command=self._man_loss).pack(side="left")

        # Recover row
        rec_row = tk.Frame(parent, bg=T.BG_CARD)
        rec_row.pack(fill="x", pady=(0, 3))
        tk.Label(rec_row, text="Gain:", bg=T.BG_CARD, fg=T.TEXT,
                 font=T.F_SMALL_B, width=6, anchor="w").pack(side="left")
        self.rec_var = tk.StringVar(value="1")
        tk.Entry(rec_row, textvariable=self.rec_var, width=4,
                 bg=T.BG_INSET, fg=T.TEXT_BRIGHT, font=T.F_SMALL, bd=0,
                 highlightthickness=1,
                 highlightbackground=T.BORDER).pack(side="left", padx=(2, 4))
        ttk.Button(rec_row, text="+ Gain Sanity", style="Green.TButton",
                   command=self._man_rec).pack(side="left")

        # DM Recovery
        tk.Label(parent, text="DM Recovery:", bg=T.BG_CARD,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack(anchor="w", pady=(4, 2))
        dm_row = tk.Frame(parent, bg=T.BG_CARD)
        dm_row.pack(fill="x", pady=(0, 3))
        ttk.Button(dm_row, text="+1d4", style="Purple.TButton",
                   command=self._minor_rec).pack(side="left", expand=True,
                   fill="x", padx=(0, 2))
        ttk.Button(dm_row, text="+2d4", style="Purple.TButton",
                   command=self._major_rec).pack(side="left", expand=True,
                   fill="x", padx=(2, 0))

        # Dice roll result display
        self._dice_result_var = tk.StringVar(value="-")
        dice_res_box = tk.Frame(parent, bg=T.BG_INSET,
                                highlightthickness=1,
                                highlightbackground=T.BORDER)
        dice_res_box.pack(fill="x", pady=(4, 0))
        tk.Frame(dice_res_box, bg=T.PURPLE, width=3).pack(side="left", fill="y")
        tk.Label(dice_res_box, textvariable=self._dice_result_var,
                 bg=T.BG_INSET, fg=T.PURPLE, font=T.F_SMALL,
                 anchor="w", padx=6, pady=4).pack(side="left", fill="x", expand=True)

        ttk.Button(parent, text="Restore to Max", style="Purple.TButton",
                   command=self._set_max).pack(fill="x", pady=(6, 0))

    # ─── MADNESS COLUMN ───────────────────────────────────────────────

    def _build_madness_column(self, parent, include_rules=True):
        mad_border = tk.Frame(parent, bg=T.PURPLE, padx=1, pady=1)
        mad_border.pack(fill="both", expand=True)
        cat_card = tk.Frame(mad_border, bg=T.BG_CARD,
                            padx=10, pady=10)
        cat_card.pack(fill="both", expand=True)

        # ── Top section: ADD MADNESS (left) + SANITY (right) ──────────
        top_section = tk.Frame(cat_card, bg=T.BG_CARD)
        top_section.pack(fill="x", pady=(0, T.PAD_SM))
        self._madness_add_section = top_section

        # ADD MADNESS bordered card (left)
        add_border = tk.Frame(top_section, bg=T.BORDER, padx=1, pady=1)
        add_border.pack(side="left", fill="both", expand=True, padx=(0, T.PAD_SM))
        add_card = tk.Frame(add_border, bg=T.BG_CARD, padx=T.PAD_SM, pady=T.PAD_SM)
        add_card.pack(fill="both", expand=True)

        tk.Frame(add_card, bg=T.PURPLE, height=2).pack(fill="x", pady=(0, 6))
        hdr = tk.Frame(add_card, bg=T.BG_CARD)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="ADD MADNESS", bg=T.BG_CARD, fg=T.PURPLE,
                 font=T.F_SECTION).pack(side="left")

        tk.Label(add_card,
                 text="Auto-added at thresholds. Select from dropdown or add custom.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_TINY,
                 justify="left", wraplength=300).pack(anchor="w", pady=(0, 6))

        self._build_madness_category_box(add_card, "SHORT-TERM",
            "1d10 minutes", T.M_SHORT, "short")
        self._build_madness_category_box(add_card, "LONG-TERM",
            "1d10 × 10 hours", T.M_LONG, "long")
        self._build_madness_category_box(add_card, "INDEFINITE",
            "Until cured", T.M_INDEF, "indefinite")

        # SANITY bordered card (right)
        self._san_border = tk.Frame(top_section, bg=T.BORDER, padx=1, pady=1)
        self._san_border.pack(side="right", fill="y")
        san_inner = tk.Frame(self._san_border, bg=T.BG_CARD,
                             padx=T.PAD_SM, pady=T.PAD_SM)
        san_inner.pack(fill="both", expand=True)

        tk.Frame(san_inner, bg=T.PURPLE, height=2).pack(fill="x", pady=(0, 6))
        self._build_sanity_controls(san_inner)

        # ── ACTIVE MADNESS bordered card ───────────────────────────────
        active_mad_border = tk.Frame(cat_card, bg=T.BORDER, padx=1, pady=1)
        active_mad_border.pack(fill="both", expand=True, pady=(0, T.PAD_SM))
        active_mad_card = tk.Frame(active_mad_border, bg=T.BG_CARD,
                                   padx=T.PAD_SM, pady=T.PAD_SM)
        active_mad_card.pack(fill="both", expand=True)

        tk.Frame(active_mad_card, bg=T.PURPLE, height=2).pack(fill="x", pady=(0, 6))
        tk.Label(active_mad_card, text="ACTIVE MADNESS", bg=T.BG_CARD,
                 fg=T.PURPLE, font=T.F_SECTION).pack(anchor="w", pady=(0, 4))

        self._madness_lb = tk.Listbox(
            active_mad_card, height=6, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.BG_HOVER, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.BORDER,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._madness_lb.pack(fill="both", expand=True, pady=(0, 4))
        self._madness_lb.bind("<<ListboxSelect>>",
                              lambda _: self._on_madness_sel())

        mad_btn_row = tk.Frame(active_mad_card, bg=T.BG_CARD)
        mad_btn_row.pack(fill="x")
        ttk.Button(mad_btn_row, text="🗑 Remove Selected", style="Ghost.TButton",
                   command=self._remove_madness).pack(side="left")
        ttk.Button(mad_btn_row, text="🗑 Remove All", style="Ghost.TButton",
                   command=self._remove_all_madness).pack(side="left", padx=(4, 0))

        if include_rules:
            mad_rules_border = tk.Frame(parent, bg=T.PURPLE, padx=1, pady=1)
            mad_rules_border.pack(fill="x", pady=(T.PAD_SM, 0))
            rules_card = tk.Frame(mad_rules_border, bg=T.BG_CARD,
                                  padx=T.PAD, pady=T.PAD)
            rules_card.pack(fill="both", expand=True)
            self._build_rules_section(rules_card, MADNESS_RULES_TEXT,
                                      accent=T.PURPLE)

    def _build_madness_category_box(self, parent, title, duration, color, kind):
        """Build a single madness category box with dropdown selection."""
        # Outer wrapper: left accent bar + inset body
        wrapper = tk.Frame(parent, bg=T.BG_DEEP)
        wrapper.pack(fill="x", pady=(0, 4))
        tk.Frame(wrapper, bg=color, width=3).pack(side="left", fill="y")
        box = tk.Frame(wrapper, bg=T.BG_INSET, padx=8, pady=5)
        box.pack(side="left", fill="both", expand=True)

        # Title row
        title_row = tk.Frame(box, bg=T.BG_INSET)
        title_row.pack(fill="x", pady=(0, 3))
        tk.Label(title_row, text=title, bg=T.BG_INSET, fg=color,
                 font=T.F_SMALL_B).pack(side="left")
        tk.Label(title_row, text=f"({duration})", bg=T.BG_INSET,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack(side="left", padx=(6, 0))

        # Dropdown + Add button row
        drop_row = tk.Frame(box, bg=T.BG_INSET)
        drop_row.pack(fill="x", pady=(0, 2))

        options = self._get_madness_options(kind)
        # Blank first entry - selecting it and clicking Add is a no-op
        display_vals = [""] + [o[0] for o in options]
        opts_map = {o[0]: o for o in options}
        setattr(self, f"_mad_opts_{kind}", opts_map)

        combo_var = tk.StringVar()
        setattr(self, f"_mad_drop_{kind}_var", combo_var)
        def _combo_opened():
            self._any_combo_open = True
        def _combo_closed(e, k=kind):
            self._any_combo_open = False
            self._combo_popup_cooldown_until = 0.0
            self._preview_from_dropdown(k)
        def _combo_focusout(_e):
            self._any_combo_open = False
            self._combo_popup_cooldown_until = 0.0
        combo = ttk.Combobox(drop_row, textvariable=combo_var,
                             values=display_vals, state="readonly",
                             font=T.F_TINY, postcommand=_combo_opened)
        self._tracked_combos.append(combo)
        combo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        combo.bind("<<ComboboxSelected>>", _combo_closed)
        combo.bind("<FocusOut>", _combo_focusout)
        # Block mouse-wheel scrolling through options when popup is closed
        combo.bind("<MouseWheel>",
                   lambda _e: "break" if not self._any_combo_open else None)

        roll_style = {
            "short": "MadShort.TButton",
            "long": "MadLong.TButton",
            "indefinite": "MadIndef.TButton",
        }.get(kind, "Purple.TButton")
        ttk.Button(drop_row, text="+ Add", style=roll_style,
                   command=lambda k=kind: self._add_from_dropdown(k)
                   ).pack(side="left")


    def _get_madness_options(self, kind: str) -> List[Tuple[str, str, str, str]]:
        """Returns [(display_str, roll_range, name, effect), ...]"""
        table = {
            "short": SHORT_TERM_MADNESS_TABLE,
            "long": LONG_TERM_MADNESS_TABLE,
            "indefinite": INDEFINITE_MADNESS_TABLE,
        }.get(kind, [])
        opts = []
        for entry in table:
            if len(entry) == 3:
                roll_range, name, effect = entry
            else:
                roll_range, effect = entry
                name = self.state._madness_name_base(kind, effect, roll_range)
            display = f"{roll_range}: {name}" if name else roll_range
            opts.append((display, roll_range, name, effect))
        return opts

    def _add_from_dropdown(self, kind: str):
        """Add madness from dropdown selection."""
        combo_var = getattr(self, f"_mad_drop_{kind}_var", None)
        opts_map = getattr(self, f"_mad_opts_{kind}", {})
        if not combo_var:
            return
        sel = combo_var.get()
        if not sel or sel not in opts_map:
            return
        display, roll_range, name, effect = opts_map[sel]
        self._push_undo()
        m = self.state.add_madness_specific(kind, roll_range, name, effect)
        combo_var.set("")
        self._refresh_madness_display()
        self._show_madness_effect(kind, roll_range, name, effect)
        self._log(f"🧠 {m.kind_label} Madness: {m.name}")
        self._save()

    def _refresh_madness_display(self):
        self._madness_lb.delete(0, "end")
        for i, m in enumerate(self.state.madnesses):
            name = m.name or m.kind_label
            dur = f"  [{m.duration}]" if m.duration else ""
            self._madness_lb.insert("end", f"  {name}{dur}")
            fg = m.kind_color
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._madness_lb.itemconfigure(i, foreground=fg, background=bg)
        if not self.state.madnesses:
            self._reset_madness_effect_panel()

    def _on_madness_sel(self):
        sel = self._madness_lb.curselection()
        if not sel or sel[0] >= len(self.state.madnesses):
            return
        m = self.state.madnesses[sel[0]]
        self._madness_lb.config(selectbackground=m.kind_color)
        self._show_madness_effect(m.kind, m.roll_range,
                                  m.name or m.kind_label, m.effect,
                                  m.duration)

    def _remove_madness(self):
        sel = self._madness_lb.curselection()
        if not sel or sel[0] >= len(self.state.madnesses): return
        self._push_undo()
        m = self.state.madnesses.pop(sel[0])
        self._refresh_madness_display()
        if not self.state.madnesses:
            self._reset_madness_effect_panel()
        self._log(f"Removed madness: {m.kind_label}")
        self._save()

    def _remove_all_madness(self):
        if not self.state.madnesses: return
        self._push_undo()
        self.state.madnesses.clear()
        self._refresh_madness_display()
        self._reset_madness_effect_panel()
        self._log("Removed all madness entries")
        self._save()

    def _reset_madness_effect_panel(self):
        if not hasattr(self, "_madness_effect_title"):
            return
        bg = T.BG_INSET
        self._madness_effect_title.config(
            text="Select an effect or add one", fg=T.PURPLE, bg=bg)
        self._madness_effect_roll.config(text="", bg=bg)
        if hasattr(self, "_madness_effect_duration"):
            self._madness_effect_duration.config(text="", bg=bg)
        self._madness_effect_desc.config(text="", bg=bg)
        self._madness_effect_accent.config(bg=T.PURPLE)
        self._madness_effect_box.config(bg=bg, highlightbackground=T.BORDER)
        self._madness_effect_text.config(bg=bg)

    # --- Rules section builder ────────────────────────────────────────

    def _build_rules_section(self, parent, text, accent=T.GOLD):
        hdr = ttk.Frame(parent, style="Card.TFrame")
        hdr.pack(fill="x", pady=(0, T.PAD_SM))
        tk.Label(hdr, text="📖", bg=T.BG_CARD, fg=accent,
                 font=(T.FONT_FAMILY, 14)).pack(side="left", padx=(0, 8))
        tk.Label(hdr, text="RULES", bg=T.BG_CARD, fg=accent,
                 font=T.F_SECTION).pack(side="left")

        txt = tk.Text(parent, wrap="word", bg=T.BG_INSET, fg=T.TEXT,
                      font=T.F_BODY, bd=0, highlightthickness=1,
                      highlightbackground=T.BORDER, insertbackground=T.TEXT,
                      height=10)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.tag_configure("title", foreground=accent, font=T.F_BODY_B)
        for kw in [
                    # Fear tab
                    "FEAR ENCOUNTER SYSTEM", "SANITY POOL",
                    "HOW AN ENCOUNTER WORKS",
                    "CONFRONT", "AVOID",
                    "EXTREME SEVERITY", "FEAR SEVERITY LEVELS",
                    "Low Severity", "Moderate Severity",
                    "High Severity", "Extreme Severity",
                    "DESENSITIZATION",
                    "Low Desensitization", "Moderate Desensitization",
                    "High Desensitization", "Extreme Desensitization",
                    # Madness tab
                    "SANITY & MADNESS SYSTEM", "SANITY THRESHOLDS",
                    "ON THRESHOLD TRIGGER", "MADNESS DURATIONS",
                    "RECOVERY", "ADDING & REMOVING MADNESS MANUALLY",
                    "CURING WITH SPELLS", "EXHAUSTION",
                    # Wounds tab
                    "LINGERING WOUNDS SYSTEM",
                    "WHEN TO MAKE A WOUND CHECK",
                    "WOUND CHECK OUTCOMES",
                    "MINOR WOUNDS", "MAJOR WOUNDS",
                    "EXHAUSTION FROM WOUNDS", "CURING WOUNDS",
                    ]:
            start = "1.0"
            while True:
                pos = txt.search(kw, start, stopindex="end")
                if not pos: break
                end = f"{pos}+{len(kw)}c"
                txt.tag_add("title", pos, end); start = end
        txt.configure(state="disabled")

    def _show_madness_effect(self, kind: str, roll_range: str, name: str,
                             effect: str, duration: str = ""):
        """Update the madness effects box with selected entry details."""
        if not hasattr(self, "_madness_effect_box"):
            return
        color = {"short": T.M_SHORT, "long": T.M_LONG,
                 "indefinite": T.M_INDEF}.get(kind, T.PURPLE)
        self._madness_effect_current_kind = kind
        kind_label = {"short": "Short-Term", "long": "Long-Term",
                      "indefinite": "Indefinite"}.get(kind, kind)
        bg = hex_lerp(T.BG_INSET, color, 0.06)
        self._madness_effect_accent.config(bg=color)
        self._madness_effect_title.config(text=name, fg=color, bg=bg)
        self._madness_effect_roll.config(
            text=f"[{kind_label}]   Roll: {roll_range}", bg=bg)
        if hasattr(self, "_madness_effect_duration"):
            dur_text = f"Duration: {duration}" if duration else ""
            self._madness_effect_duration.config(text=dur_text, bg=bg)
        self._madness_effect_desc.config(text=effect, bg=bg)
        self._madness_effect_box.config(
            bg=bg, highlightbackground=hex_lerp(T.BORDER, color, 0.4))
        self._madness_effect_text.config(bg=bg)

    def _preview_from_dropdown(self, kind: str):
        """Show effect in effects box when dropdown item is highlighted."""
        combo_var = getattr(self, f"_mad_drop_{kind}_var", None)
        opts_map = getattr(self, f"_mad_opts_{kind}", {})
        if not combo_var:
            return
        sel = combo_var.get()
        if sel not in opts_map:
            return
        _, roll_range, name, effect = opts_map[sel]
        self._show_madness_effect(kind, roll_range, name, effect)

    def _focus_madness_effects(self, n=6):
        """Animate the madness effects box."""
        if getattr(self, "_active_tab", -1) != 1:
            return
        if not hasattr(self, "_madness_effect_box"):
            return
        self._mad_fx_tok += 1
        tok = self._mad_fx_tok

        def tick(i):
            if i <= 0 or tok != self._mad_fx_tok:
                if hasattr(self, "_madness_effect_current_kind"):
                    kind = self._madness_effect_current_kind
                    color = {"short": T.M_SHORT, "long": T.M_LONG,
                             "indefinite": T.M_INDEF}.get(kind, T.PURPLE)
                    bg = hex_lerp(T.BG_INSET, color, 0.06)
                    self._madness_effect_box.config(
                        bg=bg, highlightbackground=hex_lerp(T.BORDER, color, 0.4))
                    for w in [self._madness_effect_text, self._madness_effect_title,
                              self._madness_effect_roll, self._madness_effect_duration,
                              self._madness_effect_desc]:
                        if hasattr(w, "config"):
                            w.config(bg=bg)
                if hasattr(self, "_madness_effect_border"):
                    self._madness_effect_border.config(bg=T.PURPLE)
                return

            kind = getattr(self, "_madness_effect_current_kind", "short")
            color = {"short": T.M_SHORT, "long": T.M_LONG,
                     "indefinite": T.M_INDEF}.get(kind, T.PURPLE)
            on = (i % 2 == 0)
            glow = hex_lerp(color, T.TEXT_BRIGHT, 0.55)
            bg = hex_lerp(T.BG_INSET, color, 0.22 if on else 0.06)
            border = glow if on else hex_lerp(T.BORDER, color, 0.4)
            self._madness_effect_box.config(bg=bg, highlightbackground=border)
            if hasattr(self, "_madness_effect_text"):
                self._madness_effect_text.config(bg=bg)
            if hasattr(self, "_madness_effect_border"):
                self._madness_effect_border.config(bg=glow if on else T.PURPLE)
            if hasattr(self, "_madness_effect_accent"):
                self._madness_effect_accent.config(bg=glow if on else color)
            if hasattr(self, "_madness_effect_title"):
                self._madness_effect_title.config(bg=bg)
            if hasattr(self, "_madness_effect_roll"):
                self._madness_effect_roll.config(bg=bg)
            if hasattr(self, "_madness_effect_duration"):
                self._madness_effect_duration.config(bg=bg)
            if hasattr(self, "_madness_effect_desc"):
                self._madness_effect_desc.config(bg=bg)
            self.after(100, lambda: tick(i - 1))

        kind = getattr(self, "_madness_effect_current_kind", "short")
        ov_color = {"short": T.M_SHORT, "long": T.M_LONG,
                    "indefinite": T.M_INDEF}.get(kind, T.PURPLE)
        self._show_active_overlay(
            self._madness_effect_box, ov_color,
            "_mad_eff_ov", "_mad_ov_tok")
        tick(n * 2)

    # ─── Wound effects helpers ────────────────────────────────────────

    def _get_wound_options(self, severity: str) -> List[Tuple[str, str, str]]:
        """Returns [(display_str, name, effect), ...]"""
        table = MINOR_WOUND_TABLE if severity == "minor" else MAJOR_WOUND_TABLE
        return [(f"{num}: {name}", name, effect) for num, name, effect in table]

    def _build_wound_dropdown_box(self, parent, title, duration, color, severity):
        """Build a wound category dropdown box, matching madness category style."""
        wrapper = tk.Frame(parent, bg=T.BG_DEEP)
        wrapper.pack(fill="x", pady=(0, 4))
        tk.Frame(wrapper, bg=color, width=3).pack(side="left", fill="y")
        box = tk.Frame(wrapper, bg=T.BG_INSET, padx=8, pady=5)
        box.pack(side="left", fill="both", expand=True)

        title_row = tk.Frame(box, bg=T.BG_INSET)
        title_row.pack(fill="x", pady=(0, 3))
        tk.Label(title_row, text=title, bg=T.BG_INSET, fg=color,
                 font=T.F_SMALL_B).pack(side="left")
        tk.Label(title_row, text=f"({duration})", bg=T.BG_INSET,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack(side="left", padx=(6, 0))

        drop_row = tk.Frame(box, bg=T.BG_INSET)
        drop_row.pack(fill="x", pady=(0, 2))

        options = self._get_wound_options(severity)
        display_vals = [""] + [o[0] for o in options]
        opts_map = {o[0]: o for o in options}
        setattr(self, f"_wound_opts_{severity}", opts_map)

        combo_var = tk.StringVar()
        setattr(self, f"_wound_drop_{severity}_var", combo_var)

        def _combo_opened():
            self._any_combo_open = True

        def _combo_closed(e, s=severity):
            self._any_combo_open = False
            self._combo_popup_cooldown_until = 0.0
            self._preview_wound_from_dropdown(s)

        def _combo_focusout(_e):
            self._any_combo_open = False
            self._combo_popup_cooldown_until = 0.0

        combo = ttk.Combobox(drop_row, textvariable=combo_var,
                             values=display_vals, state="readonly",
                             font=T.F_TINY, postcommand=_combo_opened)
        self._tracked_combos.append(combo)
        combo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        combo.bind("<<ComboboxSelected>>", _combo_closed)
        combo.bind("<FocusOut>", _combo_focusout)
        combo.bind("<MouseWheel>",
                   lambda _e: "break" if not self._any_combo_open else None)

        btn_style = "DullRed.TButton" if severity == "minor" else "Blood.TButton"
        ttk.Button(drop_row, text="+ Add", style=btn_style,
                   command=lambda s=severity: self._add_wound_from_dropdown(s)
                   ).pack(side="left")

    def _add_wound_from_dropdown(self, severity: str):
        """Add a wound from the dropdown selection."""
        combo_var = getattr(self, f"_wound_drop_{severity}_var", None)
        opts_map = getattr(self, f"_wound_opts_{severity}", {})
        if not combo_var:
            return
        sel = combo_var.get()
        if not sel or sel not in opts_map:
            return
        display, name, effect = opts_map[sel]
        self._push_undo()
        self.state.add_wound(name, effect, severity)
        combo_var.set("")
        self._refresh_wounds_tab()
        self._show_wound_effect(severity, name, effect)
        self._log(f"🩸 {'Minor' if severity == 'minor' else 'MAJOR'} wound: {name}")
        self._save()

    def _preview_wound_from_dropdown(self, severity: str):
        """Show wound effect preview when dropdown item is selected."""
        combo_var = getattr(self, f"_wound_drop_{severity}_var", None)
        opts_map = getattr(self, f"_wound_opts_{severity}", {})
        if not combo_var:
            return
        sel = combo_var.get()
        if sel not in opts_map:
            return
        display, name, effect = opts_map[sel]
        self._show_wound_effect(severity, name, effect)

    def _show_wound_effect(self, severity: str, name: str, effect: str):
        """Update the wound effects box with selected entry details (no color change)."""
        if severity == "minor":
            if not hasattr(self, "_minor_wound_effect_box"):
                return
            self._minor_wound_eff_title.config(text=name)
            self._minor_wound_eff_sub.config(text="[Minor Wound]")
            self._minor_wound_eff_desc.config(text=effect)
        else:
            if not hasattr(self, "_major_wound_effect_box"):
                return
            self._major_wound_eff_title.config(text=name)
            self._major_wound_eff_sub.config(text="[Major Wound]")
            self._major_wound_eff_desc.config(text=effect)

    def _focus_wound_effects(self, severity: str, n=6):
        """Animate the wound effects box with flash + overlay."""
        if getattr(self, "_active_tab", -1) != 2:
            return
        color = T.RED if severity == "minor" else T.BLOOD
        tok_attr = "_minor_fx_tok" if severity == "minor" else "_major_fx_tok"
        ov_attr  = "_minor_ov_tok" if severity == "minor" else "_major_ov_tok"
        box_attr    = "_minor_wound_effect_box"    if severity == "minor" else "_major_wound_effect_box"
        border_attr = "_minor_wound_effect_border" if severity == "minor" else "_major_wound_effect_border"
        accent_attr = "_minor_wound_eff_accent"    if severity == "minor" else "_major_wound_eff_accent"
        text_attr   = "_minor_wound_eff_text"      if severity == "minor" else "_major_wound_eff_text"
        title_attr  = "_minor_wound_eff_title"     if severity == "minor" else "_major_wound_eff_title"
        sub_attr    = "_minor_wound_eff_sub"       if severity == "minor" else "_major_wound_eff_sub"
        desc_attr   = "_minor_wound_eff_desc"      if severity == "minor" else "_major_wound_eff_desc"

        if not hasattr(self, box_attr):
            return
        box = getattr(self, box_attr)

        setattr(self, tok_attr, getattr(self, tok_attr, 0) + 1)
        tok = getattr(self, tok_attr)

        def tick(i):
            if i <= 0 or getattr(self, tok_attr) != tok:
                if hasattr(self, box_attr):
                    getattr(self, box_attr).config(
                        bg=T.BG_INSET, highlightbackground=T.BORDER)
                if hasattr(self, text_attr):
                    getattr(self, text_attr).config(bg=T.BG_INSET)
                if hasattr(self, border_attr):
                    getattr(self, border_attr).config(bg=T.BORDER)
                return
            on = (i % 2 == 0)
            glow = hex_lerp(color, T.TEXT_BRIGHT, 0.55)
            bg = hex_lerp(T.BG_INSET, color, 0.22 if on else 0.06)
            border_col = glow if on else hex_lerp(T.BORDER, color, 0.4)
            getattr(self, box_attr).config(bg=bg, highlightbackground=border_col)
            if hasattr(self, text_attr):
                getattr(self, text_attr).config(bg=bg)
            if hasattr(self, border_attr):
                getattr(self, border_attr).config(bg=glow if on else T.BORDER)
            if hasattr(self, accent_attr):
                getattr(self, accent_attr).config(bg=glow if on else color)
            if hasattr(self, title_attr):
                getattr(self, title_attr).config(bg=bg)
            if hasattr(self, sub_attr):
                getattr(self, sub_attr).config(bg=bg)
            if hasattr(self, desc_attr):
                getattr(self, desc_attr).config(bg=bg)
            self.after(100, lambda: tick(i - 1))

        ov_label_attr = f"_{severity}_wound_eff_ov"
        self._show_active_overlay(box, color, ov_label_attr, ov_attr)
        tick(n * 2)

    def _remove_all_minor_wounds(self):
        if not self.state.minor_wounds:
            return
        self._push_undo()
        self.state.wounds = [w for w in self.state.wounds if w.severity != "minor"]
        self._refresh_wounds_tab()
        self._log("🗑 Removed all minor wounds")
        self._save()

    def _remove_all_major_wounds(self):
        if not self.state.major_wounds:
            return
        self._push_undo()
        self.state.wounds = [w for w in self.state.wounds if w.severity != "major"]
        self._refresh_wounds_tab()
        self._log("🗑 Removed all major wounds")
        self._save()

    def _focus_sanity_controls(self, n=4):
        """Pulse the sanity controls border when sanity is modified."""
        if not hasattr(self, "_san_border"):
            return
        self._san_fx_tok += 1
        tok = self._san_fx_tok

        def tick(i):
            if i <= 0 or tok != self._san_fx_tok:
                if hasattr(self, "_san_border"):
                    self._san_border.config(bg=T.BORDER)
                return
            on = (i % 2 == 0)
            glow = hex_lerp(T.PURPLE, T.TEXT_BRIGHT, 0.55)
            self._san_border.config(bg=glow if on else T.BORDER)
            self.after(100, lambda: tick(i - 1))

        tick(n * 2)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 2: Wounds
    # ═══════════════════════════════════════════════════════════════════

    def _build_tab_wounds(self, parent):
        # Red top band - Wounds system
        tk.Frame(parent, bg=T.BLOOD, height=3).pack(fill="x")

        content = ttk.Frame(parent)
        content.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))

        left_col = ttk.Frame(content)
        left_col.pack(side="left", fill="both", expand=True,
                      padx=(0, T.PAD_SM))
        right_col = ttk.Frame(content)
        right_col.pack(side="right", fill="both", expand=True)

        # ─── Left: Encounter card (Blood border) ──────────────────────
        enc_border = tk.Frame(left_col, bg=T.BLOOD, padx=1, pady=1)
        enc_border.pack(fill="x")
        enc_card = tk.Frame(enc_border, bg=T.BG_CARD,
                            padx=T.PAD, pady=T.PAD)
        enc_card.pack(fill="both", expand=True)

        eh = tk.Frame(enc_card, bg=T.BG_CARD)
        eh.pack(fill="x", pady=(0, T.PAD_SM))
        _wound_enc_icon = tk.Label(eh, bg=T.BG_CARD, bd=0,
                                    relief="flat", highlightthickness=0)
        if getattr(self, "blood_btn_img", None):
            _wound_enc_icon.config(image=self.blood_btn_img)
        else:
            _wound_enc_icon.config(text="🩸", fg=T.BLOOD, font=(T.FONT_FAMILY, 14))
        _wound_enc_icon.pack(side="left", padx=(0, 8))
        tk.Label(eh, text="WOUND ENCOUNTER", bg=T.BG_CARD, fg=T.BLOOD,
                 font=T.F_SECTION).pack(side="left")

        tk.Label(enc_card,
                 text="Trigger: 0 HP or critical hit → CON save.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_TINY,
                 justify="left").pack(anchor="w", pady=(0, 8))

        dc_row = tk.Frame(enc_card, bg=T.BG_CARD)
        dc_row.pack(fill="x", pady=(0, 6))
        tk.Label(dc_row, text="DC:", bg=T.BG_CARD, fg=T.TEXT_DIM,
                 font=T.F_SMALL_B).pack(side="left")
        self._wound_dc_var = tk.StringVar(value="10")
        tk.Entry(dc_row, textvariable=self._wound_dc_var, width=5,
                 bg=T.BG_INSET, fg=T.TEXT, font=T.F_BODY, bd=0,
                 justify="center", highlightthickness=1,
                 highlightbackground=T.BORDER).pack(side="left", padx=(6, 8))
        tk.Label(dc_row, text="(10 or half dmg)", bg=T.BG_CARD,
                 fg=T.TEXT_DIM, font=T.F_TINY).pack(side="left")

        dmg_row = tk.Frame(enc_card, bg=T.BG_CARD)
        dmg_row.pack(fill="x", pady=(0, 8))
        tk.Label(dmg_row, text="Damage:", bg=T.BG_CARD, fg=T.TEXT_DIM,
                 font=T.F_SMALL_B).pack(side="left")
        self._wound_dmg_var = tk.StringVar(value="0")
        tk.Entry(dmg_row, textvariable=self._wound_dmg_var, width=5,
                 bg=T.BG_INSET, fg=T.TEXT, font=T.F_BODY, bd=0,
                 justify="center", highlightthickness=1,
                 highlightbackground=T.BORDER).pack(side="left", padx=(6, 4))
        ttk.Button(dmg_row, text="Calc DC", style="Sm.Ghost.TButton",
                   command=self._calc_wound_dc).pack(side="left")

        self._wound_enc_btn = ttk.Button(
            enc_card, text="WOUND ENCOUNTER", style="Blood.TButton",
            command=self._wound_encounter)
        if getattr(self, "blood_btn_img", None):
            try: self._wound_enc_btn.configure(image=self.blood_btn_img, compound="left")
            except: pass
        self._wound_enc_btn.pack(fill="x", pady=(0, 6))

        # Wound roll panel
        self._wound_roll_panel = tk.Frame(enc_card, bg=T.BG_CARD)
        self._wound_roll_lbl = tk.Label(self._wound_roll_panel, text="N/A",
                                        bg=T.BG_CARD, fg=T.TEXT_DIM,
                                        font=T.F_SMALL)
        self._wound_roll_lbl.pack(anchor="w")
        self._wound_roll_big = tk.Label(self._wound_roll_panel, text="",
                                        bg=T.BG_CARD, fg=T.TEXT_BRIGHT,
                                        font=T.F_MED_NUM)
        self._wound_roll_big.pack(anchor="w", pady=(4, 6))

        wr1 = tk.Frame(self._wound_roll_panel, bg=T.BG_CARD)
        wr1.pack(fill="x", pady=(0, 4))
        self._wound_pass5_btn = ttk.Button(
            wr1, text="✓ Pass by 5+", style="BrightGreen.TButton",
            command=lambda: self._wound_resolve("pass5"))
        self._wound_pass5_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._wound_pass_btn = ttk.Button(
            wr1, text="✓ Pass", style="DullGreen.TButton",
            command=lambda: self._wound_resolve("pass"))
        self._wound_pass_btn.pack(side="left", expand=True, fill="x")

        wr2 = tk.Frame(self._wound_roll_panel, bg=T.BG_CARD)
        wr2.pack(fill="x")
        self._wound_fail_btn = ttk.Button(
            wr2, text="✗ Fail", style="Red.TButton",
            command=lambda: self._wound_resolve("fail"))
        self._wound_fail_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._wound_fail5_btn = ttk.Button(
            wr2, text="✗ Fail by 5+", style="Blood.TButton",
            command=lambda: self._wound_resolve("fail5"))
        self._wound_fail5_btn.pack(side="left", expand=True, fill="x")

        self._wound_result_lbl = tk.Label(self._wound_roll_panel, text="",
                                          bg=T.BG_CARD, fg=T.TEXT_DIM,
                                          font=T.F_SMALL)
        self._wound_result_lbl.pack(anchor="w", pady=(6, 0))

        # Hope row — shown only when save fails and hope is active
        self._wound_hope_row = tk.Frame(self._wound_roll_panel, bg=T.BG_CARD)
        tk.Label(self._wound_hope_row, text="✦ Hope is active",
                 bg=T.BG_CARD, fg=T.GOLD_LT, font=T.F_TINY).pack(
                     side="left", padx=(0, 8))
        self._wound_hope_btn = tk.Button(
            self._wound_hope_row, text="USE HOPE",
            bg=T.GOLD_DK, fg=T.TEXT_BRIGHT,
            activebackground=T.GOLD, activeforeground=T.TEXT_DARK,
            relief="flat", bd=0, cursor="hand2", font=T.F_SMALL_B,
            highlightthickness=1, highlightbackground=T.GOLD,
            command=self._use_hope_wound)
        self._wound_hope_btn.pack(side="left")
        self._wound_hope_row_visible = False

        # ─── Left: Add Wound card (Border outline, 2 dropdowns) ───────
        add_border = tk.Frame(left_col, bg=T.BORDER, padx=1, pady=1)
        add_border.pack(fill="x", pady=(T.PAD_SM, 0))
        add_card = tk.Frame(add_border, bg=T.BG_CARD, padx=T.PAD_SM, pady=T.PAD_SM)
        add_card.pack(fill="both", expand=True)

        tk.Frame(add_card, bg=T.RED, height=2).pack(fill="x", pady=(0, 6))
        add_hdr = tk.Frame(add_card, bg=T.BG_CARD)
        add_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(add_hdr, text="ADD WOUND", bg=T.BG_CARD, fg=T.RED,
                 font=T.F_SECTION).pack(side="left")

        self._build_wound_dropdown_box(add_card, "MINOR", "Long Rest", T.RED, "minor")
        self._build_wound_dropdown_box(add_card, "MAJOR", "Major Resoration", T.BLOOD, "major")

        # ─── Left: Active Minor Wounds card ───────────────────────────
        minor_border = tk.Frame(left_col, bg=T.BORDER, padx=1, pady=1)
        minor_border.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))
        minor_card = tk.Frame(minor_border, bg=T.BG_CARD, padx=T.PAD, pady=T.PAD)
        minor_card.pack(fill="both", expand=True)

        tk.Frame(minor_card, bg=T.RED, height=2).pack(fill="x", pady=(0, 6))
        mh = tk.Frame(minor_card, bg=T.BG_CARD)
        mh.pack(fill="x", pady=(0, 4))
        tk.Label(mh, text="ACTIVE MINOR WOUNDS", bg=T.BG_CARD, fg=T.RED,
                 font=T.F_SECTION).pack(side="left")

        self._w_minor_lb = tk.Listbox(
            minor_card, height=4, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.RED, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.RED,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._w_minor_lb.pack(fill="both", expand=True, pady=(0, 6))
        self._w_minor_lb.bind("<<ListboxSelect>>",
                              lambda _: self._on_wound_sel("minor"))

        mbtn = tk.Frame(minor_card, bg=T.BG_CARD)
        mbtn.pack(fill="x")
        ttk.Button(mbtn, text="🗑 Remove Selected", style="Ghost.TButton",
                   command=self._remove_minor_tab).pack(side="left")
        ttk.Button(mbtn, text="🗑 Remove All", style="Ghost.TButton",
                   command=self._remove_all_minor_wounds).pack(side="left", padx=(4, 0))

        # ─── Left: Active Major Wounds card ───────────────────────────
        major_border = tk.Frame(left_col, bg=T.BORDER, padx=1, pady=1)
        major_border.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))
        major_card = tk.Frame(major_border, bg=T.BG_CARD, padx=T.PAD, pady=T.PAD)
        major_card.pack(fill="both", expand=True)

        tk.Frame(major_card, bg=T.BLOOD, height=2).pack(fill="x", pady=(0, 6))
        jh = tk.Frame(major_card, bg=T.BG_CARD)
        jh.pack(fill="x", pady=(0, 4))
        tk.Label(jh, text="ACTIVE MAJOR WOUNDS", bg=T.BG_CARD, fg=T.BLOOD,
                 font=T.F_SECTION).pack(side="left")

        self._w_major_lb = tk.Listbox(
            major_card, height=4, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.BLOOD, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.BLOOD,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._w_major_lb.pack(fill="both", expand=True, pady=(0, 6))
        self._w_major_lb.bind("<<ListboxSelect>>",
                              lambda _: self._on_wound_sel("major"))

        jbtn = tk.Frame(major_card, bg=T.BG_CARD)
        jbtn.pack(fill="x")
        ttk.Button(jbtn, text="🗑 Remove Selected", style="Ghost.TButton",
                   command=self._remove_major_tab).pack(side="left")
        ttk.Button(jbtn, text="🗑 Remove All", style="Ghost.TButton",
                   command=self._remove_all_major_wounds).pack(side="left", padx=(4, 0))

        # ─── Right: Minor Wound Effects box ────────────────────────────
        minor_eff_border = tk.Frame(right_col, bg=T.BORDER, padx=1, pady=1)
        minor_eff_border.pack(fill="x", pady=(0, T.PAD_SM))
        self._minor_wound_effect_border = minor_eff_border
        minor_eff_card = tk.Frame(minor_eff_border, bg=T.BG_CARD,
                                  padx=T.PAD_SM, pady=T.PAD_SM)
        minor_eff_card.pack(fill="both", expand=True)
        tk.Frame(minor_eff_card, bg=T.RED, height=2).pack(fill="x", pady=(0, 5))
        meff_hdr = tk.Frame(minor_eff_card, bg=T.BG_CARD)
        meff_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(meff_hdr, text="MINOR WOUND EFFECTS", bg=T.BG_CARD, fg=T.RED,
                 font=T.F_SECTION).pack(side="left")
        self._minor_wound_effect_box = tk.Frame(
            minor_eff_card, bg=T.BG_INSET, highlightthickness=1,
            highlightbackground=T.BORDER)
        self._minor_wound_effect_box.pack(fill="x")
        self._minor_wound_eff_accent = tk.Frame(
            self._minor_wound_effect_box, bg=T.RED, width=5)
        self._minor_wound_eff_accent.pack(side="left", fill="y")
        meff_txt = tk.Frame(self._minor_wound_effect_box, bg=T.BG_INSET,
                            padx=10, pady=8)
        self._minor_wound_eff_text = meff_txt
        meff_txt.pack(side="left", fill="both", expand=True)
        self._minor_wound_eff_title = tk.Label(
            meff_txt, text="Select a wound or add one", bg=T.BG_INSET,
            fg=T.RED, font=T.F_SMALL_B, anchor="w")
        self._minor_wound_eff_title.pack(fill="x")
        self._minor_wound_eff_sub = tk.Label(
            meff_txt, text="", bg=T.BG_INSET, fg=T.TEXT_DIM,
            font=T.F_TINY, anchor="w")
        self._minor_wound_eff_sub.pack(fill="x")
        self._minor_wound_eff_desc = tk.Label(
            meff_txt, text="", bg=T.BG_INSET, fg=T.TEXT,
            font=T.F_SMALL, anchor="nw", wraplength=500, justify="left")
        self._minor_wound_eff_desc.pack(fill="both", expand=True, pady=(4, 0))

        # ─── Right: Major Wound Effects box ────────────────────────────
        major_eff_border = tk.Frame(right_col, bg=T.BORDER, padx=1, pady=1)
        major_eff_border.pack(fill="x", pady=(0, T.PAD_SM))
        self._major_wound_effect_border = major_eff_border
        major_eff_card = tk.Frame(major_eff_border, bg=T.BG_CARD,
                                  padx=T.PAD_SM, pady=T.PAD_SM)
        major_eff_card.pack(fill="both", expand=True)
        tk.Frame(major_eff_card, bg=T.BLOOD, height=2).pack(fill="x", pady=(0, 5))
        jeff_hdr = tk.Frame(major_eff_card, bg=T.BG_CARD)
        jeff_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(jeff_hdr, text="MAJOR WOUND EFFECTS", bg=T.BG_CARD, fg=T.BLOOD,
                 font=T.F_SECTION).pack(side="left")
        self._major_wound_effect_box = tk.Frame(
            major_eff_card, bg=T.BG_INSET, highlightthickness=1,
            highlightbackground=T.BORDER)
        self._major_wound_effect_box.pack(fill="x")
        self._major_wound_eff_accent = tk.Frame(
            self._major_wound_effect_box, bg=T.BLOOD, width=5)
        self._major_wound_eff_accent.pack(side="left", fill="y")
        jeff_txt = tk.Frame(self._major_wound_effect_box, bg=T.BG_INSET,
                            padx=10, pady=8)
        self._major_wound_eff_text = jeff_txt
        jeff_txt.pack(side="left", fill="both", expand=True)
        self._major_wound_eff_title = tk.Label(
            jeff_txt, text="Select a wound or add one", bg=T.BG_INSET,
            fg=T.BLOOD, font=T.F_SMALL_B, anchor="w")
        self._major_wound_eff_title.pack(fill="x")
        self._major_wound_eff_sub = tk.Label(
            jeff_txt, text="", bg=T.BG_INSET, fg=T.TEXT_DIM,
            font=T.F_TINY, anchor="w")
        self._major_wound_eff_sub.pack(fill="x")
        self._major_wound_eff_desc = tk.Label(
            jeff_txt, text="", bg=T.BG_INSET, fg=T.TEXT,
            font=T.F_SMALL, anchor="nw", wraplength=500, justify="left")
        self._major_wound_eff_desc.pack(fill="both", expand=True, pady=(4, 0))

        # ─── Right: Rules section ──────────────────────────────────────
        wrules_border = tk.Frame(right_col, bg=T.BLOOD, padx=1, pady=1)
        wrules_border.pack(fill="both", expand=True)
        rules_card = tk.Frame(wrules_border, bg=T.BG_CARD,
                              padx=T.PAD, pady=T.PAD)
        rules_card.pack(fill="both", expand=True)
        self._build_rules_section(rules_card, WOUND_RULES_TEXT, accent=T.BLOOD)

    # ═══════════════════════════════════════════════════════════════════
    # SPELLS TAB
    # ═══════════════════════════════════════════════════════════════════

    def _build_tab_spells(self, parent):
        # Silver top band - Healing Spells system
        tk.Frame(parent, bg=T.SILVER, height=3).pack(fill="x")

        content = ttk.Frame(parent)
        content.pack(fill="both", expand=True, pady=(T.PAD_SM, 0))

        left_col = ttk.Frame(content)
        left_col.pack(side="left", fill="both", expand=True,
                      padx=(0, T.PAD_SM))
        right_col = ttk.Frame(content)
        right_col.pack(side="right", fill="both", expand=True)

        # ─── LEFT: Minor Restoration ───────────────────────────────────
        minor_border = tk.Frame(left_col, bg=T.SILVER_DK, padx=1, pady=1)
        minor_border.pack(fill="both", expand=True)
        minor_card = tk.Frame(minor_border, bg=T.BG_CARD,
                              padx=T.PAD, pady=T.PAD)
        minor_card.pack(fill="both", expand=True)

        # Header
        mh = ttk.Frame(minor_card, style="Card.TFrame")
        mh.pack(fill="x", pady=(0, T.PAD_SM))
        tk.Label(mh, text="MINOR RESTORATION", bg=T.BG_CARD, fg=T.SILVER_LT,
                 font=T.F_SECTION).pack(side="left")

        # Info block - one property per line
        minfo = tk.Frame(minor_card, bg=T.BG_INSET, padx=8, pady=6)
        minfo.pack(fill="x", pady=(0, T.PAD_SM))
        for line, col in [
            ("2nd-level Abjuration", T.SILVER_LT),
            ("Casting Time: 10 minutes", T.TEXT_DIM),
            ("Range: Touch", T.TEXT_DIM),
            ("Components: V, S", T.TEXT_DIM),
            ("Duration: Instantaneous", T.TEXT_DIM),
            ("Classes: Artificer, Bard, Cleric, Druid, Paladin, Ranger", T.TEXT_DIM),
        ]:
            tk.Label(minfo, text=line, bg=T.BG_INSET, fg=col,
                     font=T.F_SMALL, anchor="w").pack(fill="x")

        # Description
        tk.Frame(minor_card, bg=T.SILVER, height=1).pack(fill="x", pady=(0, 6))
        tk.Label(minor_card,
                 text="You touch a creature and mend lesser afflictions"
                      " of body or mind.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_SMALL,
                 justify="left", wraplength=320).pack(anchor="w", pady=(0, 4))

        tk.Label(minor_card, text="Choose one:",
                 bg=T.BG_CARD, fg=T.TEXT, font=T.F_SMALL_B,
                 justify="left").pack(anchor="w")
        tk.Label(minor_card,
                 text="\u2022  End one Minor Wound affecting the target.\n"
                      "\u2022  End one instance of Long-Term Madness or\n"
                      "    Short-Term Madness affecting the target.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_SMALL,
                 justify="left").pack(anchor="w", padx=(4, 0), pady=(2, 4))
        tk.Label(minor_card,
                 text="This spell has no effect on Major Wounds or"
                      " Indefinite Madness.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_TINY,
                 justify="left", wraplength=320).pack(anchor="w",
                                                      pady=(0, T.PAD_SM))

        # ── Minor Wounds list ─────────────────────────────────
        mwh = ttk.Frame(minor_card, style="Card.TFrame")
        mwh.pack(fill="x", pady=(0, 4))
        tk.Label(mwh, text="MINOR WOUNDS", bg=T.BG_CARD, fg=T.RED,
                 font=T.F_SMALL_B).pack(side="left")

        self._spell_minor_wound_lb = tk.Listbox(
            minor_card, height=4, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.SILVER, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.SILVER_DK,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._spell_minor_wound_lb.pack(fill="x", pady=(0, 4))
        self._spell_minor_wound_lb.bind(
            "<<ListboxSelect>>",
            lambda _: self._on_spell_list_sel("minor_wound"))

        # ── Short/Long-term Madness list ──────────────────────
        mmd = ttk.Frame(minor_card, style="Card.TFrame")
        mmd.pack(fill="x", pady=(T.PAD_SM, 4))
        tk.Label(mmd, text="SHORT / LONG-TERM MADNESS", bg=T.BG_CARD,
                 fg=T.M_LONG, font=T.F_SMALL_B).pack(side="left")

        self._spell_minor_mad_lb = tk.Listbox(
            minor_card, height=4, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.SILVER, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.SILVER_DK,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._spell_minor_mad_lb.pack(fill="x", pady=(0, T.PAD_SM))
        self._spell_minor_mad_lb.bind(
            "<<ListboxSelect>>",
            lambda _: self._on_spell_list_sel("minor_mad"))

        # Cast button
        ttk.Button(minor_card, text="Cast Minor Restoration",
                   style="Silver.TButton",
                   command=self._cast_minor_restoration).pack(fill="x")

        # ─── RIGHT: Major Restoration ──────────────────────────────────
        major_border = tk.Frame(right_col, bg=T.SILVER_DK, padx=1, pady=1)
        major_border.pack(fill="both", expand=True)

        major_card = tk.Frame(major_border, bg=T.BG_CARD,
                              padx=T.PAD, pady=T.PAD)
        major_card.pack(fill="both", expand=True)

        # Header
        jh = ttk.Frame(major_card, style="Card.TFrame")
        jh.pack(fill="x", pady=(0, T.PAD_SM))
        tk.Label(jh, text="MAJOR RESTORATION", bg=T.BG_CARD, fg=T.SILVER_LT,
                 font=T.F_SECTION).pack(side="left")

        # Info block - one property per line
        jinfo = tk.Frame(major_card, bg=T.BG_INSET, padx=8, pady=6)
        jinfo.pack(fill="x", pady=(0, T.PAD_SM))
        for line, col in [
            ("4th-level Abjuration", T.SILVER_LT),
            ("Casting Time: 1 Hour", T.TEXT_DIM),
            ("Range: Touch", T.TEXT_DIM),
            ("Components: V, S, M (nonmagical item \u2265100 gp, destroyed)", T.TEXT_DIM),
            ("Duration: Instantaneous", T.TEXT_DIM),
            ("Classes: Artificer, Bard, Cleric, Druid, Paladin, Ranger", T.TEXT_DIM),
        ]:
            tk.Label(jinfo, text=line, bg=T.BG_INSET, fg=col,
                     font=T.F_SMALL, anchor="w").pack(fill="x")

        # Description
        tk.Frame(major_card, bg=T.SILVER, height=1).pack(fill="x", pady=(0, 6))
        tk.Label(major_card,
                 text="You present an object of personal or material value,"
                      " offering it as sacrifice. The item crumbles to ash as"
                      " restorative magic flows into the creature you touch.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_SMALL,
                 justify="left", wraplength=320).pack(anchor="w", pady=(0, 4))

        tk.Label(major_card, text="Choose one:",
                 bg=T.BG_CARD, fg=T.TEXT, font=T.F_SMALL_B,
                 justify="left").pack(anchor="w")
        tk.Label(major_card,
                 text="\u2022  End one Major Wound affecting the target,\n"
                      "    regenerating any lost body parts.\n"
                      "\u2022  End one instance of Indefinite Madness"
                      " affecting the target.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_SMALL,
                 justify="left").pack(anchor="w", padx=(4, 0), pady=(2, T.PAD_SM))

        # ── Major Wounds list ─────────────────────────────────
        jwh = ttk.Frame(major_card, style="Card.TFrame")
        jwh.pack(fill="x", pady=(0, 4))
        tk.Label(jwh, text="MAJOR WOUNDS", bg=T.BG_CARD, fg=T.STAGE_4,
                 font=T.F_SMALL_B).pack(side="left")

        self._spell_major_wound_lb = tk.Listbox(
            major_card, height=4, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.SILVER, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.SILVER_DK,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._spell_major_wound_lb.pack(fill="x", pady=(0, 4))
        self._spell_major_wound_lb.bind(
            "<<ListboxSelect>>",
            lambda _: self._on_spell_list_sel("major_wound"))

        # ── Indefinite Madness list ───────────────────────────
        imd = ttk.Frame(major_card, style="Card.TFrame")
        imd.pack(fill="x", pady=(T.PAD_SM, 4))
        tk.Label(imd, text="INDEFINITE MADNESS", bg=T.BG_CARD,
                 fg=T.M_INDEF, font=T.F_SMALL_B).pack(side="left")

        self._spell_major_mad_lb = tk.Listbox(
            major_card, height=4, bg=T.BG_INSET, fg=T.TEXT,
            selectbackground=T.SILVER, selectforeground=T.TEXT_BRIGHT,
            highlightthickness=1, highlightbackground=T.SILVER_DK,
            relief="flat", activestyle="none", font=T.F_SMALL, bd=0)
        self._spell_major_mad_lb.pack(fill="x", pady=(0, T.PAD_SM))
        self._spell_major_mad_lb.bind(
            "<<ListboxSelect>>",
            lambda _: self._on_spell_list_sel("major_mad"))

        # CON save note
        tk.Frame(major_card, bg=T.SILVER, height=1).pack(fill="x", pady=(0, 6))
        tk.Label(major_card,
                 text="After the spell is cast, the target must make a"
                      " DC 15 Constitution saving throw.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_TINY,
                 justify="left", wraplength=320).pack(anchor="w", pady=(0, 3))
        tk.Label(major_card,
                 text="\u2022  Success: The restoration succeeds.\n"
                      "\u2022  Failure: The restoration succeeds, but the target\n"
                      "    gains 1 level of exhaustion and cannot benefit from\n"
                      "    this spell again until they complete a Long Rest.",
                 bg=T.BG_CARD, fg=T.TEXT_DIM, font=T.F_TINY,
                 justify="left").pack(anchor="w", padx=(4, 0), pady=(0, T.PAD_SM))

        # Cast button
        ttk.Button(
            major_card, text="Cast Major Restoration",
            style="Silver.TButton",
            command=self._cast_major_restoration).pack(fill="x")

    # ═══════════════════════════════════════════════════════════════════
    # WOUND TAB ACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def _refresh_wounds_tab(self):
        self._w_minor_lb.delete(0, "end")
        minors = self.state.minor_wounds
        for i, w in enumerate(minors):
            self._w_minor_lb.insert("end", f"  {w.description}")
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._w_minor_lb.itemconfigure(i, background=bg, foreground=T.TEXT)
        if not minors:
            self._reset_wound_effect_panel("minor")

        self._w_major_lb.delete(0, "end")
        majors = self.state.major_wounds
        for i, w in enumerate(majors):
            self._w_major_lb.insert("end", f"  {w.description}")
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._w_major_lb.itemconfigure(i, background=bg, foreground=T.TEXT)
        if not majors:
            self._reset_wound_effect_panel("major")

    def _reset_wound_effect_panel(self, severity: str):
        if severity == "minor":
            if not hasattr(self, "_minor_wound_effect_box"):
                return
            self._minor_wound_eff_title.config(text="Select a wound or add one")
            self._minor_wound_eff_sub.config(text="")
            self._minor_wound_eff_desc.config(text="")
            self._minor_wound_eff_accent.config(bg=T.RED)
            self._minor_wound_effect_box.config(bg=T.BG_INSET, highlightbackground=T.BORDER)
            self._minor_wound_eff_text.config(bg=T.BG_INSET)
        else:
            if not hasattr(self, "_major_wound_effect_box"):
                return
            self._major_wound_eff_title.config(text="Select a wound or add one")
            self._major_wound_eff_sub.config(text="")
            self._major_wound_eff_desc.config(text="")
            self._major_wound_eff_accent.config(bg=T.BLOOD)
            self._major_wound_effect_box.config(bg=T.BG_INSET, highlightbackground=T.BORDER)
            self._major_wound_eff_text.config(bg=T.BG_INSET)

    def _on_wound_sel(self, severity):
        lb = self._w_minor_lb if severity == "minor" else self._w_major_lb
        sel = lb.curselection()
        indices = self._get_wound_indices(severity)
        if not sel or sel[0] >= len(indices):
            return
        w = self.state.wounds[indices[sel[0]]]
        lb.config(selectbackground=T.RED if severity == "minor" else T.BLOOD)
        self._show_wound_effect(severity, w.description, w.effect)

    def _get_wound_indices(self, severity):
        return [i for i, w in enumerate(self.state.wounds) if w.severity == severity]

    def _cure_minor_tab(self):
        sel = self._w_minor_lb.curselection()
        indices = self._get_wound_indices("minor")
        if not sel:
            if not indices: return
            idx = indices[-1]
        else:
            idx = indices[sel[0]] if sel[0] < len(indices) else None
        if idx is not None:
            self._push_undo(); r = self.state.wounds.pop(idx)
            self._refresh_wounds_tab()
            self._log(f"🩹 Minor wound cured: {r.description}"); self._save()

    def _cure_major_tab(self):
        sel = self._w_major_lb.curselection()
        indices = self._get_wound_indices("major")
        if not sel:
            if not indices: return
            idx = indices[-1]
        else:
            idx = indices[sel[0]] if sel[0] < len(indices) else None
        if idx is not None:
            self._push_undo(); r = self.state.wounds.pop(idx)
            self._refresh_wounds_tab()
            self._log(f"🩹 Major wound cured: {r.description}"); self._save()

    def _remove_minor_tab(self):
        sel = self._w_minor_lb.curselection()
        indices = self._get_wound_indices("minor")
        if not sel or sel[0] >= len(indices): return
        self._push_undo(); r = self.state.wounds.pop(indices[sel[0]])
        self._refresh_wounds_tab()
        self._log(f"🗑 Removed: {r.description}"); self._save()

    def _remove_major_tab(self):
        sel = self._w_major_lb.curselection()
        indices = self._get_wound_indices("major")
        if not sel or sel[0] >= len(indices): return
        self._push_undo(); r = self.state.wounds.pop(indices[sel[0]])
        self._refresh_wounds_tab()
        self._log(f"🗑 Removed: {r.description}"); self._save()

    # ═══════════════════════════════════════════════════════════════════
    # SPELL TAB ACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def _refresh_spells_tab(self):
        if not hasattr(self, "_spell_minor_wound_lb"):
            return

        # Minor Wounds
        self._spell_minor_wound_lb.delete(0, "end")
        minors = self.state.minor_wounds
        for i, w in enumerate(minors):
            self._spell_minor_wound_lb.insert("end", f"  {w.description}")
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._spell_minor_wound_lb.itemconfigure(i, background=bg, foreground=T.TEXT)

        # Short/Long-term Madnesses
        self._spell_minor_mad_lb.delete(0, "end")
        short_long = [m for m in self.state.madnesses if m.kind in ("short", "long")]
        for i, m in enumerate(short_long):
            label = f"  [{m.kind_label}] {m.name}"
            self._spell_minor_mad_lb.insert("end", label)
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._spell_minor_mad_lb.itemconfigure(i, background=bg,
                                                   foreground=m.kind_color)

        # Major Wounds
        self._spell_major_wound_lb.delete(0, "end")
        majors = self.state.major_wounds
        for i, w in enumerate(majors):
            self._spell_major_wound_lb.insert("end", f"  {w.description}")
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._spell_major_wound_lb.itemconfigure(i, background=bg, foreground=T.TEXT)

        # Indefinite Madnesses
        self._spell_major_mad_lb.delete(0, "end")
        indef = [m for m in self.state.madnesses if m.kind == "indefinite"]
        for i, m in enumerate(indef):
            self._spell_major_mad_lb.insert("end", f"  {m.name}")
            bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)
            self._spell_major_mad_lb.itemconfigure(i, background=bg, foreground=T.M_INDEF)

    def _on_spell_list_sel(self, which: str):
        """When a list gets a selection, clear the other list in the same spell group."""
        if which == "minor_wound":
            self._spell_minor_mad_lb.selection_clear(0, "end")
        elif which == "minor_mad":
            self._spell_minor_wound_lb.selection_clear(0, "end")
        elif which == "major_wound":
            self._spell_major_mad_lb.selection_clear(0, "end")
        elif which == "major_mad":
            self._spell_major_wound_lb.selection_clear(0, "end")

    def _cast_minor_restoration(self):
        wound_sel = self._spell_minor_wound_lb.curselection()
        mad_sel   = self._spell_minor_mad_lb.curselection()
        if not wound_sel and not mad_sel:
            self._err("Nothing selected",
                      "Select a Minor Wound or Short/Long-term Madness to cure.")
            return
        self._push_undo()
        if wound_sel:
            minors = self.state.minor_wounds
            idx = wound_sel[0]
            if idx < len(minors):
                real_indices = [i for i, w in enumerate(self.state.wounds)
                                if w.severity == "minor"]
                removed = self.state.wounds.pop(real_indices[idx])
                self._log(f"✨ Minor Restoration: cured minor wound "
                          f"'{removed.description}'")
                self._refresh_wounds_tab()
        elif mad_sel:
            eligible = [m for m in self.state.madnesses
                        if m.kind in ("short", "long")]
            idx = mad_sel[0]
            if idx < len(eligible):
                target = eligible[idx]
                self.state.madnesses.remove(target)
                self._log(f"✨ Minor Restoration: cured {target.kind_label} "
                          f"madness '{target.name}'")
                self._refresh_madness_display()
        self._refresh_spells_tab()
        self._save()

    def _cast_major_restoration(self):
        wound_sel = self._spell_major_wound_lb.curselection()
        mad_sel   = self._spell_major_mad_lb.curselection()
        if not wound_sel and not mad_sel:
            self._err("Nothing selected",
                      "Select a Major Wound or Indefinite Madness to cure.")
            return
        self._push_undo()
        if wound_sel:
            majors = self.state.major_wounds
            idx = wound_sel[0]
            if idx < len(majors):
                real_indices = [i for i, w in enumerate(self.state.wounds)
                                if w.severity == "major"]
                removed = self.state.wounds.pop(real_indices[idx])
                self._log(f"Major Restoration: cured major wound "
                          f"'{removed.description}'")
                self._refresh_wounds_tab()
        elif mad_sel:
            eligible = [m for m in self.state.madnesses if m.kind == "indefinite"]
            idx = mad_sel[0]
            if idx < len(eligible):
                target = eligible[idx]
                self.state.madnesses.remove(target)
                self._log(f"Major Restoration: cured indefinite madness "
                          f"'{target.name}'")
                self._refresh_madness_display()
        self._refresh_spells_tab()
        self._save()

    # ─── Wound Encounter ──────────────────────────────────────────────

    def _calc_wound_dc(self):
        try: dmg = safe_int(self._wound_dmg_var.get(), lo=0)
        except ValueError:
            self._err("Invalid", "Enter damage as a non-negative integer."); return
        dc = max(10, dmg // 2)
        self._wound_dc_var.set(str(dc))
        self._log(f"⚙ Wound DC = max(10, {dmg}÷2) = {dc}")

    def _wound_encounter(self):
        try: dc = safe_int(self._wound_dc_var.get(), lo=1)
        except ValueError:
            self._err("Invalid", "Enter a valid DC."); return
        try: self.blood_overlay()
        except: pass

        self.wound_enc.reset()
        self.wound_enc.phase = WoundEncPhase.AWAITING_SAVE
        self.wound_enc.dc = dc; self.wound_enc.con_mod_used = self.state.con_mod

        use_adv = getattr(self, "_con_adv_var", None) and self._con_adv_var.get()
        if use_adv:
            r1, r2 = roll_d(20, 1)[0], roll_d(20, 1)[0]
            roll = max(r1, r2)
        else:
            roll = roll_d(20, 1)[0]
        total = roll + self.state.con_mod
        self.wound_enc.roll_total = total

        self._wound_roll_panel.pack(fill="x", pady=(T.PAD_SM, 0))
        if use_adv:
            dice_str = f"d20({r1}, {r2}) → highest({roll})"
        else:
            dice_str = f"d20({roll})"
        self._wound_roll_lbl.config(
            text=f"CON Save: {dice_str} + CON({self.state.con_mod:+d}) = {total}  vs DC {dc}")

        diff = total - dc
        if diff >= 5:
            verdict = "PASSED BY 5+"
            hint = f"Passed by {diff}: No wound!"
            v_color = T.GREEN
            self._wound_result_lbl.config(text=hint, fg=T.GREEN)
        elif diff >= 0:
            verdict = "PASSED"
            hint = f"Passed (by {diff}) → Minor wound"
            v_color = T.GREEN
            self._wound_result_lbl.config(text=hint, fg=T.STAGE_2)
        elif diff > -5:
            verdict = "FAILED"
            hint = f"Failed (by {abs(diff)}) → Major wound"
            v_color = T.RED
            self._wound_result_lbl.config(text=hint, fg=T.RED)
        else:
            verdict = "FAILED BY 5+"
            hint = f"Failed by {abs(diff)}: Major + Exhaustion"
            v_color = T.BLOOD
            self._wound_result_lbl.config(text=hint, fg=T.BLOOD)
        self._wound_roll_big.config(text=f"{verdict}: {total}", fg=v_color)

        # Show hope button only on fail when hope is active
        wound_failed = diff < 0
        if hasattr(self, "_wound_hope_row"):
            if wound_failed and self.state.hope:
                if not self._wound_hope_row_visible:
                    self._wound_hope_row.pack(anchor="w", pady=(6, 0))
                    self._wound_hope_row_visible = True
            else:
                if self._wound_hope_row_visible:
                    self._wound_hope_row.pack_forget()
                    self._wound_hope_row_visible = False

        self._log(f"=== 🩸 WOUND ENCOUNTER: DC {dc} ===")
        if use_adv:
            self._log(f"🎲 CON Save (Advantage): d20({r1}, {r2}) highest({roll}) + {self.state.con_mod:+d} = {total}")
        else:
            self._log(f"🎲 CON Save: d20({roll}) + {self.state.con_mod:+d} = {total}")
        self._log(f"  → {verdict}: {total} vs DC {dc} ({hint})")

    def _wound_resolve(self, result: str):
        self._push_undo()

        if result == "pass5":
            self._log("✓ Passed by 5+ - No wound!")
        elif result == "pass":
            num, name, effect = roll_random_wound("minor")
            self.state.add_wound(name, effect, "minor")
            self._log(f"✓ Passed - Minor #{num}: {name}")
            self._log(f"  → {effect}")
            self._show_wound_effect("minor", name, effect)
            self.after(300, lambda: self._focus_wound_effects("minor"))
        elif result == "fail":
            num, name, effect = roll_random_wound("major")
            self.state.add_wound(name, effect, "major")
            self._log(f"✗ Failed - Major #{num}: {name}")
            self._log(f"  → {effect}")
            self._show_wound_effect("major", name, effect)
            self.after(300, lambda: self._focus_wound_effects("major"))
        elif result == "fail5":
            num, name, effect = roll_random_wound("major")
            self.state.add_wound(name, effect, "major")
            self.state.exhaustion = min(MAX_EXHAUSTION, self.state.exhaustion + 1)
            self._log(f"✗ Failed by 5+ - Major #{num}: {name}")
            self._log(f"  → {effect}")
            self._log(f"  +1 Exhaustion → {self.state.exhaustion}")
            self._draw_exhaustion()
            self._show_wound_effect("major", name, effect)
            self.after(300, lambda: self._focus_wound_effects("major"))

        self.wound_enc.reset()
        self._wound_roll_panel.pack_forget()
        self._wound_roll_lbl.config(text="N/A")
        self._wound_roll_big.config(text="")
        self._wound_result_lbl.config(text="")
        if hasattr(self, "_wound_hope_row") and self._wound_hope_row_visible:
            self._wound_hope_row.pack_forget()
            self._wound_hope_row_visible = False
        self._refresh_wounds_tab(); self._sync_all(); self._save()

    # ─── Log ──────────────────────────────────────────────────────────

    def _build_log(self, parent):
        log_border = tk.Frame(parent, bg=T.BLUE, padx=1, pady=1)
        log_border.pack(fill="x", pady=(T.PAD_SM, 0))
        lf = tk.Frame(log_border, bg=T.BG_CARD, padx=T.PAD, pady=T.PAD)
        lf.pack(fill="both", expand=True)
        top = ttk.Frame(lf, style="Card.TFrame")
        top.pack(fill="x")
        tk.Label(top, text="📜", bg=T.BG_CARD, fg=T.BLUE_LT,
                 font=(T.FONT_FAMILY, 12)).pack(side="left", padx=(0, 6))
        tk.Label(top, text="SESSION LOG", bg=T.BG_CARD, fg=T.BLUE_LT,
                 font=T.F_SECTION).pack(side="left")
        ttk.Button(top, text="Copy", style="Sm.Ghost.TButton",
                   command=self._export_log).pack(side="right")

        self.log_w = tk.Text(lf, height=8, wrap="word", bg=T.BG_INSET,
                             fg=T.TEXT, font=T.F_SMALL, bd=0,
                             highlightthickness=1,
                             highlightbackground=T.BLUE,
                             insertbackground=T.TEXT)
        self.log_w.pack(fill="both", expand=True, pady=(6, 0))
        self.log_w.configure(state="disabled")
        for tag, color in [("warn", T.GOLD), ("skull", T.RED),
                           ("dice", T.BLUE), ("shield", T.GREEN),
                           ("sword", T.STAGE_3), ("dim", T.TEXT_DIM),
                           ("wound", T.BLOOD), ("brain", T.PURPLE),
                           ("fear", T.GOLD), ("sanity", T.PURPLE_LT),
                           ("passed", T.GREEN), ("failed", T.RED)]:
            self.log_w.tag_configure(tag, foreground=color)

    def _log(self, text):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {text}"; self._log_lines.append(line)
        tag = ""
        low = text.lower()
        # System-specific coloring (most specific first)
        if "🩸" in text or "🩹" in text or "wound" in low or "WOUND" in text:
            tag = "wound"
        elif "🧠" in text or "madness" in low or "MADNESS" in text:
            tag = "brain"
        elif "✓" in text or "PASSED" in text:
            tag = "passed"
        elif "✗" in text or "FAILED" in text:
            tag = "failed"
        elif "☠" in text or "ENCOUNTER" in text or "😱" in text or "fear" in low:
            tag = "fear"
        elif "Confront" in text:
            tag = "sword"
        elif "🛡" in text:
            tag = "shield"
        elif ("sanity" in low or "âž-" in text or "âž•" in text or "âš-" in text
              or "Restored" in text or "Loss:" in text or "Recovery:" in text):
            tag = "sanity"
        elif "🎲" in text:
            tag = "dice"
        elif "âš " in text:
            tag = "warn"
        elif "↩" in text or "📜" in text or "📋" in text:
            tag = "dim"
        elif "âš™" in text:
            tag = "dim"
        self.log_w.configure(state="normal")
        self.log_w.insert("end", line + "\n", tag if tag else ())
        self.log_w.see("end"); self.log_w.configure(state="disabled")

    def _export_log(self):
        if self._log_lines:
            self.clipboard_clear()
            self.clipboard_append("\n".join(self._log_lines))
            self._log("📋 Log copied to clipboard.")

    # ─── Feedback ─────────────────────────────────────────────────────

    def _popup_dialog(self, title: str, msg: str, kind: str = "info",
                      yes_no: bool = False, accent: str | None = None) -> bool:
        """Custom dark popup dialog with rounded-card visuals."""
        self.update_idletasks()
        d = tk.Toplevel(self)
        d.transient(self)
        d.title(title)
        d.configure(bg=T.BG_DEEP)
        d.resizable(False, False)
        d.attributes("-topmost", True)

        default_accent = {"error": T.RED, "warn": T.GOLD, "info": T.PURPLE}.get(kind, T.PURPLE)
        accent = accent if accent is not None else default_accent
        icon = {"error": "!", "warn": "!", "info": "i"}.get(kind, "i")

        outer = tk.Frame(d, bg=T.BG_DEEP, padx=10, pady=10)
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, width=460, height=210, bg=T.BG_DEEP,
                       highlightthickness=0, bd=0)
        cv.pack(fill="both", expand=True)

        r = 18
        x1, y1, x2, y2 = 6, 6, 454, 204
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1, x1 + r, y1
        ]
        cv.create_polygon(points, smooth=True, splinesteps=36,
                          fill=T.BG_CARD, outline=T.BORDER, width=1)
        cv.create_rectangle(x1 + 16, y1 + 16, x1 + 44, y1 + 44,
                            fill=accent, outline=accent)
        cv.create_text(x1 + 30, y1 + 30, text=icon, fill=T.TEXT_BRIGHT,
                       font=(T.FONT_FAMILY, 12, "bold"))
        cv.create_text(x1 + 58, y1 + 20, text=title, anchor="w",
                       fill=T.TEXT_BRIGHT, font=T.F_SECTION)

        msg_lbl = tk.Label(cv, text=msg, bg=T.BG_CARD, fg=T.TEXT,
                           justify="left", wraplength=390, font=T.F_SMALL)
        cv.create_window(x1 + 58, y1 + 44, anchor="nw", window=msg_lbl)

        result = {"value": False}
        btn_row = tk.Frame(cv, bg=T.BG_CARD)
        cv.create_window(x2 - 16, y2 - 16, anchor="se", window=btn_row)
        if yes_no:
            ttk.Button(btn_row, text="No", style="Ghost.TButton",
                       command=lambda: (result.update(value=False), d.destroy())
                       ).pack(side="right")
            ttk.Button(btn_row, text="Yes", style="Purple.TButton",
                       command=lambda: (result.update(value=True), d.destroy())
                       ).pack(side="right", padx=(0, 6))
        else:
            ttk.Button(btn_row, text="OK", style="Purple.TButton",
                       command=d.destroy).pack(side="right")

        self._center_window(d)
        d.grab_set()
        d.bind("<Escape>", lambda _e: d.destroy())
        d.wait_window()
        return bool(result["value"])

    def _center_window(self, win: tk.Toplevel):
        self.update_idletasks()
        win.update_idletasks()
        px, py = self.winfo_rootx(), self.winfo_rooty()
        pw, ph = self.winfo_width(), self.winfo_height()
        ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()
        x = px + max(0, (pw - ww) // 2)
        y = py + max(0, (ph - wh) // 2)
        win.geometry(f"+{x}+{y}")

    def _shake(self, s=10, n=8):
        x, y = self.winfo_x(), self.winfo_y()
        def step(i):
            if i <= 0: self.geometry(f"+{x}+{y}"); return
            self.geometry(f"+{x + (s if i % 2 == 0 else -s)}+{y}")
            self.after(30, lambda: step(i - 1))
        step(n)

    def _err(self, title, msg):
        self._shake()
        self._popup_dialog(title, msg, kind="error", yes_no=False)

    # ═══════════════════════════════════════════════════════════════════
    # REFRESH / SYNC
    # ═══════════════════════════════════════════════════════════════════

    def _sync_all(self, bar_from_pct: float | None = None):
        pct = self.state.percent * 100
        self._san_chip.config(
            text=f"🧠  {self.state.current_sanity} / "
                 f"{self.state.max_sanity}")
        if hasattr(self, "_bar"):
            if bar_from_pct is not None:
                self._bar.snap(bar_from_pct)
                self._bar.go(pct)
            else:
                self._bar.snap(pct)
        self._draw_exhaustion()
        self._wis_mod_lbl.config(text=f"MOD {self.state.wis_mod:+d}")
        self._con_mod_lbl.config(text=f"MOD {self.state.con_mod:+d}")
        self._refresh_stages(); self._refresh_wounds_tab()
        self._refresh_madness_display(); self._refresh_spells_tab()

    def _refresh_stages(self):
        for s in range(1, 5):
            i = FEAR_STAGES[s]
            self.stage_tvars[s].set(f"{i.name}  ·  {i.dice}d4")
        n = self._sel_fear()
        if not n:
            self._show_stage_select_prompt()
        else:
            s = int(clamp(self.selected_stage.get(), 1, 4))
            i = FEAR_STAGES[s]
            if hasattr(self, "_stage_effect_title"):
                self._stage_effect_title.config(text=i.name, fg=i.color)
            if hasattr(self, "_stage_effect_detail"):
                self._stage_effect_detail.config(
                    text=i.desc.replace("\n", " "), fg=T.TEXT)
            if hasattr(self, "_stage_effect_accent"):
                self._stage_effect_accent.config(bg=i.color)
        self._update_stage_btn_visuals()
        self._refresh_desens_effects()

    def _show_stage_select_prompt(self):
        if not hasattr(self, "_stage_effect_title"):
            return
        bg = T.BG_INSET
        self._stage_effect_title.config(
            text="Select a fear or add one", fg=T.GOLD, bg=bg)
        self._stage_effect_detail.config(
            text="Fear Severity effects appear here once a fear is selected.",
            fg=T.TEXT_DIM, bg=bg)
        self._stage_effect_accent.config(bg=T.GOLD)
        self._stage_effect_box.config(bg=bg, highlightbackground=T.BORDER)
        self._stage_effect_text.config(bg=bg)

    def _refresh_desens_effects(self):
        """Update the Desensitization Effects panel for the currently selected fear."""
        if not hasattr(self, "_desens_effect_title"):
            return
        n = self._sel_fear()
        if not n:
            self._show_desens_select_prompt()
            return
        r = self.fm.get_desens(n)
        c    = DESENS_RUNG_COLORS[r]
        name = DESENS_NAMES[r]
        desc = (
            f"Rung {r}/4 • Encounter DC {DESENS_DC[r]} • "
            "Confront: +1 rung, Avoid: -1 rung."
        )
        tint = hex_lerp(T.BG_INSET, c, 0.10)
        self._desens_effect_box.config(bg=tint,
                                       highlightbackground=T.GOLD_DK)
        self._desens_effect_text.config(bg=tint)
        self._desens_effect_title.config(text=name, fg=c, bg=tint)
        self._desens_effect_detail.config(
            text=desc,
            fg=T.TEXT, bg=tint)
        self._desens_effect_accent.config(bg=c)

    def _show_desens_select_prompt(self):
        if not hasattr(self, "_desens_effect_title"):
            return
        bg = T.BG_INSET
        self._desens_effect_box.config(bg=bg, highlightbackground=T.GOLD_DK)
        self._desens_effect_text.config(bg=bg)
        self._desens_effect_title.config(
            text="Select a fear or add one", fg=DESENS_COLOR, bg=bg)
        self._desens_effect_detail.config(
            text="Fear Desensitization effects appear here once a fear is selected.",
            fg=T.TEXT_DIM, bg=bg)
        self._desens_effect_accent.config(bg=DESENS_COLOR)

    def _handle_thresh(self, thresh_list: List[Tuple[str, str]]):
        awarded: set[str] = set()
        for label, kind in thresh_list:
            if kind == "zero":
                self._log(f"âš  {label}")
                continue
            if kind in awarded:
                continue
            awarded.add(kind)
            kind_label = {"short": "Short-Term", "long": "Long-Term",
                          "indefinite": "Indefinite"}.get(kind, kind)
            madness_accent = {
                "short": T.M_SHORT, "long": T.M_LONG, "indefinite": T.M_INDEF
            }.get(kind, T.GOLD)
            want_auto = self._popup_dialog(
                "Sanity Threshold Crossed!",
                f"{label}\n\n"
                f"Would you like to automatically add a random {kind_label} Madness-\n\n"
                f"Yes -> Auto-roll a random mandness\n"
                f"No -> Roll a dice and select a maddness from the dropdown menu in the Sanity tab",
                kind="warn", yes_no=True, accent=madness_accent
            )
            if want_auto:
                m = self.state.add_madness(kind)
                self._log(f"⚠ {label} → {m.kind_label} MADNESS")
                self._log(f"  🧠 {m.name}: {m.effect[:80]}")
                self._switch_tab(1)
                def _nav_and_animate(m=m):
                    self._show_madness_effect(
                        m.kind, m.roll_range, m.name or m.kind_label, m.effect)
                    self._focus_madness_effects()
                self.after(200, _nav_and_animate)
            else:
                self._log(f"⚠ {label} → Select a {kind_label} madness from the dropdown.")
                self._switch_tab(1)
        if thresh_list:
            self._refresh_madness_display()

    def _sync_enc_ui(self):
        p = self.enc.phase
        if p == EncounterPhase.IDLE:
            if self._enc_panel_visible:
                self.roll_panel.pack_forget()
                self._enc_panel_visible = False
            self.fail_btn.config(state="disabled")
            self.pass_btn.config(state="disabled")
            self.push_btn.config(state="disabled")
            self.avoid_btn.config(state="disabled")
            self.pend_lbl.config(text=""); self.roll_big.config(text="")
            self.roll_lbl.config(text="N/A")
            self._clear_enc_sanity_preview()
        elif p == EncounterPhase.AWAITING_SAVE:
            if not self._enc_panel_visible:
                self.roll_panel.pack(fill="x", pady=(T.PAD_SM, 0))
                self._enc_panel_visible = True
            self.fail_btn.config(state="normal")
            self.pass_btn.config(state="normal")
            self.push_btn.config(state="disabled")
            self.avoid_btn.config(state="disabled")
            self.pend_lbl.config(text=f"Encounter: {self.enc.fear_name}")
            self._clear_enc_sanity_preview()
        elif p == EncounterPhase.AWAITING_CHOICE:
            if not self._enc_panel_visible:
                self.roll_panel.pack(fill="x", pady=(T.PAD_SM, 0))
                self._enc_panel_visible = True
            self.fail_btn.config(state="disabled")
            self.pass_btn.config(state="disabled")
            self.push_btn.config(state="normal")
            self.avoid_btn.config(state="normal")
            self.pend_lbl.config(
                text=f"Choose: Confront or Avoid  ({self.enc.fear_name})")

    def _clear_enc_sanity_preview(self):
        if hasattr(self, "_enc_formula_push_var"):
            self._enc_formula_push_var.set("Confront: N/A")
        if hasattr(self, "_enc_formula_avoid_var"):
            self._enc_formula_avoid_var.set("Avoid: N/A")
        if hasattr(self, "_enc_formula_push_stage_var"):
            self._enc_formula_push_stage_var.set("")
        if hasattr(self, "_enc_formula_avoid_stage_var"):
            self._enc_formula_avoid_stage_var.set("")
        if hasattr(self, "_enc_formula_push_stage_lbl"):
            self._enc_formula_push_stage_lbl.config(fg=T.TEXT_DIM)
        if hasattr(self, "_enc_formula_avoid_stage_lbl"):
            self._enc_formula_avoid_stage_lbl.config(fg=T.TEXT_DIM)

    def _update_enc_sanity_preview(self, total: int):
        if not hasattr(self, "_enc_formula_push_var"):
            return
        cur = int(self.state.current_sanity)
        max_s = max(1, int(self.state.max_sanity))
        amt = max(0, int(total))

        push_new = max(0, cur - amt)
        avoid_new = min(max_s, cur + amt)

        self._enc_formula_push_var.set(f"Confront: {cur} - {amt} = {push_new}")
        self._enc_formula_avoid_var.set(f"Avoid: {cur} + {amt} = {avoid_new}")

        cur_stage = MadnessStage.from_state(cur / max_s, cur)
        push_stage = MadnessStage.from_state(push_new / max_s, push_new)
        avoid_stage = MadnessStage.from_state(avoid_new / max_s, avoid_new)

        if push_stage != cur_stage:
            self._enc_formula_push_stage_var.set(f"→ {MADNESS[push_stage].title}")
            self._enc_formula_push_stage_lbl.config(fg=MADNESS[push_stage].color)
        else:
            self._enc_formula_push_stage_var.set("No threshold crossed")
            self._enc_formula_push_stage_lbl.config(fg=T.TEXT_DIM)

        if avoid_stage != cur_stage:
            self._enc_formula_avoid_stage_var.set(f"→ {MADNESS[avoid_stage].title}")
            self._enc_formula_avoid_stage_lbl.config(fg=MADNESS[avoid_stage].color)
        else:
            self._enc_formula_avoid_stage_var.set("No threshold crossed")
            self._enc_formula_avoid_stage_lbl.config(fg=T.TEXT_DIM)

    def _end_enc(self):
        self.enc.reset(); self._sync_enc_ui()
        if hasattr(self, "_fear_hope_row") and self._fear_hope_row_visible:
            self._fear_hope_row.pack_forget()
            self._fear_hope_row_visible = False

    def _cancel_enc(self):
        if self.enc.active:
            self._log("âš  Encounter cancelled."); self._end_enc()

    # ─── Fear list ────────────────────────────────────────────────────

    def _refresh_fears(self, keep=None):
        self._refreshing_fear_list = True
        try:
            prev = self._sel_fear()
            # Rebuild text widget content
            txt = self.fear_lb
            txt.config(state="normal")
            txt.delete("1.0", "end")
            # Remove all dynamic per-row tags from previous build
            for tag in list(txt.tag_names()):
                if tag.startswith("_r"):
                    txt.tag_delete(tag)

            names = self.fm.sorted_names
            for i, n in enumerate(names):
                s = self.fm.get_stage(n)
                d = self.fm.get_desens(n)
                sev_col = FEAR_STAGES[s].color
                desens_col = DESENS_RUNG_COLORS[d]
                row_bg = T.BG_INSET if i % 2 == 0 else hex_lerp(T.BG_INSET, T.BG_CARD, 0.5)

                # Tag names unique per row
                t_row = f"_r{i}_bg"
                t_name = f"_r{i}_nm"
                t_bull = f"_r{i}_bl"
                t_sev = f"_r{i}_sv"
                t_bull2 = f"_r{i}_b2"
                t_des = f"_r{i}_ds"

                # Insert segments with their tags
                txt.insert("end", "  ", (t_row,))
                txt.insert("end", n, (t_row, t_name))
                txt.insert("end", "  •  ", (t_row, t_bull))
                txt.insert("end", FEAR_STAGES[s].name, (t_row, t_sev))
                txt.insert("end", "  •  ", (t_row, t_bull2))
                txt.insert("end", DESENS_NAMES[d], (t_row, t_des))
                txt.insert("end", "\n", (t_row,))

                txt.tag_configure(t_row, background=row_bg)
                txt.tag_configure(t_name, foreground=T.TEXT_BRIGHT)
                txt.tag_configure(t_bull, foreground=T.TEXT_DIM)
                txt.tag_configure(t_bull2, foreground=T.TEXT_DIM)
                txt.tag_configure(t_sev, foreground=sev_col)
                txt.tag_configure(t_des, foreground=desens_col)

            txt.config(state="disabled")

            # Determine which fear to select
            selected = None
            if keep and keep in self.fm.fears:
                selected = keep
            elif self._last_selected_fear and self._last_selected_fear in self.fm.fears:
                selected = self._last_selected_fear
            elif prev and prev in self.fm.fears:
                selected = prev
            elif names:
                selected = names[0]

            if selected:
                try:
                    idx = names.index(selected)
                    self._fear_lb_sel = idx
                    self._last_selected_fear = selected
                    self._apply_fear_lb_selection()
                    txt.see(f"{idx + 1}.0")
                    self.selected_stage.set(self.fm.get_stage(selected))
                    self._refresh_stages()
                    self._refresh_desens_tracker()
                    self._refresh_fear_encounter_total_dc()
                except ValueError:
                    pass
            else:
                self._fear_lb_sel = None
                self._last_selected_fear = None
                self._refresh_stages()
                self._refresh_desens_tracker()
                self._refresh_fear_encounter_total_dc()
        finally:
            self._refreshing_fear_list = False

    def _apply_fear_lb_selection(self):
        """Highlight the currently selected row in the fear Text widget."""
        txt = self.fear_lb
        txt.tag_remove("_sel", "1.0", "end")
        if self._fear_lb_sel is not None:
            row = self._fear_lb_sel
            txt.tag_add("_sel", f"{row + 1}.0", f"{row + 2}.0")
            txt.tag_raise("_sel")

    def _on_fear_lb_click(self, event):
        if self._refreshing_fear_list:
            return
        # Determine which line was clicked in the Text widget (1-indexed lines)
        idx_str = self.fear_lb.index(f"@{event.x},{event.y}")
        row = int(idx_str.split(".")[0]) - 1   # convert to 0-indexed
        names = self.fm.sorted_names
        if 0 <= row < len(names):
            self._fear_lb_sel = row
            self._apply_fear_lb_selection()
            self._on_fear_sel()

    def _sel_fear(self):
        if self._fear_lb_sel is None:
            return None
        names = self.fm.sorted_names
        i = self._fear_lb_sel
        return names[i] if 0 <= i < len(names) else None

    # ═══════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def _set_wis(self):
        try: w = safe_int(self.wis_var.get(), lo=WIS_MIN, hi=WIS_MAX)
        except ValueError:
            self._err("Invalid", f"WIS must be {WIS_MIN}-{WIS_MAX}."); return
        self._push_undo(); self.state.wis_score = w
        self.state.recalc_and_reset(); self._end_enc()
        self._log(f"⚙ WIS → {w}. Max sanity = {self.state.max_sanity}.")
        self._sync_all(); self._save()

    def _set_con(self):
        try: c = safe_int(self.con_var.get(), lo=CON_MIN, hi=CON_MAX)
        except ValueError:
            self._err("Invalid", f"CON must be {CON_MIN}-{CON_MAX}."); return
        self._push_undo(); self.state.con_score = c
        self._log(f"⚙ CON → {c}. Modifier = {self.state.con_mod:+d}.")
        self._sync_all(); self._save()

    def _suggest(self):
        s = self.fm.suggest()
        if s: self.fear_var.set(s)
        else: self._log("All pool fears already added.")

    def _add_fear(self):
        err = self.fm.add(self.fear_var.get())
        if err: self._err("Error", err); return
        n = self.fear_var.get().strip(); self._push_undo()
        self.fear_var.set(""); self._refresh_fears(keep=n)
        self.selected_stage.set(1); self._end_enc()
        self._log(f"😱 Added: {n} (Low Severity, Low Desensitization)"); self._save()

    def _remove_fear(self):
        n = self._sel_fear()
        if not n: self._err("None selected", "Select a fear."); return
        self._push_undo(); self.fm.remove(n)
        self._end_enc(); self._refresh_fears()
        self._log(f"🗑 Removed: {n}"); self._save()

    def _remove_all_fears(self):
        if not self.fm.fears: return
        self._push_undo()
        names = list(self.fm.fears.keys())
        for n in names:
            self.fm.remove(n)
        self._end_enc(); self._refresh_fears()
        self._log("🗑 Removed all fears"); self._save()

    def _on_fear_sel(self):
        if self._refreshing_fear_list:
            return
        n = self._sel_fear()
        if not n: return
        self._last_selected_fear = n
        if self.enc.active:
            self._log("âš  Encounter cancelled."); self._end_enc()
        self.selected_stage.set(self.fm.get_stage(n))
        self._refresh_stages()
        self._refresh_desens_tracker()
        self._refresh_fear_encounter_total_dc()

    def _on_stage_change(self):
        if self._refreshing_fear_list:
            return
        n = self._sel_fear()
        if not n: return
        self._push_undo(); s = self.selected_stage.get()
        self.fm.set_stage(n, s); self._refresh_stages()
        self._refresh_fears(keep=n)
        if self.enc.active:
            self._log("âš  Encounter cancelled."); self._end_enc()
        self._log(f"  {n} → {FEAR_STAGES[s].name}"); self._save()

    # ─── Hope ─────────────────────────────────────────────────────────

    def _use_hope_fear(self):
        """Use hope to auto-pass the current fear encounter."""
        self._push_undo()
        self.state.hope = False
        self.hope_var.set(False)
        if hasattr(self, "_fear_hope_row") and self._fear_hope_row_visible:
            self._fear_hope_row.pack_forget()
            self._fear_hope_row_visible = False
        self._log("✦ Hope used — Fear save auto-passed!")
        self._passed()

    def _use_hope_wound(self):
        """Use hope to auto-pass the current wound encounter."""
        self._push_undo()
        self.state.hope = False
        self.hope_var.set(False)
        if hasattr(self, "_wound_hope_row") and self._wound_hope_row_visible:
            self._wound_hope_row.pack_forget()
            self._wound_hope_row_visible = False
        self._log("✦ Hope used — Wound save auto-passed!")
        self._wound_resolve("pass5")

    # ─── Fear Encounter ───────────────────────────────────────────────

    def _encounter(self):
        n = self._sel_fear()
        if not n: self._err("None selected", "Select a fear."); return
        s = self.fm.get_stage(n)
        self.selected_stage.set(s); self._refresh_stages()

        desens_rung = self.fm.get_desens(n)
        desens_dc = DESENS_DC.get(desens_rung, DESENS_DC[1])
        try:
            enc_dc = safe_int(
                getattr(self, "_fear_dc_var",
                        tk.StringVar(value=str(FEAR_ENC_DC))).get(),
                lo=1)
        except (ValueError, AttributeError):
            enc_dc = desens_dc

        if s == 4:
            self._push_undo()
            self.state.exhaustion = min(MAX_EXHAUSTION, self.state.exhaustion + 1)
            self._draw_exhaustion()
            self._log(f"⚠ Extreme Severity encounter → +1 Exhaustion ({self.state.exhaustion})")

        try: self.skull_overlay()
        except: pass

        self.enc.reset()
        self.enc.phase = EncounterPhase.AWAITING_SAVE
        self.enc.fear_name = n; self.enc.fear_stage = s

        use_adv = getattr(self, "_wis_adv_var", None) and self._wis_adv_var.get()
        if use_adv:
            d20a, d20b = roll_d(20, 1)[0], roll_d(20, 1)[0]
            d20 = max(d20a, d20b)
        else:
            d20 = roll_d(20, 1)[0]
        wis_total = d20 + self.state.wis_mod
        self.enc.wis_save_total = wis_total

        self._sync_enc_ui()
        desens_name = DESENS_NAMES[desens_rung]
        extra = "" if enc_dc == desens_dc else f" (Desensitization DC {desens_dc})"
        if use_adv:
            dice_str = f"d20({d20a}, {d20b}) → highest({d20})"
            log_dice = f"d20({d20a}, {d20b}) highest({d20})"
        else:
            dice_str = f"d20({d20})"
            log_dice = f"d20({d20})"
        self.roll_lbl.config(
            text=f"WIS Save: {dice_str} + WIS({self.state.wis_mod:+d})"
                 f" = {wis_total}  vs DC {enc_dc}{extra}")
        passed = wis_total >= enc_dc
        result_text = "PASSED" if passed else "FAILED"
        color = T.GREEN if passed else T.RED
        self.roll_big.config(text=f"{result_text}: {wis_total}", fg=color)

        # Show hope button only on fail when hope is active
        if hasattr(self, "_fear_hope_row"):
            if not passed and self.state.hope:
                if not self._fear_hope_row_visible:
                    self._fear_hope_row.pack(anchor="w", pady=(6, 0))
                    self._fear_hope_row_visible = True
            else:
                if self._fear_hope_row_visible:
                    self._fear_hope_row.pack_forget()
                    self._fear_hope_row_visible = False


        sev_name = FEAR_STAGES[s].name
        self._log(f"=== ☠ ENCOUNTER: {n} ({sev_name}) ===")
        si = FEAR_STAGES[s]
        self._log(f"  Severity effect: {si.desc.split(chr(10))[0]}")
        self._log(f"  Desensitization: {desens_name} (DC {desens_dc})")
        self._log(f"🎲 WIS Save: {log_dice} + {self.state.wis_mod:+d}"
                  f" = {wis_total} vs DC {enc_dc} → {result_text}")

    def _passed(self):
        if not self.enc.active: return
        n = self.enc.fear_name or "N/A"
        self.enc_history.append({"fear": n, "result": "passed",
                                 "time": datetime.now().isoformat()})
        self._log(f"✓ Passed save vs {n}. Encounter ends.")
        self._focus_stage_effects()
        self._end_enc(); self._save()

    def _roll_fail(self):
        if self.enc.phase != EncounterPhase.AWAITING_SAVE:
            self._err("Not ready", "Start an encounter first."); return
        n = self.enc.fear_name
        if n not in self.fm.fears: self._end_enc(); return
        s = self.fm.get_stage(n); self.enc.fear_stage = s
        i = FEAR_STAGES[s]
        rolls = roll_d(4, i.dice); total = sum(rolls)
        rt = " + ".join(map(str, rolls))
        self.enc.roll_total = total
        self.enc.roll_text = f"{i.dice}d4 = {rt} = {total}"
        self.enc.phase = EncounterPhase.AWAITING_CHOICE
        self._sync_enc_ui()
        self.roll_lbl.config(text=self.enc.roll_text)
        self.roll_big.config(text=f"SANITY ROLL: {total}", fg=T.TEXT_BRIGHT)
        self._update_enc_sanity_preview(total)
        self._focus_stage_effects(highlight_actions=True)
        self._log(f"🎲 Sanity roll: {self.enc.roll_text}")
        self._log(f"  Confront = lose {total} sanity, Desensitization +1")
        self._log(f"  Avoid = recover {total} sanity, Severity +1, Desensitization -1")

    def _push(self):
        if self.enc.phase != EncounterPhase.AWAITING_CHOICE: return
        self._push_undo(); loss = self.enc.roll_total or 0
        n = self.enc.fear_name or "N/A"
        old_pct = self.state.percent * 100
        msgs = self.state.apply_loss(loss)
        # Confront: desensitization rung +1 (DC will be harder next encounter)
        old_desens = self.fm.get_desens(n)
        new_desens = self.fm.incr_desens(n)
        self.enc_history.append({"fear": n, "result": "confront", "loss": loss,
                                 "time": datetime.now().isoformat()})
        self._log(f"⚔ Confront ({n}): −{loss} → "
                  f"{self.state.current_sanity}/{self.state.max_sanity}")
        if new_desens != old_desens:
            self._log(f"  Desensitization: {DESENS_NAMES[old_desens]} → "
                      f"{DESENS_NAMES[new_desens]} (DC +{DESENS_DC[new_desens]} next encounter)")
        # Update fear list & desens tracker first so panel shows new rung before animation
        self._refresh_fears(keep=n)
        self._refresh_desens_tracker()
        # Fire desensitization animation - then defer popup + sync until animation has started
        self._focus_desens_effects()
        def _finish_confront():
            self._handle_thresh(msgs)
            if self.state.current_sanity == 0:
                self._log("☠ 0 SANITY - DM controls character.")
            self._sync_all(bar_from_pct=old_pct); self._save(); self._end_enc()
        self.after(160, _finish_confront)

    def _avoid(self):
        if self.enc.phase != EncounterPhase.AWAITING_CHOICE: return
        self._push_undo(); gain = self.enc.roll_total or 0
        n = self.enc.fear_name or "N/A"
        old_pct = self.state.percent * 100
        old_sev = self.fm.get_stage(n)
        # Avoid: desensitization rung -1 (easier DC next encounter) + severity +1
        old_desens = self.fm.get_desens(n)
        new_desens = self.fm.decr_desens(n)
        rec_removed = self.state.apply_recovery(gain)
        new_sev = self.fm.increment_stage(n)
        self.enc_history.append({"fear": n, "result": "avoid", "gain": gain,
                                 "time": datetime.now().isoformat()})
        self._log(f"🛡 Avoid ({n}): +{gain} → "
                  f"{self.state.current_sanity}/{self.state.max_sanity}")
        self._log(f"  Severity: {FEAR_STAGES[old_sev].name} → {FEAR_STAGES[new_sev].name}")
        if new_desens != old_desens:
            self._log(f"  Desensitization: {DESENS_NAMES[old_desens]} → "
                      f"{DESENS_NAMES[new_desens]} (DC +{DESENS_DC[new_desens]} next encounter)")
        self._apply_rec_and_log(rec_removed)
        if old_sev == MAX_FEAR_STAGE:
            nf = self.fm.add_random()
            if nf:
                self._log(f"☠ Extreme Severity Avoid → new fear: {nf}")
                self._switch_tab(0)
                self._refresh_fears(keep=nf)
                self.selected_stage.set(1)
                self._refresh_stages()
                self.after(200, self._focus_stage_effects)
            else:
                self._log("☠ Extreme Severity Avoid - pool exhausted.")
        self._refresh_fears(keep=n)
        self.selected_stage.set(new_sev)
        self._refresh_desens_tracker()
        # Fire desensitization animation after avoid
        self._focus_desens_effects()
        self._sync_all(bar_from_pct=old_pct); self._save(); self._end_enc()

    # ─── Manual sanity ────────────────────────────────────────────────

    def _man_loss(self):
        try: a = safe_int(self.loss_var.get(), lo=0)
        except ValueError:
            self._err("Invalid", "Enter a non-negative integer."); return
        self._push_undo(); old_pct = self.state.percent * 100
        msgs = self.state.apply_loss(a)
        self._log(f"➖ Loss: −{a} → "
                  f"{self.state.current_sanity}/{self.state.max_sanity}")
        self._handle_thresh(msgs)
        if self.state.current_sanity == 0: self._log("☠ 0 SANITY.")
        self._end_enc(); self._sync_all(bar_from_pct=old_pct); self._save()

    def _apply_rec_and_log(self, removed: list):
        """Log and refresh after any recovery that may have cleared madnesses."""
        for _, kind_label, n in removed:
            self._log(f"✨ Above {kind_label} threshold - {n}× {kind_label} "
                      f"madness cleared")
        if removed:
            self._refresh_madness_display()

    def _man_rec(self):
        try: a = safe_int(self.rec_var.get(), lo=0)
        except ValueError:
            self._err("Invalid", "Enter a non-negative integer."); return
        self._push_undo(); old_pct = self.state.percent * 100
        removed = self.state.apply_recovery(a)
        self._log(f"➕ Recovery: +{a} → "
                  f"{self.state.current_sanity}/{self.state.max_sanity}")
        self._apply_rec_and_log(removed)
        self._sync_all(bar_from_pct=old_pct); self._save()

    def _dice_rec(self, n, label):
        self._push_undo(); old_pct = self.state.percent * 100
        rolls = roll_d(4, n); g = sum(rolls)
        removed = self.state.apply_recovery(g)
        r = " + ".join(map(str, rolls)) if n > 1 else str(rolls[0])
        self._log(f"🎲 {label}: +{n}d4 = {r} = {g} → "
                  f"{self.state.current_sanity}/{self.state.max_sanity}")
        if hasattr(self, "_dice_result_var"):
            roll_expr = f"{r} = " if n > 1 else ""
            self._dice_result_var.set(f"+{n}d4 → {roll_expr}+{g} sanity")
        self._apply_rec_and_log(removed)
        self._sync_all(bar_from_pct=old_pct); self._save()

    def _minor_rec(self): self._dice_rec(1, "Minor")
    def _major_rec(self): self._dice_rec(2, "Major")

    def _set_max(self):
        self._push_undo()
        old_pct = self.state.percent * 100
        amt = self.state.max_sanity - self.state.current_sanity
        removed = self.state.apply_recovery(amt)
        self._log(f"Restored to max ({self.state.max_sanity}).")
        self._apply_rec_and_log(removed)
        self._end_enc(); self._sync_all(bar_from_pct=old_pct); self._save()


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()
