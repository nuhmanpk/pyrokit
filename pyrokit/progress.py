import random
import math
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Progress:
    DEFAULT_FINISHED_PROGRESS_STR = "▓"
    DEFAULT_UNFINISHED_PROGRESS_STR = "░"

    COMBINATIONS = [
        ("■", "□"),
        ("▒", "▓"),
        ("◼", "◻"),
        ("▩", "▪"),
        ("⬛", "⬜"),
    ]

    def __init__(self, finished_progress_str=None, unfinished_progress_str=None, random=False):
        if random:
            self.finished_progress_str, self.unfinished_progress_str = random.choice(Progress.COMBINATIONS)
        else:
            if finished_progress_str and unfinished_progress_str:
                self.finished_progress_str = finished_progress_str
                self.unfinished_progress_str = unfinished_progress_str
            else:
                self.finished_progress_str = Progress.DEFAULT_FINISHED_PROGRESS_STR
                self.unfinished_progress_str = Progress.DEFAULT_UNFINISHED_PROGRESS_STR

    def progress_bar(self, current, total):
        percentage = current / total
        finished_length = int(percentage * 10)
        unfinished_length = 10 - finished_length
        progress = f"{self.finished_progress_str * finished_length}{self.unfinished_progress_str * unfinished_length}"
        formatted_percentage = "{:.2f}".format(percentage * 100)
        return progress, formatted_percentage
    
    async def progress_for_pyrogram(current, total, ud_type, message, start):
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚫Cancel", callback_data="cdstoptrasmission")]]
        )
        now = time.time()
        diff = now - start
        if round(diff % 10.00) == 0 or current == total:
            # if round(current / total * 100, 0) % 5 == 0:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion

            elapsed_time = human_readable_time(milliseconds=elapsed_time)
            estimated_total_time = human_readable_time(milliseconds=estimated_total_time)

            progress = "[{0}{1}] \n <b>📊Percentage:</b> {2}%\n".format(
                "".join([self.finished_progress_str for i in range(math.floor(percentage / 5))]),
                "".join([self.unfinished_progress_str for i in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2),
            )

            tmp = (
                progress
                + "<b>✅Completed:</b>{0} \n<b>📁Total Size:</b> {1}\n<b>🚀Speed:</b> {2}/s\n<b>⌚️ETA:</b> {3}\n @BughunterBots".format(
                    human_readable_size(current),
                    human_readable_size(total),
                    human_readable_size(speed),
                    estimated_total_time if estimated_total_time != "" else "0 s",
                )
            )
            try:
                await message.edit(
                    text="{}\n {}".format(ud_type, tmp), reply_markup=reply_markup
                )
            except:
                pass


    def human_readable_size(size):
        if not size:
            return ""
        power = 2**10
        n = 0
        Dic_powerN = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
        while size > power:
            size /= power
            n += 1
        return str(round(size, 2)) + " " + Dic_powerN[n] + "B"


    def human_readable_time(milliseconds: int) -> str:
        seconds, milliseconds = divmod(int(milliseconds), 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        tmp = (
            ((str(days) + "d, ") if days else "")
            + ((str(hours) + "h, ") if hours else "")
            + ((str(minutes) + "m, ") if minutes else "")
            + ((str(seconds) + "s, ") if seconds else "")
            + ((str(milliseconds) + "ms, ") if milliseconds else "")
        )
        return tmp[:-2]
