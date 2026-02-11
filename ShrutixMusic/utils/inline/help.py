from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutixMusic import nand
from config import SUPPORT_CHAT

# --- 1. MAIN MENU (Music/Group Buttons + Back to Home) ---
def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="🎧 Music Management", 
                callback_data="help_domain_music"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🛡️ Group Management", 
                callback_data="help_domain_security"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], # Back -> Home (Start)
                callback_data="settings_back_home"
            )
        ],
    ]
    return buttons

# --- RESTORED FUNCTION: help_pannel ---
def help_pannel(_, update):
    return private_help_panel(_)

# --- 2. BACK BUTTON FOR MUSIC TEXT PAGES ---
# (Yeh button Text Page par dikhega, aur click karne par wapas Grid/Buttons par le jayega)
def help_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_domain_music", # Ye Grid wapas layega
                )
            ]
        ]
    )

# --- 3. SECURITY MENU GRID ---
def security_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text="☢️ Anti Cheater", callback_data="help_cmd_antinuke"),
            InlineKeyboardButton(text="🤖 Anti Bots", callback_data="help_cmd_antibot"),
        ],
        [
            InlineKeyboardButton(text="🤬 Abuse Guardian", callback_data="help_cmd_abuse"),
            InlineKeyboardButton(text="🔞 NSFW Remover", callback_data="help_cmd_antinsfw"),
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Guardian", callback_data="help_cmd_antiedit"),
            InlineKeyboardButton(text="🗑️ Media Guardian", callback_data="help_cmd_autodelete"),
        ],
        [
            InlineKeyboardButton(text="👮 Administration", callback_data="help_cmd_management"),
        ],
        [
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settings_back_helper"),
        ]
    ]
    return buttons

# --- 4. BACK BUTTON FOR SECURITY TEXT PAGES ---
def security_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_domain_security", 
                )
            ]
        ]
    )
    
