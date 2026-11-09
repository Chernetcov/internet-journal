from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from iju.templatetags.dates import month_name, rus_date


class RusDateFilterTest(SimpleTestCase):
    def test_datetime(self):
        self.assertEqual(rus_date(datetime(2026, 10, 11)), "11 октября 2026")

    def test_date(self):
        self.assertEqual(rus_date(date(2026, 10, 11)), "11 октября 2026")

    def test_aware_datetime(self):
        value = datetime(2026, 10, 11, 23, 30, tzinfo=ZoneInfo("Europe/Moscow"))
        self.assertEqual(rus_date(value), "11 октября 2026")

    def test_iso_string(self):
        self.assertEqual(rus_date("2026-10-11"), "11 октября 2026")

    def test_iso_string_with_time(self):
        self.assertEqual(rus_date("2026-10-11T23:30:00"), "11 октября 2026")

    def test_none(self):
        self.assertEqual(rus_date(None), "")

    def test_invalid_string(self):
        self.assertEqual(rus_date("не дата"), "не дата")

    def test_all_months_are_declined(self):
        expected = [
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        ]
        actual = [rus_date(date(2026, month, 1)) for month in range(1, 13)]
        self.assertEqual(
            actual,
            [f"1 {month} 2026" for month in expected],
        )

    def test_no_leading_zero_in_day(self):
        self.assertEqual(rus_date(date(2026, 1, 5)), "5 января 2026")


class MonthNameFilterTest(SimpleTestCase):
    def test_datetime(self):
        self.assertEqual(month_name(datetime(2026, 10, 11)), "октября")

    def test_date(self):
        self.assertEqual(month_name(date(2026, 3, 1)), "марта")

    def test_int(self):
        self.assertEqual(month_name(5), "мая")
        self.assertEqual(month_name("12"), "декабря")

    def test_none(self):
        self.assertEqual(month_name(None), "")

    def test_out_of_range(self):
        self.assertEqual(month_name(0), "0")
        self.assertEqual(month_name(13), "13")

    def test_invalid_value(self):
        self.assertEqual(month_name("май"), "май")
