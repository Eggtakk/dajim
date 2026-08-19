# model/

Standalone Python implementation of dajim's data pipeline + spending trend
prediction model (see `../docs/api-and-model-plan.md` §2-2). Independent
from `dajim-web` (Next.js) and `prototype` (static HTML) — no shared code,
just the same category IDs and the same algorithm, ported.

## Setup

```bash
cd model
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in AIHUB_API_KEY yourself
```

## Downloading AI Hub data

Requires `aihubshell` on your PATH and an approved download request for
dataset 71792 (금융 합성 데이터). If `/usr/local/bin` isn't writable without
`sudo`, install it to a user-owned directory instead:

```bash
mkdir -p ~/.local/bin
curl -o ~/.local/bin/aihubshell https://api.aihub.or.kr/api/aihubshell.do
chmod +x ~/.local/bin/aihubshell
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

**Set `AIHUB_FILE_KEYS` before downloading anything.** Dataset 71792 has 74
files across its 12 data types; leaving `AIHUB_FILE_KEYS` empty in `.env`
downloads *all* of them (27M+ records) — that can run long enough to look
hung. List the dataset first to find 카드 승인매출정보's file key, put just
that key in `.env`, then download:

```bash
aihubshell -mode l -datasetkey 71792   # find the 카드 승인매출정보 file key
# .env: AIHUB_FILE_KEYS=<that key>
python -m scripts.fetch_data
```

`fetch_data` doesn't capture `aihubshell`'s output — it prints straight to
your terminal in real time, since it can run for a while and may prompt for
confirmation. If it appears to hang with no output at all, that usually
means `AIHUB_FILE_KEYS` was left empty (see above), not that it's broken.

This was not run end-to-end in the session that wrote this code — no API
key was available. `data/aihub_client.py` builds and runs the `aihubshell`
command; its argument-building is unit tested, and download failures raise
`AihubDownloadError` rather than failing silently.

## Two data paths — read this first

`data/schema.py` (승인일자/가맹점업종코드/승인금액, per-transaction) was written
*before* a real file was available, as a best-effort guess. Once the real
카드 승인매출정보 file was downloaded and inspected (2026-08-19), it turned out
to be structured completely differently — see `data/schema_monthly.py`'s
docstring for the real column names. **Use the monthly path, not
`loader.py`/`schema.py`, for this file:**

- Each monthly CSV (`201807_승인매출정보.csv`, ...) is a **panel of many
  synthetic customers**, one row per (`발급회원번호`, `기준년월`) — not raw
  transactions. Category totals (쇼핑/요식/RP 등) are already pre-aggregated
  as columns; there's nothing to categorize or aggregate into weeks.
- `data/monthly_loader.py`'s `load_customer_monthly_spend()` picks one
  customer's row out of each monthly file and returns their category totals
  as a `MonthlySpendPoint` series (see its docstring / `schema_monthly.py`
  for which AI Hub columns map to which dajim category, and why "cafe"
  isn't derivable from this file).
- `prediction/monthly_trend_model.py`'s `predict_next_month()` fits a
  linear trend over that series and extrapolates one month forward — the
  monthly analogue of `predict_category_trend()`, minus the within-month
  pace-blending (every month here is a closed period, not a partial one).

`loader.py`/`schema.py`/`predict_category_trend()` (the weekly,
per-transaction path) are kept as-is for a data source that actually looks
like that — e.g. a real open-banking/card transaction feed — but they were
never validated against this AI Hub file and most likely don't apply to it.

## Running

```bash
python -m scripts.fetch_data                       # download raw CSVs (see caveat above re: aihubshell's merge step)
python3 -c "
from pathlib import Path
from data.monthly_loader import load_customer_monthly_spend
from prediction.monthly_trend_model import predict_next_month

zip_path = Path('data/raw/.../03.카드_승인매출정보.zip')  # wherever you extracted/merged it
months = [f'2018{m:02d}_승인매출정보.csv' for m in range(7, 13)]
series = load_customer_monthly_spend(zip_path, months, member_id='SYN_0')
for category, points in series.items():
    print(category, predict_next_month(points))
"
```

## Testing

```bash
pytest
```
