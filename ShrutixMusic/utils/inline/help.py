from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutixMusic import nand
from config import SUPPORT_CHAT

def private_help_panel(_):
    # --- YE HAI WO 2 BUTTONS WALA MENU ---
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

def help_back_markup(_):
    # Music Menu se wapas aane ke liye
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="settings_back_helper", # Wapas 2 buttons pe le jayega
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"], callback_data="close"
                )
            ]
        ]
    )

# --- SECURITY MENU BUTTONS ---
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

def security_back_markup(_):
    # Security Text se wapas Security Menu pe aane ke liye
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
    
