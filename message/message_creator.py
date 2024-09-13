from model.models import Color, DiscordRequestMainContent, SpreadsheetData
from scraping.liquipedia import get_picture_from_liquipedia


# 差分を取り、team_name, end_date, roster_status, roleの変更のみ告知する
def create_message_list(
    data_list_update_old: list[SpreadsheetData],
    data_list_update_new: list[SpreadsheetData],
    data_list_added: list[SpreadsheetData],
    data_list_removed: list[SpreadsheetData],
):
    message_list: list[DiscordRequestMainContent] = []

    # updateされたデータをmessage_listに追加
    for index in range(len(data_list_update_new)):
        if data_list_update_new[index] == data_list_update_old[index]:
            break
        data_new = data_list_update_new[index]
        data_old = data_list_update_old[index]
        title_str = ""
        if data_new.team_name != data_old.team_name:
            title_str = "{}({} {}, {}, ex-{}) joined {}".format(
                data_new.handle_name,
                data_new.first_name,
                data_new.family_name,
                data_new.role,
                data_old.team_name,
                data_new.team_name,
            )
        elif data_new.end_date != data_old.end_date:
            title_str = (
                "The end date of {}({} {}, {} in {}) was changed from {} to {}".format(
                    data_new.handle_name,
                    data_new.first_name,
                    data_new.family_name,
                    data_new.role,
                    data_new.team_name,
                    data_old.end_date,
                    data_new.end_date,
                )
            )
        elif data_new.roster_status != data_old.roster_status:
            title_str = "{}({} {}, {} in {}) is {} now".format(
                data_new.handle_name,
                data_new.first_name,
                data_new.family_name,
                data_new.role,
                data_new.team_name,
                data_new.roster_status,
            )
        elif data_new.role != data_old.role:
            title_str = "{}({} {} in {}) changed role from {} to {}".format(
                data_new.handle_name,
                data_new.first_name,
                data_new.family_name,
                data_new.team_name,
                data_old.role,
                data_new.role,
            )
        if title_str != "":
            image_url = get_picture_from_liquipedia(data_new.handle_name)
            message_list.append(
                DiscordRequestMainContent(Color.UPDATE, image_url, title_str)
            )

    # 削除されたデータをmessage_listに追加
    for data in data_list_removed:
        message_list.append(
            DiscordRequestMainContent(
                color=Color.REMOVED,
                image_url=get_picture_from_liquipedia(data.handle_name),
                title="{}({} {}, {}) was removed from {}".format(
                    data.handle_name,
                    data.first_name,
                    data.family_name,
                    data.role,
                    data.team_name,
                ),
            )
        )

    # 追加されたデータをmessage_listに追加
    for data in data_list_added:
        message_list.append(
            DiscordRequestMainContent(
                color=Color.ADDED,
                image_url=get_picture_from_liquipedia(data.handle_name),
                title="{}({} {}, {}) joined {}".format(
                    data.handle_name,
                    data.first_name,
                    data.family_name,
                    data.role,
                    data.team_name,
                ),
            )
        )
    return message_list
