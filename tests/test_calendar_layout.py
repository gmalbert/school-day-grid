from product_routes import WEEKDAY_NAMES, schedule_calendar_weeks


def test_schedule_calendar_weeks_starts_on_sunday_and_keeps_dates_ordered():
    rows = [{"day": f"2026-08-{day:02d}", "kind": "school"} for day in range(27, 32)]
    rows += [{"day": f"2026-09-{day:02d}", "kind": "school"} for day in range(1, 6)]

    weeks = schedule_calendar_weeks(rows)

    assert WEEKDAY_NAMES == ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
    assert weeks[0][:4] == [None, None, None, None]
    assert [cell["display_day"] for cell in weeks[0][4:] if cell] == ["8/27", "8/28", "8/29"]
    assert [cell["display_day"] for cell in weeks[1] if cell] == ["8/30", "8/31", "9/1", "9/2", "9/3", "9/4", "9/5"]
