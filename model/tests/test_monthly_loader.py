import csv
import io
import zipfile
from pathlib import Path

from data.monthly_loader import load_customer_monthly_spend

COLUMNS = ["기준년월", "발급회원번호", "이용금액_쇼핑", "이용금액_요식", "RP금액_B0M"]


def _month_csv_bytes(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    return buf.getvalue()


def _write_sample_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr(
            "201807_승인매출정보.csv",
            _month_csv_bytes(
                [
                    ["201807", "SYN_0", "140824", "0", "14790"],
                    ["201807", "SYN_1", "215804", "0", "0"],
                ]
            ),
        )
        z.writestr(
            "201808_승인매출정보.csv",
            _month_csv_bytes(
                [
                    ["201808", "SYN_0", "150000", "5000", "14790"],
                    ["201808", "SYN_1", "220000", "0", "0"],
                ]
            ),
        )


def test_load_customer_monthly_spend_picks_one_member_across_months(tmp_path):
    zip_path = tmp_path / "sample.zip"
    _write_sample_zip(zip_path)

    result = load_customer_monthly_spend(
        zip_path,
        ["201807_승인매출정보.csv", "201808_승인매출정보.csv"],
        member_id="SYN_0",
    )

    assert result["shopping"] == [
        {"month": "2018-07", "total_won": 140824},
        {"month": "2018-08", "total_won": 150000},
    ]
    assert result["delivery"] == [
        {"month": "2018-07", "total_won": 0},
        {"month": "2018-08", "total_won": 5000},
    ]
    assert result["subscription"] == [
        {"month": "2018-07", "total_won": 14790},
        {"month": "2018-08", "total_won": 14790},
    ]


def test_load_customer_monthly_spend_ignores_other_members(tmp_path):
    zip_path = tmp_path / "sample.zip"
    _write_sample_zip(zip_path)

    result = load_customer_monthly_spend(
        zip_path,
        ["201807_승인매출정보.csv", "201808_승인매출정보.csv"],
        member_id="SYN_1",
    )

    assert result["shopping"] == [
        {"month": "2018-07", "total_won": 215804},
        {"month": "2018-08", "total_won": 220000},
    ]


def test_load_customer_monthly_spend_unknown_member_returns_empty_series(tmp_path):
    zip_path = tmp_path / "sample.zip"
    _write_sample_zip(zip_path)

    result = load_customer_monthly_spend(
        zip_path,
        ["201807_승인매출정보.csv", "201808_승인매출정보.csv"],
        member_id="SYN_999",
    )

    assert result == {"shopping": [], "delivery": [], "subscription": []}
