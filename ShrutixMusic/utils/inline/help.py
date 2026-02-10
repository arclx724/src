from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutixMusic import nand
from config import SUPPORT_CHAT, START_IMG_URL

# --- 1. MAIN MENU (Vertical Buttons + Back) ---
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
                text=_["BACK_BUTTON"], # Yahan ab 'Back' likha aayega
                callback_data="close"  # Kaam Close ka karega (kyunki isse peeche kuch nahi hai)
            )
        ],
    ]
    return buttons

# --- 2. BACK BUTTON FOR SUB-MENUS ---
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

# --- 3. SECURITY MENU (Vertical/Grid) ---
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
    
