import json
import re
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
    "wuthering.ics": {
        "name": "💙 鸣潮",
        "game": "wuthering",
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


def update_wuthering_calendar(filename):
    base_url = (
        "https://api.github.com/repos/"
        "TheLovinator1/wutheringwaves/contents/articles"
    )

    calendar_events = []

    # Get ALL article pages instead of only the first page.
    page = 1

    while True:
        url = (
            base_url
            + "?ref=master&per_page=100&page="
            + str(page)
        )

        data = fetch_json(url)

        if not isinstance(data, list) or not data:
            break

        for file in data:
            file_url = file.get("download_url")

            if not file_url:
                continue

            if not file.get("name", "").endswith(".json"):
                continue

            try:
                article = fetch_json(file_url)
            except Exception:
                continue

            title = article.get("articleTitle", "")
            start = article.get("startTime", "")
            content = article.get("articleContent", "")

            if not title:
                continue

            # Only keep articles that are useful for the calendar.
            keywords = [
                "Upcoming Events",
                "Featured Resonator",
                "Featured Weapon",
                "Limited-Time",
                "Combat Event",
                "Leisure Event",
                "Exploration Event",
                "Commission Event",
                "Login Event",
                "Double Drop",
                "Double Drop Event",
                "Event Notice",
                "Event Preview",
                "Event",
                "Convene",
                "Version",
                "Patch Notes",
            ]

            if not any(
                keyword.lower() in title.lower()
                for keyword in keywords
            ):
                continue

            start_dt = None
            end_dt = None

            # -------------------------------------------------
            # Try to find the actual event duration in article
            # content.
            #
            # Example:
            # 2026-07-11 10:00 - 2026-08-19 11:59
            # -------------------------------------------------

            duration_patterns = [
                r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*-\s*"
                r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",

                r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*-\s*"
                r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
            ]

            for pattern in duration_patterns:
                match = re.search(
                    pattern,
                    content
                )

                if match:
                    try:
                        start_dt = datetime.strptime(
                            match.group(1),
                            "%Y-%m-%d %H:%M"
                        ).replace(
                            tzinfo=ZoneInfo("Asia/Kuala_Lumpur")
                        )

                        end_dt = datetime.strptime(
                            match.group(2),
                            "%Y-%m-%d %H:%M"
                        ).replace(
                            tzinfo=ZoneInfo("Asia/Kuala_Lumpur")
                        )

                        break

                    except ValueError:
                        try:
                            start_dt = datetime.strptime(
                                match.group(1),
                                "%Y-%m-%d %H:%M:%S"
                            ).replace(
                                tzinfo=ZoneInfo(
                                    "Asia/Kuala_Lumpur"
                                )
                            )

                            end_dt = datetime.strptime(
                                match.group(2),
                                "%Y-%m-%d %H:%M:%S"
                            ).replace(
                                tzinfo=ZoneInfo(
                                    "Asia/Kuala_Lumpur"
                                )
                            )

                            break

                        except ValueError:
                            pass

            # -------------------------------------------------
            # Fallback:
            # If no duration is available, use article startTime.
            # -------------------------------------------------

            if start_dt is None and start:
                try:
                    start_dt = datetime.strptime(
                        start,
                        "%Y-%m-%d %H:%M:%S"
                    ).replace(
                        tzinfo=ZoneInfo(
                            "Asia/Kuala_Lumpur"
                        )
                    )

                    end_dt = start_dt

                except ValueError:
                    continue

            if start_dt is None:
                continue

            if end_dt is None:
                end_dt = start_dt

            article_id = article.get(
                "articleId",
                file.get("name", title)
            )

            calendar_events.append({
                "id": f"wuthering-{article_id}",
                "name": title,
                "start_time": start_dt.timestamp(),
                "end_time": end_dt.timestamp(),
                "description": (
                    "鸣潮活动 / 官方公告\n"
                    + title
                ),
            })

        page += 1

    # Remove duplicates.
    unique_events = {}

    for event in calendar_events:
        unique_events[event["id"]] = event

    calendar_events = list(
        unique_events.values()
    )

    # Sort chronologically.
    calendar_events.sort(
        key=lambda event: event["start_time"]
    )

    print(
        f"wuthering: {len(calendar_events)} events"
    )

    content = make_calendar(
        "💙 鸣潮",
        calendar_events
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(content)

    print(
        f"Generated {filename}"
    )


def main():
    for filename, calendar in CALENDARS.items():
        try:
            if calendar["game"] == "endfield":
                update_endfield_calendar(filename)
            elif calendar["game"] == "wuthering":
                update_wuthering_calendar(filename)
            else:
                update_hoyo_calendar(filename, calendar)
        except Exception as error:
            print(
                f"ERROR updating {filename}: {error}"
            )
            raise



if __name__ == "__main__":
    main()
