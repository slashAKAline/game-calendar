from datetime import datetime

CALENDARS = {
    "genshin.ics": {
        "name": "🩵 原神",
        "events": []
    },
    "starrail.ics": {
        "name": "🩷 崩坏：星穹铁道",
        "events": []
    },
    "zenless.ics": {
        "name": "🧡 绝区零",
        "events": []
    },
    "endfield.ics": {
        "name": "💚 明日方舟：终末地",
        "events": []
    },
    "wuthering.ics": {
        "name": "💙 鸣潮",
        "events": []
    }
}


def escape(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def make_calendar(name, events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Game Calendar//CN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:" + escape(name),
        "X-WR-TIMEZONE:Asia/Kuala_Lumpur",
    ]

    for event in events:
        lines.extend([
            "BEGIN:VEVENT",
            "UID:" + escape(event["uid"]),
            "DTSTAMP:20260915T030000Z",
            "DTSTART:" + event["start"],
            "DTEND:" + event["end"],
            "SUMMARY:" + escape(event["summary"]),
            "DESCRIPTION:" + escape(event.get("description", "")),
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines) + "\n"


for filename, calendar in CALENDARS.items():
    content = make_calendar(
        calendar["name"],
        calendar["events"]
    )

    with open(filename, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    print(f"Generated {filename}")
