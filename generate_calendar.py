import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Asia/Kuala_Lumpur")

HOYO_API = "https://api.ennead.cc"


CALENDARS = {
    "genshin.ics": {
        "name": "🩵 原神",
        "game": "genshin",
    },
    "starrail.ics": {
        "name": "🩷 崩坏：星穹铁道",
        "game": "starrail",
    },
    "zenless.ics": {
        "name": "🧡 绝区零",
        "game": "zenless",
    },
    "endfield.ics": {
        "name": "💚 明日方舟：终末地",
        "game": "endfield",
    },
}


def fetch_json(url):
    print(f"Fetching: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "game-calendar/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def escape(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def ics_time(timestamp):
    dt = datetime.fromtimestamp(timestamp, timezone.utc)
    dt = dt.astimezone(TZ)

    return dt.strftime("%Y%m%dT%H%M%S")


def make_calendar(name, events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Game Calendar//Auto//CN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:" + escape(name),
        "X-WR-TIMEZONE:Asia/Kuala_Lumpur",
    ]

    for event in events:
        start = event.get("start_time")
        end = event.get("end_time")

        if not start or not end:
            continue

        event_id = event.get("id", event["name"])

        lines.extend([
            "BEGIN:VEVENT",
            "UID:" + escape(str(event_id) + "@" + name),
            "DTSTAMP:" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "DTSTART;TZID=Asia/Kuala_Lumpur:" + ics_time(start),
            "DTEND;TZID=Asia/Kuala_Lumpur:" + ics_time(end),
            "SUMMARY:" + escape(event["name"]),
            "DESCRIPTION:" + escape(
                event.get("description", "")
            ),
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")

    return "\n".join(lines) + "\n"


def update_hoyo_calendar(filename, calendar):
    game = calendar["game"]

    url = f"{HOYO_API}/mihoyo/{game}/calendar?lang=zh-cn"

    data = fetch_json(url)

    events = data.get("events", [])

    print(f"{game}: {len(events)} events")

    content = make_calendar(
        calendar["name"],
        events
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated {filename}")


def update_endfield_calendar(filename):
    url = (
        "https://ef-cal.mogujun.icu/api/v1/events"
        "?status=upcoming"
    )

    data = fetch_json(url)

    if not data.get("success"):
        raise RuntimeError("Endfield API returned an unsuccessful response")

    events = data.get("data", {}).get("events", [])

    print(f"endfield: {len(events)} events")

    calendar_events = []

    for event in events:
        start = event.get("start")
        end = event.get("end")

        if not start or not end:
            continue

        calendar_events.append({
            "id": event.get("id"),
            "name": event.get("title", "未命名活动"),
            "start_time": datetime.fromisoformat(
                start.replace("Z", "+00:00")
            ).timestamp(),
            "end_time": datetime.fromisoformat(
                end.replace("Z", "+00:00")
            ).timestamp(),
            "description": event.get("description", ""),
        })

    content = make_calendar(
        "💚 明日方舟：终末地",
        calendar_events
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated {filename}")


def main():
    for filename, calendar in CALENDARS.items():
        try:
            if calendar["game"] == "endfield":
                update_endfield_calendar(filename)
            else:
                update_hoyo_calendar(filename, calendar)
        except Exception as error:
            print(
                f"ERROR updating {filename}: {error}"
            )
            raise



if __name__ == "__main__":
    main()
