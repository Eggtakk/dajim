#!/usr/bin/env python3
"""
거래 카테고리 분류기 — 재학습 스크립트

notebooks/train_classifier.ipynb 와 동일한 로직을 셀 없이 한 번에 실행한다.

사용법:
    export DAJIM_SANGGA_DIR="원본_폴더_경로"
    python dajim-ml/scripts/train.py
"""


# ======================================================================
# 거래 카테고리 분류기 — 학습 · 평가 · 아티팩트 생성
# ======================================================================

# ---- CODE 1 --------------------------------------------------
import sys, glob, json, os, time, warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


# ---- 저장소 루트 찾기 ------------------------------------------------------
# 주피터를 어디서 띄우든(notebooks/, dajim-ml/, 저장소 루트) 동작해야 한다.
# 처음에는 Path.cwd().parent 로 고정했는데, VS Code 나 Jupyter Lab 이
# 작업 디렉터리를 다르게 잡으면 그대로 ModuleNotFoundError 가 났다.
# cwd 에서 위로 올라가며 패키지가 있는 위치를 직접 찾는 쪽이 안전하다.
def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "category_classifier" / "__init__.py").exists():
            return p
    raise RuntimeError(
        "category_classifier 패키지를 찾지 못했습니다.\n"
        f"현재 위치: {start}\n"
        "dajim-ml/notebooks/ 안에서 주피터를 실행했는지 확인하세요."
    )


ROOT = find_root(Path.cwd().resolve())
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
pd.set_option("display.width", 160)

from category_classifier.taxonomy import (CATEGORIES, MID_MAP, SUB_OVERRIDE,
                                          code_to_category, korean, ALL_LABELS)
from category_classifier.brands import BRANDS, brand_stats
from category_classifier.classifier import (MerchantClassifier, CharNGramNB,
                                            normalize, build_merchant_dict,
                                            keyword_match)

ART = ROOT / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

print("ROOT         :", ROOT)
print("artifacts    :", ART)
print("카테고리      :", {k: korean(k) for k in ALL_LABELS})
print("브랜드 사전   :", brand_stats(), "| 합계", sum(brand_stats().values()))

# ---- CODE 2 --------------------------------------------------
# ---- 원본 데이터 위치 찾기 --------------------------------------------------
# 원본(약 1.5GB)은 저장소에 없다. 아래 순서로 찾는다.
#   1순위  환경변수 DAJIM_SANGGA_DIR
#   2순위  흔히 두는 위치들을 자동 탐색 (하위 폴더 한 단계까지)
#
# 예전에는 곧바로 pd.concat(...) 을 호출했는데, 경로가 틀리면
# 파일 목록이 빈 리스트가 되어 "No objects to concatenate" 라는
# 원인을 알 수 없는 에러가 났다. 무엇을 어디서 찾았는지 먼저 알려준다.
REQUIRED = ["상호명", "상권업종소분류코드", "상권업종소분류명"]


def find_data_dir() -> Path:
    env = os.environ.get("DAJIM_SANGGA_DIR")
    candidates = ([Path(env).expanduser()] if env else []) + [
        ROOT / "data",
        ROOT.parent / "data",
        ROOT.parent.parent / "data",
        Path.home() / "Downloads",
    ]
    tried = []
    for c in candidates:
        if not c.exists():
            tried.append(f"  ✗ {c}  (폴더 없음)")
            continue
        if glob.glob(str(c / "*.csv")):
            return c
        subs = [d for d in sorted(c.iterdir())
                if d.is_dir() and glob.glob(str(d / "*.csv"))]
        if subs:
            return subs[0]
        tried.append(f"  ✗ {c}  (csv 없음)")

    raise FileNotFoundError(
        "상가(상권)정보 CSV 를 찾지 못했습니다.\n\n"
        "찾아본 곳:\n" + "\n".join(tried) + "\n\n"
        "해결 방법 — 터미널에서 아래를 실행한 뒤 주피터를 다시 시작하세요.\n"
        '  export DAJIM_SANGGA_DIR="원본_폴더_경로"\n\n'
        "원본이 없다면 재학습을 건너뛰고 artifacts/ 에 커밋된 모델을 쓰면 됩니다.\n"
        "  https://www.data.go.kr/data/15083033/fileData.do"
    )


DATA_DIR = find_data_dir()
files = sorted(glob.glob(str(DATA_DIR / "*.csv")))
print(f"데이터 위치: {DATA_DIR}")
print(f"CSV {len(files)}개 발견")

# 스키마 확인 — 첫 파일의 헤더만 읽어 필요한 컬럼이 있는지 본다
head = pd.read_csv(files[0], nrows=0, encoding="utf-8")
missing = [c for c in REQUIRED if c not in head.columns]
if missing:
    raise ValueError(
        f"필요한 컬럼이 없습니다: {missing}\n"
        f"이 파일의 컬럼: {list(head.columns)[:10]} ...\n"
        "상가(상권)정보가 아닌 다른 CSV 를 가리키고 있을 수 있습니다."
    )

t0 = time.time()
df = pd.concat([pd.read_csv(f, usecols=REQUIRED, encoding="utf-8",
                            low_memory=False) for f in files],
               ignore_index=True)
print(f"{len(df):,}건 적재 ({time.time()-t0:.1f}초)")
df.head(3)

# ---- CODE 3 --------------------------------------------------
df["category"] = df["상권업종소분류코드"].map(code_to_category)

dist = (df["category"].value_counts(normalize=True) * 100).round(2)
dist_df = pd.DataFrame({"비율(%)": dist, "건수": df["category"].value_counts()})
dist_df["한글"] = [korean(i) for i in dist_df.index]
print(dist_df.to_string())

# ======================================================================
# ⚠️ 여기서 반드시 짚어야 할 사실
# ======================================================================

# ---- CODE 4 --------------------------------------------------
# 카테고리별 대표 업종 확인 — 매핑이 상식과 맞는지 눈으로 검증
for cat in ["food", "shopping", "leisure", "transport", "living", "other"]:
    top = (df[df.category == cat]["상권업종소분류명"]
           .value_counts().head(6).index.tolist())
    print(f"{korean(cat):6s} ({cat:9s}) ← {', '.join(top)}")

# ---- CODE 5 --------------------------------------------------
demo = ["(주)스타벅스커피코리아 강남2호점", "김밥천국 역삼점", "GS25 서울대점",
        "㈜배달의민족", "NETFLIX.COM", "올리브영 홍대점 1층"]
pd.DataFrame({"원본": demo, "정규화": [normalize(x) for x in demo]})

# ---- CODE 6 --------------------------------------------------
t0 = time.time()
df["norm"] = df["상호명"].map(normalize)
df = df[df["norm"].str.len() >= 2].copy()
print(f"정규화 완료 ({time.time()-t0:.1f}초) | {len(df):,}건 / 고유 상호명 {df['norm'].nunique():,}개")

# ---- CODE 7 --------------------------------------------------
# 고유 상호명 → 최빈 카테고리 (groupby.apply 는 느려서 value_counts 방식 사용)
vc = df.groupby(["norm", "category"]).size().reset_index(name="n")
vc = vc.sort_values("n", ascending=False).drop_duplicates("norm")
uniq = vc[["norm", "category"]].reset_index(drop=True)

rng = np.random.default_rng(42)
mask = rng.random(len(uniq)) < 0.80
train_names = set(uniq.loc[mask, "norm"])
test_names = set(uniq.loc[~mask, "norm"])
print(f"train 고유명 {len(train_names):,} / test 고유명 {len(test_names):,}")

train_df = df[df["norm"].isin(train_names)]
test_df = df[df["norm"].isin(test_names)].drop_duplicates("norm")
print(f"train 행 {len(train_df):,} / test 행 {len(test_df):,}")

# ---- CODE 8 --------------------------------------------------
t0 = time.time()
merchant_dict = build_merchant_dict(
    train_df["norm"].tolist(), train_df["category"].tolist(),
    min_count=3, min_purity=0.80)
print(f"사전 등재 {len(merchant_dict):,}개 ({time.time()-t0:.1f}초)")

md_cat = Counter(v[0] for v in merchant_dict.values())
print({korean(k): v for k, v in md_cat.most_common()})

# 순도 때문에 탈락한 이름 예시
# (groupby.apply 에 lambda 를 쓰면 147만 그룹에서 몇 분씩 걸린다. 벡터 연산으로 처리)
g = train_df.groupby(["norm", "category"]).size().reset_index(name="n")
g["total"] = g.groupby("norm")["n"].transform("sum")
best = g.sort_values("n", ascending=False).drop_duplicates("norm")
best["purity"] = best["n"] / best["total"]
rejected = best[(best["total"] >= 20) & (best["purity"] < 0.80)] \
    .sort_values("total", ascending=False)
print("\n[순도 미달로 사전에서 제외된 상호명 — 여러 업종에 걸쳐 있어 확신할 수 없음]")
print(rejected.head(10)[["norm", "total", "category", "purity"]].round(2).to_string(index=False))

# ---- CODE 9 --------------------------------------------------
ml_train = uniq[uniq["norm"].isin(train_names)]
SAMPLE = 400_000                       # 롱테일 폴백이므로 전량 학습이 필요하지 않다
if len(ml_train) > SAMPLE:
    ml_train = ml_train.sample(SAMPLE, random_state=42)

t0 = time.time()
model = CharNGramNB(ngram_range=(2, 4), n_buckets=1 << 18, alpha=0.2, temperature=8.0)
model.fit(ml_train["norm"].tolist(), ml_train["category"].tolist())
print(f"학습 {len(ml_train):,}건 / {time.time()-t0:.1f}초 / 클래스 {model.classes_}")

# ======================================================================
# 신뢰도 보정 — 처음엔 전부 0.9999가 나왔다
# ======================================================================

# ---- CODE 10 --------------------------------------------------
probe = ["행복한동네정육", "별빛헤어살롱", "현대오토서비스", "한빛수학전문",
         "zzqx", "김철수", "ㅁㄴㅇㄹ"]
pd.DataFrame([{"입력": t, "예측": korean(model.predict_one(t)[0]),
               "신뢰도": round(model.predict_one(t)[1], 3)} for t in probe])

# ---- CODE 11 --------------------------------------------------
clf = MerchantClassifier(merchant_dict=merchant_dict, model=model, ml_threshold=0.45)

t0 = time.time()
preds = clf.predict_many(test_df["상호명"].tolist())
print(f"추론 {len(preds):,}건 / {time.time()-t0:.1f}초 "
      f"({len(preds)/(time.time()-t0):,.0f}건/초)")

res = pd.DataFrame(preds)
res["true"] = test_df["category"].values
res["correct"] = res["category"] == res["true"]

# ---- CODE 12 --------------------------------------------------
# ---- 단계별 커버리지 & 정확도 ----
layer = res.groupby("layer").agg(
    건수=("correct", "size"),
    정확도=("correct", "mean"),
).reset_index()
layer["커버리지(%)"] = (layer["건수"] / len(res) * 100).round(2)
layer["정확도"] = layer["정확도"].round(4)
layer = layer.sort_values("건수", ascending=False)
print(layer.to_string(index=False))

known = res[res["category"] != "unknown"]
print(f"\n전체 정확도(미분류 포함) : {res['correct'].mean():.4f}")
print(f"분류된 건만의 정확도      : {known['correct'].mean():.4f}")
print(f"미분류율                 : {(res['category']=='unknown').mean():.4f}")

# ---- CODE 13 --------------------------------------------------
# ---- 카테고리별 Precision / Recall / F1 ----
def prf(res):
    rows = []
    for c in sorted(set(res["true"]) | set(res["category"])):
        if c == "unknown":
            continue
        tp = ((res["category"] == c) & (res["true"] == c)).sum()
        fp = ((res["category"] == c) & (res["true"] != c)).sum()
        fn = ((res["true"] == c) & (res["category"] != c)).sum()
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        rows.append({"카테고리": korean(c), "code": c, "support": int(tp + fn),
                     "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)})
    return pd.DataFrame(rows).sort_values("support", ascending=False)

prf_df = prf(res)
print(prf_df.to_string(index=False))

# support 가 0인 클래스를 macro 평균에 넣으면 안 된다.
# delivery·subscription 은 '모델이 못 맞힌 것'이 아니라 '평가할 데이터가 없는 것'이다.
# 이 둘을 0점으로 넣으면 macro-F1 이 0.53 으로 떨어져 실제보다 나쁘게 보인다.
evaluable = prf_df[prf_df["support"] > 0]
print(f"\n평가 가능한 클래스 : {len(evaluable)}개 "
      f"(delivery·subscription·transfer 는 상가정보에 표본이 없어 제외)")
print(f"macro-F1    : {evaluable['f1'].mean():.4f}")
print(f"weighted-F1 : {(evaluable['f1']*evaluable['support']).sum()/evaluable['support'].sum():.4f}")

# ---- CODE 14 --------------------------------------------------
# ---- 혼동 행렬 (상위 오답 쌍) ----
conf = (res[~res["correct"] & (res["category"] != "unknown")]
        .groupby(["true", "category"]).size()
        .reset_index(name="건수").sort_values("건수", ascending=False).head(12))
conf["실제"] = conf["true"].map(korean)
conf["예측"] = conf["category"].map(korean)
print(conf[["실제", "예측", "건수"]].to_string(index=False))

# ======================================================================
# 이 정확도를 그대로 서비스 정확도로 읽으면 안 된다
# ======================================================================

# ---- CODE 15 --------------------------------------------------
row_cov = df["norm"].isin(merchant_dict).mean()
uniq_cov = uniq["norm"].isin(merchant_dict).mean()
print(f"고유 상호명 기준 사전 커버리지 : {uniq_cov:6.2%}   ← 위 평가가 보는 세계")
print(f"실제 거래(행) 기준 커버리지    : {row_cov:6.2%}   ← 서비스가 보는 세계")
print()
print(f"→ 같은 사전인데 거래 기준으로 보면 커버리지가 {row_cov/uniq_cov:.1f}배로 커진다.")
print("  실제 카드내역은 체인점 비중이 상가정보보다 훨씬 높으므로")
print("  L3(정확도 95%) 비중은 이보다 더 커질 것으로 예상되지만,")
print("  ⚠️ 이건 아직 추정이다. 실제 카드내역 샘플로 검증해야 한다.")

# ---- CODE 16 --------------------------------------------------
REAL_WORLD_CASES = [
    # (결제 표기, 정답 카테고리)
    ("배달의민족", "delivery"), ("(주)우아한형제들", "delivery"),
    ("쿠팡이츠", "delivery"), ("요기요", "delivery"),
    ("NETFLIX.COM", "subscription"), ("유튜브프리미엄", "subscription"),
    ("스포티파이", "subscription"), ("(주)멜론", "subscription"),
    ("OPENAI *CHATGPT SUBSCR", "subscription"), ("NOTION LABS", "subscription"),
    ("쿠팡(주)", "shopping"), ("무신사", "shopping"), ("올리브영 홍대점", "shopping"),
    ("11번가", "shopping"), ("다이소 강남점", "shopping"),
    ("스타벅스커피 코리아", "food"), ("GS25 신촌점", "food"), ("CU 역삼점", "food"),
    ("(주)파리크라상 파리바게뜨", "food"), ("맥도날드 강남", "food"),
    ("마켓컬리", "food"), ("이마트24 서울대", "food"),
    ("카카오T 택시", "transport"), ("쏘카", "transport"), ("SK에너지 주유소", "transport"),
    ("코레일 승차권", "transport"), ("티머니 충전", "transport"),
    ("CGV 강남", "leisure"), ("야놀자", "leisure"), ("에어비앤비", "leisure"),
    ("STEAMGAMES.COM", "leisure"), ("메가박스 코엑스", "leisure"),
    ("SKT 통신요금", "living"), ("한국전력공사", "living"), ("삼성화재 보험료", "living"),
    ("행복한약국", "medical"), ("서울대치과의원", "medical"),
    ("한빛수학학원", "education"), ("YBM어학원", "education"),
    # 소비가 아닌 것 — 반드시 걸러야 한다
    ("카드대금 결제", "transfer"), ("계좌이체", "transfer"),
    ("ATM 현금출금", "transfer"), ("리볼빙 약정", "transfer"),
    # 판단 불가 — 억지로 찍으면 안 된다
    ("토스페이먼츠(주)", "unknown"), ("NICEPAY", "unknown"), ("(주)KCP", "unknown"),
]

rw = pd.DataFrame(REAL_WORLD_CASES, columns=["표기", "정답"])
rw_pred = [clf.predict(x) for x in rw["표기"]]
rw["예측"] = [p["category"] for p in rw_pred]
rw["단계"] = [p["layer"] for p in rw_pred]
rw["근거"] = [p["evidence"] for p in rw_pred]
rw["정답여부"] = rw["예측"] == rw["정답"]

print(f"실전 표기 정확도: {rw['정답여부'].mean():.3f}  ({rw['정답여부'].sum()}/{len(rw)})")
print()
print(rw[~rw["정답여부"]].to_string(index=False) if (~rw["정답여부"]).any() else "전부 정답")

# ---- CODE 17 --------------------------------------------------
rw.groupby("단계").agg(건수=("정답여부", "size"), 정확도=("정답여부", "mean")).round(3)

# ======================================================================
# 개발 중 잡은 버그 — 부분 문자열 매칭의 함정
# ======================================================================

# ---- CODE 18 --------------------------------------------------
# 오탐 재발 방지 테스트 — 위 4건이 정상 분류되는지 확인
regression = ["성주식당", "한국세탁소", "현대출력센타", "커피빈여의도교보증권점",
              "카드대금 결제", "계좌이체", "ATM출금"]
pd.DataFrame([{"표기": t, "카테고리": clf.predict(t)["category"],
               "단계": clf.predict(t)["layer"]} for t in regression])

# ---- CODE 19 --------------------------------------------------
sweep = []
for th in [0.0, 0.2, 0.3, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]:
    c2 = MerchantClassifier(merchant_dict=merchant_dict, model=model, ml_threshold=th)
    sample = test_df.sample(min(30_000, len(test_df)), random_state=1)
    pr = pd.DataFrame(c2.predict_many(sample["상호명"].tolist()))
    pr["true"] = sample["category"].values
    unk = (pr["category"] == "unknown").mean()
    ok = pr[pr["category"] != "unknown"]
    sweep.append({"임계값": th, "미분류율": round(unk, 4),
                  "분류건 정확도": round((ok["category"] == ok["true"]).mean(), 4),
                  "전체 정확도": round((pr["category"] == pr["true"]).mean(), 4)})
sweep_df = pd.DataFrame(sweep)
print(sweep_df.to_string(index=False))

# ---- CODE 20 --------------------------------------------------
clf.save(ART)

# 업종코드 → 카테고리 매핑표 (팀 공용 문서 겸 산출물)
cmap = (df.drop_duplicates("상권업종소분류코드")[["상권업종소분류코드", "상권업종소분류명", "category"]]
        .rename(columns={"상권업종소분류코드": "소분류코드", "상권업종소분류명": "소분류명"}))
cmap["중분류코드"] = cmap["소분류코드"].str[:4]
cmap["카테고리한글"] = cmap["category"].map(korean)
cmap["예외처리"] = cmap["소분류코드"].isin(SUB_OVERRIDE).map({True: "O", False: ""})
cmap = cmap.sort_values("소분류코드")[["소분류코드", "소분류명", "중분류코드",
                                    "category", "카테고리한글", "예외처리"]]
cmap.to_csv(ART / "category_map.csv", index=False, encoding="utf-8-sig")

# 평가 리포트
report = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M"),
    "source_rows": int(len(df)),
    "unique_merchants": int(df["norm"].nunique()),
    "merchant_dict_size": len(merchant_dict),
    "brand_dict_size": sum(brand_stats().values()),
    "test_accuracy_all": round(float(res["correct"].mean()), 4),
    "test_accuracy_classified": round(float(known["correct"].mean()), 4),
    "unknown_rate": round(float((res["category"] == "unknown").mean()), 4),
    "macro_f1_evaluable": round(float(evaluable["f1"].mean()), 4),
    "real_world_accuracy": round(float(rw["정답여부"].mean()), 4),
    "layer_coverage": layer.set_index("layer")["커버리지(%)"].to_dict(),
}
json.dump(report, open(ART / "eval_report.json", "w"), ensure_ascii=False, indent=2)

for p in sorted(ART.iterdir()):
    print(f"{p.name:24s} {p.stat().st_size/1024:9.1f} KB")
print()
print(json.dumps(report, ensure_ascii=False, indent=2))

# 표본이 너무 작으면 배포용으로 쓰면 안 된다는 걸 눈에 띄게 알린다.
if report["source_rows"] < 1_000_000:
    print("\n⚠️  학습 표본이 {:,}건입니다. 전체 원본(약 276만건)이 아니므로".format(report["source_rows"]))
    print("    이 artifacts 를 서비스에 그대로 쓰면 안 됩니다. 커밋도 하지 마세요.")

# ---- CODE 21 --------------------------------------------------
# 실제 CSV 처리 시뮬레이션
sample_tx = pd.DataFrame({
    "date": ["2026-08-01", "2026-08-02", "2026-08-02", "2026-08-03",
             "2026-08-04", "2026-08-05", "2026-08-05", "2026-08-06"],
    "가맹점명": ["배달의민족", "스타벅스 강남점", "NETFLIX.COM", "김철수",
                "GS25 역삼점", "무신사", "토스페이먼츠(주)", "카카오T 택시"],
    "거래유형": ["승인", "승인", "승인", "이체", "승인", "승인", "승인", "승인"],
    "amount": [-23000, -5600, -13500, -450000, -8200, -89000, -34000, -12400],
})
# 거래유형 컬럼을 함께 넘긴다 — '김철수'는 이름만으로는 절대 알 수 없다
out = [clf.predict(n, t) for n, t in zip(sample_tx["가맹점명"], sample_tx["거래유형"])]
sample_tx["category"] = [korean(o["category"]) if o["category"] in CATEGORIES
                         else o["category"] for o in out]
sample_tx["layer"] = [o["layer"] for o in out]
print(sample_tx.to_string(index=False))

spend = [o for o in out if o["category"] not in ("transfer", "unknown")]
tot = sum(-a for a, o in zip(sample_tx["amount"], out)
          if o["category"] not in ("transfer", "unknown"))
print(f"\n실제 소비 합계 : {tot:,}원  (이체·미분류 제외)")
print(f"단순 합산했다면: {-sample_tx['amount'].sum():,}원  ← 이체 45만원이 섞여 4배 부풀어난다")
