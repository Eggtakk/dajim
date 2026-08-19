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
