from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutixMusic import nand
from config import SUPPORT_CHAT

# --- 1. MAIN MENU (Vertical Buttons + Back to Home) ---
def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="🎸 Music Management", 
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
                text=_["BACK_BUTTON"], # "Back" Button
                callback_data="settings_back_home" # Ye Home/Start par le jayega
            )
        ],
    ]
    return buttons

# --- RESTORED FUNCTION: help_pannel ---
def help_pannel(_, update):
    return private_help_panel(_)

# --- 2. BACK BUTTON FOR SUB-MENUS (Music Management ke andar) ---
# Yahan se Close button hata diya gaya hai.
def help_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="settings_back_helper",
                )
            ]
        ]
    )

# --- 3. SECURITY MENU (Group Management Main Page) ---
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

# --- 4. SECURITY BACK BUTTON (Group Management ke andar) ---
# Yahan se bhi Close button hata diya gaya hai.
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
    
