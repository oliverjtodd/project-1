import datetime


class TimeConverter:
    async def humanDate(self):
        fmt = "%d/%m/%Y - %H:%M"
        time = datetime.datetime.now()
        final = time.strftime(fmt)
        return final
