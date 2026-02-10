from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutixMusic import nand
from config import SUPPORT_CHAT

def help_pannel(_, update: Union[CallbackQuery, InlineQuery]):
    first_name = update.from_user.first_name if hasattr(update, "from_user") else update.from_user.first_name
    
    # Ye Main Menu hai (Jo sabse pehle dikhega)
    buttons = [
        [
            InlineKeyboardButton(
                text="🎸 Music Management", callback_data="help_domain_music"
            ),
            InlineKeyboardButton(
                text="🛡️ Group Security", callback_data="help_domain_security"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Back", url=f"https://t.me/{nand.username}?startgroup=true"
            ),
            InlineKeyboardButton(
                text="🛠 Support", url=SUPPORT_CHAT
            ),
        ],
    ]
    return buttons

def help_back_markup(_):
    # Music ke andar ka Back button
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_domain_music", # Wapas Music menu pe layega
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"], callback_data="close"
                )
            ]
        ]
    )

def private_help_panel(_):
    # Start message se jab help khulti hai
    return [
        [
            InlineKeyboardButton(
                text="🎸 Music Management", callback_data="help_domain_music"
            ),
            InlineKeyboardButton(
                text="🛡️ Group Security", callback_data="help_domain_security"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            )
        ],
    ]

# --- SECURITY MENU BUTTONS ---
def security_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text="Anti-Nuke", callback_data="help_cmd_antinuke"),
            InlineKeyboardButton(text="Anti-Bot", callback_data="help_cmd_antibot"),
        ],
        [
            InlineKeyboardButton(text="Anti-Abuse", callback_data="help_cmd_abuse"),
            InlineKeyboardButton(text="Anti-NSFW", callback_data="help_cmd_antinsfw"),
        ],
        [
            InlineKeyboardButton(text="Anti-Edit", callback_data="help_cmd_antiedit"),
            InlineKeyboardButton(text="Auto-Delete", callback_data="help_cmd_autodelete"),
        ],
        [
            InlineKeyboardButton(text="Management", callback_data="help_cmd_management"),
        ],
        [
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settings_back_helper"),
        ]
    ]
    return buttons

def security_back_markup(_):
    # Security ke andar ka Back button
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_domain_security", # Wapas Security menu pe layega
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"], callback_data="close"
                )
            ]
        ]
    )
    
