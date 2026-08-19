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

Requires `aihubshell` on your PATH (https://api.aihub.or.kr/api/aihubshell.do)
and an approved download request for dataset 71792 (금융 합성 데이터).

```bash
curl -o /usr/local/bin/aihubshell https://api.aihub.or.kr/api/aihubshell.do
chmod +x /usr/local/bin/aihubshell
python -m scripts.fetch_data
```

This was not run in the session that wrote this code — no API key was
available. `data/aihub_client.py` builds and runs the `aihubshell` command;
its argument-building is unit tested, and download failures raise
`AihubDownloadError` rather than failing silently.

## Column mapping caveat

`data/schema.py` names the 카드 승인매출정보 columns (승인일자/가맹점업종코드/승인금액)
and maps merchant category codes to dajim's four categories. These names/codes
are best-effort based on standard Korean card-transaction terminology, not a
verified copy of AI Hub's real column headers (the detailed schema spreadsheet
requires 안심존/download access this session didn't have). **Before running
`fetch_data`/`run_prediction` against a real downloaded file, run
`head -1 <file>.csv` and update the constants in `data/schema.py` to match.**
Nothing else needs to change — `loader.py` and the tests both import from
`schema.py`, so fixing the constants there is sufficient.

## Running

```bash
python -m scripts.fetch_data                       # download raw CSVs
python -m scripts.run_prediction data/raw/카드승인매출정보.csv  # aggregate + predict
```

## Testing

```bash
pytest
```
