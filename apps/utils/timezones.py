from django.utils.translation import gettext


def get_common_timezones():
    # This is an example list of 30 common timezones. You may want to modify it for your own app.
    return [
        "Africa/Cairo",
        "Africa/Johannesburg",
        "Africa/Nairobi",
        "America/Anchorage",
        "America/Argentina/Buenos_Aires",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Mexico_City",
        "America/New_York",
        "America/Sao_Paulo",
        "America/Toronto",
        "Asia/Dubai",
        "Asia/Jerusalem",
        "Asia/Kolkata",
        "Asia/Seoul",
        "Asia/Shanghai",
        "Asia/Singapore",
        "Asia/Tokyo",
        "Australia/Perth",
        "Australia/Sydney",
        "Europe/Amsterdam",
        "Europe/Athens",
        "Europe/Berlin",
        "Europe/Brussels",
        "Europe/London",
        "Europe/Madrid",
        "Europe/Moscow",
        "Europe/Paris",
        "Europe/Rome",
        "Europe/Stockholm",
        "Europe/Vienna",
        "Europe/Zurich",
        "Pacific/Auckland",
        "Pacific/Fiji",
        "Pacific/Honolulu",
        "Pacific/Tongatapu",
        "UTC",
    ]


def get_timezones_display():
    all_tzs = get_common_timezones()
    return zip([""] + all_tzs, [gettext("Not Set")] + all_tzs, strict=False)
