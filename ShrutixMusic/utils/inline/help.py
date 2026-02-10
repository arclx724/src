from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutixMusic import nand
from config import SUPPORT_CHAT

# --- 1. MAIN MENU (The 2 Buttons) ---
def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="🎸 Music Management", callback_data="help_domain_music"
            ),
            InlineKeyboardButton(
                text="🛡️ Group Management", callback_data="help_domain_security"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            )
        ],
    ]
    return buttons

# --- FIX: OLD FUNCTION NAME MAPPING ---
# Ye function start.py dhoondh raha tha, isliye crash hua.
# Hum ise private_help_panel se connect kar denge.
def help_pannel(_, update):
    return private_help_panel(_)

# --- 2. BACK BUTTON ---
def help_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="settings_back_helper",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"], callback_data="close"
                )
            ]
        ]
    )

# --- 3. SECURITY MENU ---
def security_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text="☢️ Anti-Nuke", callback_data="help_cmd_antinuke"),
            InlineKeyboardButton(text="🤖 Anti-Bot", callback_data="help_cmd_antibot"),
        ],
        [
            InlineKeyboardButton(text="🤬 Anti-Abuse", callback_data="help_cmd_abuse"),
            InlineKeyboardButton(text="🔞 Anti-NSFW", callback_data="help_cmd_antinsfw"),
        ],
        [
            InlineKeyboardButton(text="✏️ Anti-Edit", callback_data="help_cmd_antiedit"),
            InlineKeyboardButton(text="🗑️ Auto-Delete", callback_data="help_cmd_autodelete"),
        ],
        [
            InlineKeyboardButton(text="👮‍♂️ Admin Tool", callback_data="help_cmd_management"),
        ],
        [
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settings_back_helper"),
        ]
    ]
    return buttons

# --- 4. SECURITY BACK BUTTON ---
def security_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_domain_security", 
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"], callback_data="close"
                )
            ]
        ]
    )
    
