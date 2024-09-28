from model.models import Color, DiscordRequestMainContent, SpreadsheetData
from scraping.liquipedia import get_picture_from_liquipedia
from discord_utils.discord_message_sender import *

# 差分を取り、team_name, end_date, roster_status, roleの変更のみ告知する
def create_message_list(
    data_list_update_old: list[SpreadsheetData],
    data_list_update_new: list[SpreadsheetData],
    data_list_added: list[SpreadsheetData],
    data_list_removed: list[SpreadsheetData],
    webhook_url: str
):
    message_list: list[DiscordMessageSender] = []

    # updateされたデータをmessage_listに追加
    for index in range(len(data_list_update_new)):
        if data_list_update_new[index] == data_list_update_old[index]:
            break
        data_new = data_list_update_new[index]
        data_old = data_list_update_old[index]
        if data_new.team_name != data_old.team_name:
            message_list.append(DiscordTeamUpdatedMessageSender(
                old_data=data_old, new_data=data_new, webhook_url=webhook_url
            ))
        elif data_new.end_date != data_old.end_date:
            message_list.append(DiscordEndDateUpdatedMessageSender(
                old_data=data_old, new_data=data_new,webhook_url=webhook_url
            ))
        elif data_new.roster_status != data_old.roster_status:
            message_list.append(DiscordRosterUpdatedMessageSender(
                old_data=data_old, new_data=data_new, webhook_url=webhook_url
            ))
        elif data_new.role != data_old.role:
            message_list.append(DiscordRoleUpdatedMessageSender(
                old_data=data_old, new_data=data_new, webhook_url=webhook_url
            ))

    # 削除されたデータをmessage_listに追加
    for data in data_list_removed:
        message_list.append(DiscordDeletedMessageSender(
            data=data, webhook_url=webhook_url
        ))

    # 追加されたデータをmessage_listに追加
    for data in data_list_added:
        message_list.append(DiscordAddedMessageSender(
            data=data, webhook_url=webhook_url
        ))

    return message_list
