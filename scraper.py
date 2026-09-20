#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

API_URL = "https://api.cltvlv.com/api/matches"
OUTPUT_FILE = "cola.m3u"
JAKARTA_TZ = timezone(timedelta(hours=7))


def fetch_json(url: str):
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )

    with urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def process_cola_tv():
    output = []

    try:
        data = fetch_json(API_URL)
    except Exception as exc:
        print(f"Gagal mengambil API: {exc}")
        return output

    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        return output

    for item in data["data"]:
        try:
            timestamp = int(item.get("matchTime", time.time()))
        except (TypeError, ValueError):
            timestamp = int(time.time())

        # Jika timestamp dalam milidetik
        if timestamp > 9_999_999_999:
            timestamp //= 1000

        home = item.get("home_team") or {}
        away = item.get("away_team") or {}
        streams = item.get("anchorAppointmentVoList") or []

        stream_url = ""
        blv_name = "Chính"

        for stream in streams:
            if stream.get("anchorName"):
                blv_name = str(stream["anchorName"])

            for key in (
                "playStreamAddress2",
                "playStreamAddress1",
                "playStreamAddress3",
            ):
                value = stream.get(key)
                if value and ".m3u8" in str(value):
                    stream_url = str(value)
                    break

            if stream_url:
                break

        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(JAKARTA_TZ)

        title = (
            f"{dt:%H:%M} | "
            f"{home.get('name', '')} vs {away.get('name', '')}"
        )

        output.append({
            "time": timestamp,
            "group": "CO LA TV",
            "title": title,
            "logo": home.get("logo", ""),
            "url": stream_url,
            "blv": blv_name,
        })

    return output


def m3u_escape(value) -> str:
    # Hindari karakter yang merusak atribut EXTINF.
    return str(value or "").replace('"', "'").replace("\r", " ").replace("\n", " ")


def save_m3u(channels, filename=OUTPUT_FILE):
    lines = ["#EXTM3U"]

    for channel in channels:
        if not channel.get("url"):
            continue

        title = m3u_escape(channel["title"])
        logo = m3u_escape(channel["logo"])
        group = m3u_escape(channel["group"])
        blv = m3u_escape(channel["blv"])

        lines.append(
            f'#EXTINF:-1 tvg-name="{title}" '
            f'tvg-logo="{logo}" group-title="{group}",'
            f"{title} | BLV: {blv}"
        )
        lines.append(channel["url"])

    Path(filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    channels = process_cola_tv()
    save_m3u(channels, OUTPUT_FILE)

    stream_count = sum(1 for ch in channels if ch.get("url"))
    print(f"Berhasil membuat {OUTPUT_FILE}")
    print(f"Total pertandingan : {len(channels)}")
    print(f"Stream m3u8       : {stream_count}")


if __name__ == "__main__":
    main()
