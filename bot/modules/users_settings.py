#!/usr/bin/env python3
from datetime import datetime
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex, create
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath, getcwd
from PIL import Image
from time import time
from functools import partial
from html import escape
from io import BytesIO
from asyncio import sleep
from bot import OWNER_ID, bot, user_data, config_dict, DATABASE_URL, IS_PREMIUM_USER, MAX_SPLIT_SIZE
from bot.helper.telegram_helper.message_utils import sendMessage, sendCustomMsg, editMessage, deleteMessage, sendFile, chat_info, user_info, five_minute_del
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManager
from bot.helper.ext_utils.bot_utils import update_user_ldata, get_readable_file_size, sync_to_async, new_thread, is_gdrive_link
from bot import CMD_SUFFIX

handler_dict = {}
desp_dict = {'rcc': ['RClone is a command-line program to sync files and directories to and from different cloud storage providers like GDrive, OneDrive...', 'Send rcl.conf. Timeout: 60 sec'],
            'prefix': ['Filename Prefix is the Front Part attacted with the Filename of the Leech Files.', 'Send Leech Filename Prefix. Timeout: 60 sec'],
            'suffix': ['Filename Suffix is the End Part attached with the Filename of the Leech Files', 'Send Leech Filename Suffix. Timeout: 60 sec'],
            'remname': ['Filename Remname is combination of Regex(s) used for removing or manipulating Filename of the Leech Files', 'Send Leech Filename Remname. Timeout: 60 sec'],
            'lcaption': ['Leech Caption is the Custom Caption on the Leech Files Uploaded by the bot.\n You can change front of your file caption by sending code mentioned here: https://telegram.me/Orginal_File_store_bot?start=Z2V0LTI3ODgwMTg5NDk5NTkxMjI ', 'Send Leech Caption. You can add HTML tags Timeout: 60 sec'],
            'ldump': ['Leech Files User Dump for Personal Use as a Storage.', 'Send Leech Dump Channel ID. Timeout: 60 sec'],
            'thumb': ['Custom Thumbnail to appear on the Leeched files uploaded by the bot , or you can simply add thumbnail by tagging a thumb pic with shortcut commands', 'Send a photo to save it as custom thumbnail. Timeout: 60 sec'],
            'yt_opt': ['YT-DLP Options is the Custom Quality for the extraction of videos from the yt-dlp supported sites.', 'Send YT-DLP Options. Timeout: 60 sec\nFormat: key:value|key:value|key:value.\nExample: format:bv*+mergeall[vcodec=none]|nocheckcertificate:True\nCheck all yt-dlp api options from this <a href="https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184">FILE</a> or use this <a href="https://t.me/mltb_official/177">script</a> to convert cli arguments to api options.'],
            'split_size': ['Leech Splits Size is the size to split the Leeched File before uploading', f'Send Leech split size in bytes. IS_PREMIUM_USER: {IS_PREMIUM_USER}. Timeout: 60 sec'],
            'metadata': ['Metadata will change MKV video files including all audio, streams, and subtitle titles.', 'Send metadata title. Timeout: 60 sec'],
            'user_tds': [f'UserTD helps to upload files via Bot to your Custom Drive Destination through Global SA Mail.\n\n<b>SA Mail:</b> {SA if (SA := config_dict["USER_TD_SA"]) else "Not Specified"}','Send User TD details for use while Mirror/Clone.\n<b>Format:</b> \nname drive_id/link index(optional)\n\n<b>NOTE:</b> \n1. Must add our sa mail in your drive with write permission\n2. Names can have spaces.\n3. Drive ID must be valid for acceptance.\n\n<b>Timeout:</b> 60 sec.'],
            }
fname_dict = {'rcc': 'RClone',
             'prefix': 'Prefix',
             'suffix': 'Suffix',
             'remname': 'Remname',
             'ldump': 'Dump',
             'user_tds': 'User Custom TDs',
             'lcaption': 'Caption',
             'metadata': 'Meetadata',
             'thumb': 'Thumbnail',
             'yt_opt': 'YT-DLP Options',
             'split_size': 'Leech Splits',
             }
async def get_user_settings(from_user, key=None, edit_type=None, edit_mode=None):
    user_id = from_user.id
    name = from_user.mention(style="html")
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    rclone_path = f'tanha/{user_id}.conf'
    user_dict = user_data.get(user_id, {})
    if key is None:
        buttons.ibutton("Universal", f"userset {user_id} universal")
        buttons.ibutton("Mirror", f"userset {user_id} mirror")
        buttons.ibutton("Leech", f"userset {user_id} leech")
        if user_dict and any(key in user_dict for key in ['prefix', 'suffix', 'remname', 'ldump', 'metadata', 'yt_opt', 'media_group', 'equal_splits', 'split_size', 'rclone', 'thumb', 'as_doc']):
            buttons.ibutton("Reset Setting", f"userset {user_id} reset_all")
        buttons.ibutton("Close", f"userset {user_id} close")
        text = f'<b>User Settings for {name}</b>'
        button = buttons.build_menu(2)
    elif key == 'universal':
        buttons.ibutton("YT-DLP Options", f"userset {user_id} yt_opt")
        ytopt = 'Not Exists' if (val:=user_dict.get('yt_opt', config_dict.get('YT_DLP_OPTIONS', ''))) == '' else val
        buttons.ibutton("Prefix", f"userset {user_id} prefix")
        prefix = user_dict.get('prefix', 'Not Exists')
        buttons.ibutton("Suffix", f"userset {user_id} suffix")
        suffix = user_dict.get('suffix', 'Not Exists')
        buttons.ibutton("Remname", f"userset {user_id} remname")
        remname = user_dict.get('remname', 'Not Exists')
        buttons.ibutton("Metadata", f"userset {user_id} metadata")
        metadata = user_dict.get('metadata', 'Not Exists')
        text = f'<b>Universal Settings for {name}</b>\n\n'
        text += f'<b>• YT-DLP Options:</b> <b><code>{ytopt}</code></b>\n'
        text += f'<b>• Prefix:</b> <code>{prefix}</code>\n'
        text += f'<b>• Suffix:</b> <code>{suffix}</code>\n'
        text += f'<b>• Metadata:</b> <code>{metadata}</code>\n'
        text += f'<b>• Remname:</b> <code>{remname}</code>'
        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif key == 'mirror':
        buttons.ibutton("RClone", f"userset {user_id} rcc")
        rccmsg = "Exists" if await aiopath.exists(rclone_path) else "Not Exists"
        tds_mode = "Enabled" if user_dict.get('td_mode') else "Disabled"
        user_tds = len(val) if (val := user_dict.get('user_tds', False)) else 0
        buttons.ibutton("User TDs", f"userset {user_id} user_tds")
        text = f'<b>Mirror Settings for {name}</b>\n\n'
        text += f'<b>• Rclone Config:</b> {rccmsg}\n'
        text += f'<b>• User TD Mode:</b> {tds_mode}'
        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif key == 'leech':
        if user_dict.get('as_doc', False) or 'as_doc' not in user_dict and config_dict['AS_DOCUMENT']:
            ltype = "DOCUMENT"
            buttons.ibutton("Send As Media", f"userset {user_id} doc")
        else:
            ltype = "MEDIA"
            buttons.ibutton("Send As Document", f"userset {user_id} doc")
        mediainfo = "Enabled" if user_dict.get('mediainfo', config_dict['SHOW_MEDIAINFO']) else "Disabled"
        buttons.ibutton('Disable MediaInfo' if mediainfo == 'Enabled' else 'Enable MediaInfo', f"userset {user_id} mediainfo")
        if config_dict['SHOW_MEDIAINFO']:
            mediainfo = "Force Enabled"
        buttons.ibutton("Thumbnail", f"userset {user_id} thumb")
        thumbmsg = "Exists" if await aiopath.exists(thumbpath) else "Not Exists"
        buttons.ibutton("Leech Splits", f"userset {user_id} split_size")
        split_size = get_readable_file_size(config_dict['LEECH_SPLIT_SIZE']) + ' (Default)' if user_dict.get('split_size', '') == '' else get_readable_file_size(user_dict['split_size'])
        equal_splits = 'Enabled' if user_dict.get('equal_splits', config_dict.get('EQUAL_SPLITS')) else 'Disabled'
        media_group = 'Enabled' if user_dict.get('media_group', config_dict.get('MEDIA_GROUP')) else 'Disabled'
        buttons.ibutton("Leech Caption", f"userset {user_id} lcaption")
        lcaption = user_dict.get('lcaption', 'Not Exists')
        buttons.ibutton("Leech Dump", f"userset {user_id} ldump")
        ldump = 'Not Exists' if (val:=user_dict.get('ldump', '')) == '' else val
        text = f'<b>Leech Settings for {name}</b>\n\n'
        text += f'<b>• Leech Type:</b> {ltype}\n'
        text += f'<b>• Custom Thumbnail:</b> {thumbmsg}\n'
        text += f'<b>• Leech Split Size:</b> <code>{split_size}</code>\n'
        text += f'<b>• Equal Splits:</b> {equal_splits}\n'
        text += f'<b>• Media Group:</b> {media_group}\n'
        text += f'<b>• Leech Caption:</b> <code>{escape(lcaption)}</code>\n'
        text += f'<b>• Leech Dump:</b> <code>{ldump}</code>\n'
        text += f'<b>• MediaInfo Mode:</b> <code>{mediainfo}</code>'
        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif edit_type:
        text = f"<b><u>{fname_dict[key]} Settings :</u></b>\n\n"
        if key == 'rcc':
            set_exist = await aiopath.exists(rclone_path)
            text += f"<b>rcl.conf File :</b> {'' if set_exist else 'Not'} Exists\n\n"
        elif key == 'thumb':
            set_exist = await aiopath.exists(thumbpath)
            text += f"<b>Custom Thumbnail :</b> {'' if set_exist else 'Not'} Exists\n\n"
        elif key == 'yt_opt':
            set_exist = 'Not Exists' if (val:=user_dict.get('yt_opt', config_dict.get('YT_DLP_OPTIONS', ''))) == '' else val
            text += f"<b>YT-DLP Options :</b> <code>{escape(set_exist)}</code>\n\n"
        elif key == 'split_size':
            set_exist = get_readable_file_size(config_dict['LEECH_SPLIT_SIZE']) + ' (Default)' if user_dict.get('split_size', '') == '' else get_readable_file_size(user_dict['split_size'])
            text += f"<b>Leech Split Size :</b> {set_exist}\n\n"
            if user_dict.get('equal_splits', False) or ('equal_splits' not in user_dict and config_dict['EQUAL_SPLITS']):
                buttons.ibutton("Disable Equal Splits", f"userset {user_id} esplits", "header")
            else:
                buttons.ibutton("Enable Equal Splits", f"userset {user_id} esplits", "header")
            if user_dict.get('media_group', False) or ('media_group' not in user_dict and config_dict['MEDIA_GROUP']):
                buttons.ibutton("Disable Media Group", f"userset {user_id} mgroup", "header")
            else:
                buttons.ibutton("Enable Media Group", f"userset {user_id} mgroup", "header")
        elif key in ['prefix', 'remname', 'metadata', 'suffix', 'lcaption', 'ldump']:
            set_exist = 'Not Exists' if (val:=user_dict.get(key, '')) == '' else val
            text += f"<b>Filename {fname_dict[key]} :</b> {set_exist}\n\n"
        elif key == 'user_tds':
            set_exist = len(val) if (val:=user_dict.get(key, False)) else 'Not Exists'
            tds_mode = "Enabled" if user_dict.get('td_mode') else "Disabled"
            buttons.ibutton('Disable UserTDs' if tds_mode == 'Enabled' else 'Enable UserTDs', f"userset {user_id} td_mode", "header")
            text += f"<b>User TD Mode:</b> {tds_mode}\n"
        else: 
            return
        text += f"<b>Description :</b> {desp_dict[key][0]}"
        if edit_mode:
            text += '\n\n' + desp_dict[key][1]
            buttons.ibutton("Stop Change", f"userset {user_id} {key}")
        elif key != 'user_tds' or set_exist == 'Not Exists':
            buttons.ibutton(f"Change {fname_dict[key]}" if set_exist and set_exist != 'Not Exists' and (set_exist != get_readable_file_size(config_dict['LEECH_SPLIT_SIZE']) + ' (Default)') else f"Set {fname_dict[key]}", f"userset {user_id} {key} edit")
        if set_exist and set_exist != 'Not Exists' and (set_exist != get_readable_file_size(config_dict['LEECH_SPLIT_SIZE']) + ' (Default)'):
            if key == 'thumb':
                buttons.ibutton("View Thumbnail", f"userset {user_id} vthumb", "header")
            elif key == 'user_tds':
                buttons.ibutton('Show UserTDs', f"userset {user_id} show_tds", "header")
            buttons.ibutton("Delete", f"userset {user_id} d{key}")
        buttons.ibutton("Back", f"userset {user_id} back {edit_type}", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    return text, button

async def update_user_settings(query, key=None, edit_type=None, edit_mode=None, msg=None, sdirect=False):
    msg, button = await get_user_settings(msg.from_user if sdirect else query.from_user, key, edit_type, edit_mode)
    user_id = query.from_user.id
    thumbpath = f"Thumbnails/{user_id}.jpg"
    if not ospath.exists(thumbpath):
        thumbpath = 'https://graph.org/file/e9d1f661f58c7d6aa4370.jpg'
    await editMessage(query if sdirect else query.message, msg, button, photo=thumbpath)
@new_thread
async def user_settings(client, message):
    msg, button = await get_user_settings(message.from_user)
    x = await sendMessage(message, msg, button, photo='https://graph.org/file/e9d1f661f58c7d6aa4370.jpg')
    await five_minute_del(message)
    await deleteMessage(x)

async def set_yt_options(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    update_user_ldata(user_id, 'yt_opt', value)
    await message.delete()
    await update_user_settings(pre_event, 'yt_opt', 'universal')
    if DATABASE_URL:
        await DbManager().update_user_data(user_id)

async def set_custom(client, message, pre_event, key, direct=False):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    return_key = 'leech'
    n_key = key
    user_dict = user_data.get(user_id, {})
    if key == 'user_tds':
        user_tds = user_dict.get(key, {})
        for td_item in value.split('\n'):
            if td_item == '':
                continue
            split_ck = td_item.split()
            td_details = td_item.rsplit(maxsplit=(2 if split_ck[-1].startswith('http') and not is_gdrive_link(split_ck[-1]) else 1 if len(split_ck[-1]) > 15 else 0))
            for title in list(user_tds.keys()):
                if td_details[0].casefold() == title.casefold():
                    del user_tds[title]
            if len(td_details) > 1:
                if is_gdrive_link(td_details[1].strip()):
                    td_details[1] = GoogleDriveHelper.getIdFromUrl(td_details[1])
                if await sync_to_async(GoogleDriveHelper().getFolderData, td_details[1]):
                    user_tds[td_details[0]] = {'drive_id': td_details[1],'index_link': td_details[2].rstrip('/') if len(td_details) > 2 else ''}
        value = user_tds
        return_key = 'mirror'
    update_user_ldata(user_id, n_key, value)
    await message.delete()
    await update_user_settings(pre_event, key, return_key, msg=message, sdirect=direct)
    if DATABASE_URL:
        await DbManager().update_user_data(user_id)

async def set_thumb(client, message, pre_event, key, direct=False):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    path = "Thumbnails/"
    if not await aiopath.isdir(path):
        await mkdir(path)
    photo_dir = await message.download()
    des_dir = ospath.join(path, f'{user_id}.jpg')
    await sync_to_async(Image.open(photo_dir).convert("RGB").save, des_dir, "JPEG")
    await aioremove(photo_dir)
    update_user_ldata(user_id, 'thumb', des_dir)
    await message.delete()
    await update_user_settings(pre_event, key, 'leech', msg=message, sdirect=direct)
    if DATABASE_URL:
        await DbManager().update_user_doc(user_id, 'thumb', des_dir)

async def add_rclone(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    path = f'{getcwd()}/tanha/'
    if not await aiopath.isdir(path):
        await mkdir(path)
    des_dir = ospath.join(path, f'{user_id}.conf')
    await message.download(file_name=des_dir)
    update_user_ldata(user_id, 'rclone', f'tanha/{user_id}.conf')
    await message.delete()
    await update_user_settings(pre_event, 'rcc', 'mirror')
    if DATABASE_URL:
        await DbManager().update_user_doc(user_id, 'rclone', des_dir)

async def leech_split_size(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    sdic = ['b', 'kb', 'mb', 'gb']
    value = message.text.strip()
    slice = -2 if value[-2].lower() in ['k', 'm', 'g'] else -1
    out = value[slice:].strip().lower()
    if out in sdic:
        value = min((float(value[:slice].strip()) * 1024**sdic.index(out)), MAX_SPLIT_SIZE)
    update_user_ldata(user_id, 'split_size', int(round(value)))
    await message.delete()
    await update_user_settings(pre_event, 'split_size', 'leech')
    if DATABASE_URL:
        await DbManager().update_user_data(user_id)

async def event_handler(client, query, pfunc, rfunc, photo=False, document=False):
    user_id = query.from_user.id
    handler_dict[user_id] = True
    start_time = time()
    async def event_filter(_, __, event):
        if photo:
            mtype = event.photo
        elif document:
            mtype = event.document
        else:
            mtype = event.text
        user = event.from_user or event.sender_chat
        return bool(user.id == user_id and event.chat.id == query.message.chat.id and mtype)
    handler = client.add_handler(MessageHandler(
        pfunc, filters=create(event_filter)), group=-1)
    while handler_dict[user_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[user_id] = False
            await rfunc()
    client.remove_handler(*handler)
@new_thread

async def edit_user_settings(client, query):
    from_user = query.from_user
    user_id = from_user.id
    message = query.message
    data = query.data.split()
    thumb_path = f'Thumbnails/{user_id}.jpg'
    rclone_path = f'tanha/{user_id}.conf'
    user_dict = user_data.get(user_id, {})
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    elif data[2] in ['universal', 'mirror', 'leech']:
        await query.answer()
        await update_user_settings(query, data[2])
    elif data[2] == "doc":
        update_user_ldata(user_id, 'as_doc',
                          not user_dict.get('as_doc', False))
        await query.answer()
        await update_user_settings(query, 'leech')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'vthumb':
        handler_dict[user_id] = False
        await query.answer()
        await sendFile(message, thumb_path, from_user.mention)
        await update_user_settings(query, 'thumb', 'leech')
    elif data[2] == 'show_tds':
        handler_dict[user_id] = False
        user_tds = user_dict.get('user_tds', {})
        msg = f'<b><u>User TD(s) Details</u></b>\n\n<b>Total UserTD(s) :</b> {len(user_tds)}\n\n'
        for index_no, (drive_name, drive_dict) in enumerate(user_tds.items(), start=1):
            msg += f'{index_no}: <b>Name:</b> <code>{drive_name}</code>\n'
            msg += f"  <b>Drive ID:</b> <code>{drive_dict['drive_id']}</code>\n"
            msg += f"  <b>Index Link:</b> <code>{ind_url if (ind_url := drive_dict['index_link']) else 'Not Provided'}</code>\n\n"
        try:
            await sendCustomMsg(user_id, msg)
            await query.answer('User TDs Successfully Send in your PM', show_alert=True)
        except:
            await query.answer('Start the Bot in PM (Private) and Try Again', show_alert=True)
        await update_user_settings(query, 'user_tds', 'mirror')
    elif data[2] == "dthumb":
        handler_dict[user_id] = False
        if await aiopath.exists(thumb_path):
            await query.answer()
            await aioremove(thumb_path)
            update_user_ldata(user_id, 'thumb', '')
            await update_user_settings(query, 'thumb', 'leech')
            if DATABASE_URL:
                await DbManager().update_user_doc(user_id, 'thumb')
        else:
            await query.answer("Old Settings", show_alert=True)
            await update_user_settings(query, 'leech')
    elif data[2] == 'thumb':
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'leech', edit_mode)
        if not edit_mode: return
        pfunc = partial(set_thumb, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], 'leech')
        await event_handler(client, query, pfunc, rfunc, True)
    elif data[2] == 'yt_opt':
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'universal', edit_mode)
        if not edit_mode: return
        pfunc = partial(set_yt_options, pre_event=query)
        rfunc = partial(update_user_settings, query, data[2], 'universal')
        await event_handler(client, query, pfunc, rfunc)
    elif data[2] == 'dyt_opt':
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, 'yt_opt', '')
        await update_user_settings(query, 'yt_opt', 'universal')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'td_mode':
        handler_dict[user_id] = False
        if data[2] == 'td_mode' and not user_dict.get('user_tds', False):
            return await query.answer("Set UserTD first to Enable User TD Mode !", show_alert=True)
        await query.answer()
        update_user_ldata(user_id, data[2], not user_dict.get(data[2], False))
        await update_user_settings(query, 'user_tds', 'mirror')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'mediainfo':
        handler_dict[user_id] = False
        if config_dict['SHOW_MEDIAINFO']:
            return await query.answer("Force Enabled! Can't Alter Settings", show_alert=True)
        await query.answer()
        update_user_ldata(user_id, data[2], not user_dict.get(data[2], False))
        await update_user_settings(query, 'leech')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'split_size':
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'leech', edit_mode)
        if not edit_mode: return
        pfunc = partial(leech_split_size, pre_event=query)
        rfunc = partial(update_user_settings, query, data[2], 'leech')
        await event_handler(client, query, pfunc, rfunc)
    elif data[2] == 'dsplit_size':
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, 'split_size', '')
        await update_user_settings(query, 'split_size', 'leech')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'esplits':
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, 'equal_splits', not user_dict.get('equal_splits', False))
        await update_user_settings(query, 'leech')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'mgroup':
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, 'media_group', not user_dict.get('media_group', False))
        await update_user_settings(query, 'leech')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'rcc':
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'mirror', edit_mode)
        if not edit_mode: return
        pfunc = partial(add_rclone, pre_event=query)
        rfunc = partial(update_user_settings, query, data[2], 'mirror')
        await event_handler(client, query, pfunc, rfunc, document=True)
    elif data[2] == 'drcc':
        handler_dict[user_id] = False
        if await aiopath.exists(rclone_path):
            await query.answer()
            await aioremove(rclone_path)
            update_user_ldata(user_id, 'rclone', '')
            await update_user_settings(query, 'rcc', 'mirror')
            if DATABASE_URL:
                await DbManager().update_user_doc(user_id, 'rclone')
        else:
            await query.answer("Old Settings", show_alert=True)
            await update_user_settings(query)
    elif data[2] == 'user_tds':
        handler_dict[user_id] = False
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'mirror', edit_mode)
        if not edit_mode: return
        pfunc = partial(set_custom, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], 'mirror')
        await event_handler(client, query, pfunc, rfunc)
    elif data[2] in ['prefix', 'suffix', 'remname', 'metadata']:
        handler_dict[user_id] = False
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'universal', edit_mode)
        if not edit_mode: return
        pfunc = partial(set_custom, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], 'universal')
        await event_handler(client, query, pfunc, rfunc)
    elif data[2] in ['lcaption', 'ldump']:
        handler_dict[user_id] = False
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], 'leech', edit_mode)
        if not edit_mode: return
        pfunc = partial(set_custom, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], 'leech')
        await event_handler(client, query, pfunc, rfunc)
    elif data[2] in ['dlcaption', 'dldump']:
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, data[2][1:], '')
        await update_user_settings(query, data[2][1:], 'leech')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] in ['dprefix', 'dsuffix', 'dmetadata', 'dremname']:
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, data[2][1:], '')
        await update_user_settings(query, data[2][1:], 'universal')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'duser_tds':
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, data[2][1:], {})
        if data[2] == 'duser_tds':
            update_user_ldata(user_id, 'td_mode', False)
        await update_user_settings(query, data[2][1:], 'mirror')
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == 'back':
        handler_dict[user_id] = False
        await query.answer()
        setting = data[3] if len(data) == 4 else None
        await update_user_settings(query, setting)
    elif data[2] == 'reset_all':
        handler_dict[user_id] = False
        await query.answer()
        buttons = ButtonMaker()
        buttons.ibutton('Yes', f"userset {user_id} reset_now y")
        buttons.ibutton('No', f"userset {user_id} reset_now n")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        await editMessage(message, 'Do you want to Reset Settings ?', buttons.build_menu(2))
    elif data[2] == 'reset_now':
        handler_dict[user_id] = False
        if data[3] == 'n':
            return await update_user_settings(query)
        if await aiopath.exists(thumb_path):
            await aioremove(thumb_path)
        if await aiopath.exists(rclone_path):
            await aioremove(rclone_path)
        await query.answer()
        update_user_ldata(user_id, None, None)
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
            await DbManager().update_user_doc(user_id, 'thumb')
            await DbManager().update_user_doc(user_id, 'rclone')
    elif data[2] == 'user_del':
        user_id = int(data[3])
        await query.answer()
        thumb_path = f'Thumbnails/{user_id}.jpg'
        rclone_path = f'tanha/{user_id}.conf'
        if await aiopath.exists(thumb_path):
            await aioremove(thumb_path)
        if await aiopath.exists(rclone_path):
            await aioremove(rclone_path)
        update_user_ldata(user_id, None, None)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
            await DbManager().update_user_doc(user_id, 'thumb')
            await DbManager().update_user_doc(user_id, 'rclone')
        await editMessage(message, f'Data Reset for {user_id}')
    else:
        handler_dict[user_id] = False
        await query.answer()
        await message.reply_to_message.delete()
        await message.delete()
async def getUserInfo(client, id):
    try:
        return (await client.get_users(id)).mention(style="html")
    except Exception:
        return ''
        
async def send_users_settings(client, message):
    text = message.text.split(maxsplit=1)
    userid = text[1] if len(text) > 1 else None
    if userid and not userid.isdigit():
        userid = None
    elif (reply_to := message.reply_to_message) and reply_to.from_user and not reply_to.from_user.is_bot:
        userid = reply_to.from_user.id
    if not userid:
        msg = f'<u><b>Total Users / Chats Data Saved :</b> {len(user_data)}</u>'
        buttons = ButtonMaker()
        buttons.ibutton("Close", f"userset {message.from_user.id} close")
        button = buttons.build_menu(1)
        for user, data in user_data.items():
            msg += f'\n\n<code>{user}</code>:'
            if data:
                for key, value in data.items():
                    if key in ['token', 'time']:
                        continue
                    msg += f'\n<b>{key}</b>: <code>{escape(str(value))}</code>'
            else:
                msg += "\nUser's Data is Empty!"
        if len(msg.encode()) > 4000:
            with BytesIO(str.encode(msg)) as ofile:
                ofile.name = 'users_settings.txt'
                await sendFile(message, ofile)
        else:
            await sendMessage(message, msg, button)
    elif int(userid) in user_data:
        msg = f'{await getUserInfo(client, userid)} ( <code>{userid}</code> ):'
        if data := user_data[int(userid)]:
            buttons = ButtonMaker()
            buttons.ibutton("Delete Data", f"userset {message.from_user.id} user_del {userid}")
            buttons.ibutton("Close", f"userset {message.from_user.id} close")
            button = buttons.build_menu(1)
            for key, value in data.items():
                if key in ['token', 'time']:
                    continue
                msg += f'\n<b>{key}</b>: <code>{escape(str(value))}</code>'
        else:
            msg += '\nThis User has not Saved anything.'
            button = None
        await sendMessage(message, msg, button)
    else:
        await sendMessage(message, f'{userid} have not saved anything..')
async def user_settings(client, message):
    if len(message.command) > 1 and message.command[1] == '-s':
        set_arg = message.command[2].strip() if len(message.command) > 2 else None
        msg = await sendMessage(message, '<i>Fetching Settings...</i>', photo='IMAGES')
        if set_arg and (reply_to := message.reply_to_message):
            if message.from_user.id != reply_to.from_user.id:
                return await editMessage(msg, '<i>Reply to Your Own Message for Setting via Args Directly</i>')
            if set_arg in ['prefix', 'suffix', 'remname', 'caption', 'dump'] and reply_to.text:
                return await set_custom(client, reply_to, msg, set_arg, True)
            elif set_arg == 'thumb' and reply_to.media:
                return await set_thumb(client, reply_to, msg, set_arg, True)
        await editMessage(msg, f'🌐 <b><u>Available shortcuts:</u></b> \n <b>• Reply to the Value with appropriate arg respectively to set directly without opening UserSet.</b>\n\n<b>💠 Custom Thumbnail :</b>\n   <b>/us{CMD_SUFFIX} -s thumb</b> \n<b>💠 Leech Filename Prefix :</b> \n    <b>/us{CMD_SUFFIX} -s prefix </b> \n<b>💠 Leech Filename Suffix :</b> \n    <b>/us{CMD_SUFFIX} -s suffix </b> \n<b>💠 Leech Filename Remname :</b>\n   <b>/us{CMD_SUFFIX} -s remname </b> \n<b>💠 Leech Filename Caption :</b>\n   <b>/us{CMD_SUFFIX} -s caption </b> \n<b>💠 Leech User Dump :</b>\n   <b>/us{CMD_SUFFIX} -s dump </b>')
    else:
        msg, button = await get_user_settings(message.from_user)
        await sendMessage(message, msg, button, 'IMAGES')
bot.add_handler(MessageHandler(send_users_settings, filters=command(
    BotCommands.UsersCommand) & CustomFilters.sudo))
bot.add_handler(MessageHandler(user_settings, filters=command(
    BotCommands.UserSetCommand) & CustomFilters.authorized_uset))
bot.add_handler(CallbackQueryHandler(edit_user_settings, filters=regex("^userset")))