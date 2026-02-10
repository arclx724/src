from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def botplaylist_markup(_, videoid, user_id, ptype, channel, fplay):
    """
    Markup for Playlist Control (Play/Delete)
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"], # Play Button
                callback_data=f"get_playlist_play {videoid}|{user_id}|{ptype}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"], # Delete Button
                callback_data=f"get_playlist_delete {videoid}|{user_id}|{ptype}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def add_playlist_markup(_, videoid, mode, user_id):
    """
    Markup to Add song to Playlist
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=_["PL_B_1"], # Add to Playlist
                callback_data=f"add_playlist {videoid}|{mode}|{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons
  
