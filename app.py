# 4.social_marcom_ideamaker.py
# -----------------------------------------------------------------------------
# Streamlit — "💡 Social Marcom Ideamaker"
# -----------------------------------------------------------------------------

import os
import io
import csv
import json
import random
from datetime import date, datetime, timedelta, time
from typing import List, Dict, Any, Tuple, Optional

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===============================
# 공통 유틸
# ===============================
def _json_default(o):
    if isinstance(o, (date, datetime, time)):
        return o.isoformat()
    if isinstance(o, set):
        return list(o)
    return str(o)

def _brace_escape(s: str) -> str:
    # f-string 안에 JSON 스키마를 그대로 넣을 때 중괄호 이스케이프
    return s.replace("{", "{{").replace("}", "}}")

def _esc(s: Any) -> str:
    s = str(s or "")
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# ===============================
# API 키
# ===============================
def load_api_key():
    key = None
    if hasattr(st, "secrets"):
        key = st.secrets.get("GEMINI_API_KEY", None)
    if not key:
        key = os.environ.get("GEMINI_API_KEY")
    return key

API_KEY = load_api_key()
if not API_KEY:
    st.error("❌ GEMINI_API_KEY가 없습니다. 환경변수 또는 .streamlit/secrets.toml/.env에 설정하세요.")
    st.stop()

# ===============================
# Gemini 클라이언트
# ===============================
from google import genai
from google.genai import types

@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    return genai.Client(api_key=api_key)

client = get_client(API_KEY)

# ===============================
# 상수/데이터
# ===============================
DEFAULT_COUNTRY = "대한민국"
CHANNELS = ["Instagram", "Facebook", "X(Twitter)"]   # 축소
GOALS = [
    "Social Buzz Making(재미/기믹)",
    "Engagement 생성(CTA)",
    "브랜드 인지도/선호도 상승",
    "제품 인지도/구매의향 상승",
    "제품 프로모션"
]
EVENT_CATEGORIES = [
    "Commercial", "Cultural", "PublicHoliday", "WeatherEnv",
    "School", "Religion", "MediaEnt", "Sports", "Gimmick", "WorldDays"
]
CAT_COLORS = {
    "Commercial":   "#FED7AA",
    "Cultural":     "#FBCFE8",
    "PublicHoliday":"#A7F3D0",
    "WeatherEnv":   "#BAE6FD",
    "School":       "#E9D5FF",
    "Religion":     "#FEF3C7",
    "MediaEnt":     "#C7D2FE",
    "Sports":       "#FDE68A",
    "Gimmick":      "#FFE4E6",
    "WorldDays":    "#E2E8F0",
}
WORLD_DAYS_DB: Dict[int, List[Tuple[int, str]]] = {
    1:  [(4, "세계 점자Day"), (11, "국제 감사의 날"), (24, "국제 교육의 날"), (28, "데이터 프라이버시의 날")],
    2:  [(2, "세계 습지의 날"), (9, "세계 피자Day(기믹)"), (13, "세계 라디오의 날"), (14, "밸런타인Day"), (20, "세계 사회정의의 날")],
    3:  [(3, "세계 야생동물의 날"), (8, "국제 여성의 날"), (14, "파이Day"), (20, "세계 행복의 날"),
         (21, "세계 산림의 날"), (22, "세계 물의 날"), (23, "세계 기상의 날")],
    4:  [(7, "세계 보건의 날"), (22, "지구의 날"), (23, "세계 책의 날"), (26, "세계 지식재산권의 날"), (29, "세계 춤의 날")],
    5:  [(3, "세계 언론자유의 날"), (4, "스타워즈Day(기믹)"), (8, "세계 적십자·적신월의 날"),
         (17, "세계 전기통신의 날"), (20, "세계 벌의 날"), (22, "국제 생물다양성의 날"), (25, "타월Day(기믹)")],
    6:  [(3, "세계 자전거의 날"), (5, "세계 환경의 날"), (8, "세계 해양의 날"), (14, "세계 헌혈자의 날"),
         (21, "세계 요가의 날"), (21, "세계 음악의 날"), (27, "세계 중소기업의 날")],
    7:  [(7, "세계 초콜릿Day(기믹)"), (11, "세계 인구의 날"), (17, "세계 이모지의 날"), (29, "국제 호랑이의 날")],
    8:  [(8, "세계 고양이의 날"), (12, "국제 청년의 날"), (19, "세계 인도주의의 날"), (26, "국제 개의 날")],
    9:  [(5, "국제 자선의 날"), (8, "국제 문해의 날"), (16, "세계 오존층 보호의 날"),
         (21, "세계 평화의 날"), (27, "세계 관광의 날"), (29, "세계 심장의 날")],
    10: [(1, "국제 커피의 날"), (4, "세계 동물의 날"), (10, "세계 정신건강의 날"),
         (16, "세계 식량의 날"), (20, "세계 나무늘보의 날"), (31, "할로윈(기믹)")],
    11: [(13, "세계 친절의 날"), (14, "세계 당뇨병의 날"), (20, "세계 아동의 날"), (21, "세계 텔레비전의 날")],
    12: [(3, "세계 장애인의 날"), (5, "세계 자원봉사의 날"), (11, "세계 산의 날"), (14, "원숭이Day(기믹)")]
}

RESEARCH_EVENT_SCHEMA = """
{
  "category": "string",
  "name": "string",
  "date": "YYYY-MM-DD or null",
  "note": "why relevant (1-2 lines; 명절은 '연휴 시작~끝' 포함 권장)",
  "confidence": 0.0,
  "specific_confidence": 0.0,
  "sources": ["간단 키워드 또는 URL"]
}
""".strip()

IDEA_CARD_SCHEMA = """
{
  "id": "string",
  "title": "string",
  "image_concept": "string (개념적·구체; 텍스트만)",
  "copy_draft": "string (구형 호환; 없으면 무시)",
  "copy_draft_ko": "string (한국어 캡션)",
  "copy_draft_local": "string (현지어 캡션; 나라가 한국이면 생략 가능)",
  "recommended_channels": ["Instagram","Facebook","X(Twitter)"],
  "fit_goals": ["..."],
  "targeted_events": [{"category":"string","name":"string","date":"YYYY-MM-DD or null","note":"string"}],
  "rationale": "string (이벤트 적합 이유; 구체요소 포함)",
  "expected_impact": "string",
  "specific_entities": ["구체명1","구체명2"],
  "specificity_confidence": 0.0,
  "confidence": 0.0
}
""".strip()

# 언어/타임존
LANG_BY_COUNTRY = {
    "United States": ("영어", "English"),
    "USA": ("영어", "English"),
    "US": ("영어", "English"),
    "United Kingdom": ("영어", "English"),
    "UK": ("영어", "English"),
    "Canada": ("영어", "English"),
    "Australia": ("영어", "English"),
    "New Zealand": ("영어", "English"),
    "France": ("프랑스어", "French"),
    "Belgium": ("프랑스어", "French"),
    "Switzerland": ("프랑스어", "French"),
    "Germany": ("독일어", "German"),
    "Austria": ("독일어", "German"),
    "Spain": ("스페인어", "Spanish"),
    "Mexico": ("스페인어", "Spanish"),
    "Argentina": ("스페인어", "Spanish"),
    "Japan": ("일본어", "Japanese"),
    "China": ("중국어(간체)", "Chinese Simplified"),
    "Taiwan": ("중국어(번체)", "Chinese Traditional"),
    "Hong Kong": ("중국어(번체)", "Chinese Traditional"),
    "Korea": ("한국어", "Korean"),
    "South Korea": ("한국어", "Korean"),
    "대한민국": ("한국어", "Korean"),
    "Italy": ("이탈리아어", "Italian"),
    "Brazil": ("포르투갈어(브라질)", "Portuguese (Brazil)")
}
def detect_local_language(country: str) -> Tuple[str, str]:
    c = (country or "").strip()
    if c in LANG_BY_COUNTRY: return LANG_BY_COUNTRY[c]
    if c in {"KR","Korea","South Korea","Republic of Korea","대한민국"}: return ("한국어","Korean")
    if c in {"US","USA"}: return ("영어","English")
    return ("현지어","Local language")

from zoneinfo import ZoneInfo
TZ_BY_COUNTRY = {
    "대한민국": "Asia/Seoul",
    "Korea": "Asia/Seoul",
    "South Korea": "Asia/Seoul",
    "United States": "America/New_York",
    "USA": "America/New_York",
    "US": "America/New_York",
    "United Kingdom": "Europe/London",
    "UK": "Europe/London",
    "France": "Europe/Paris",
    "Germany": "Europe/Berlin",
    "Spain": "Europe/Madrid",
    "Japan": "Asia/Tokyo",
    "China": "Asia/Shanghai",
    "Taiwan": "Asia/Taipei",
    "Hong Kong": "Asia/Hong_Kong",
    "Italy": "Europe/Rome",
    "Brazil": "America/Sao_Paulo",
    "Australia": "Australia/Sydney",
    "Canada": "America/Toronto",
    "Mexico": "America/Mexico_City",
}

def kst_equivalent(hhmm: time, local_tz_str: str, on_date: date) -> str:
    try:
        local = ZoneInfo(local_tz_str)
    except Exception:
        local = ZoneInfo("UTC")
    dt_local = datetime.combine(on_date, hhmm).replace(tzinfo=local)
    dt_kst = dt_local.astimezone(ZoneInfo("Asia/Seoul"))
    return dt_kst.strftime("%H:%M")

# ===============================
# LLM 유틸
# ===============================
def _parse_json_from_text(text: str):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    for open_b, close_b in (("[", "]"), ("{", "}")):
        l = text.find(open_b); r = text.rfind(close_b)
        if l >= 0 and r >= 0 and r > l:
            try:
                return json.loads(text[l:r+1])
            except Exception:
                pass
    return None

def call_gemini_json(prompt: str, model: str="gemini-2.5-flash", temperature: float=0.5, thinking_off: bool=True):
    try:
        cfg = types.GenerateContentConfig(
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_budget=0) if thinking_off else None
        )
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
        text = getattr(resp, "text", "") or (resp.candidates[0].content.parts[0].text if getattr(resp, "candidates", None) else "")
        data = _parse_json_from_text(text)
        if data is None:
            return None, "LLM JSON 파싱 실패"
        return data, None
    except Exception as e:
        return None, f"LLM 호출 오류: {e}"

# ===============================
# 리서치/생성
# ===============================
def normalize_event_context(raw: Any) -> Dict[str, List[Dict[str, Any]]]:
    if raw is None: return {}
    if isinstance(raw, dict) and len(raw) == 1 and next(iter(raw.keys())) in {"data","result","payload","LocalEvents","events"}:
        raw = raw[next(iter(raw.keys()))]
    if isinstance(raw, dict):
        out: Dict[str, List[Dict[str, Any]]] = {}
        for k, arr in raw.items():
            if k in EVENT_CATEGORIES and isinstance(arr, list):
                out[k] = [x for x in arr if isinstance(x, dict)]
        if out: return out
        if isinstance(raw.get("events"), list): raw = raw["events"]
    if isinstance(raw, list):
        out: Dict[str, List[Dict[str, Any]]] = {}
        for it in raw:
            if isinstance(it, dict):
                cat = it.get("category","")
                if cat in EVENT_CATEGORIES:
                    out.setdefault(cat, []).append(it)
        return out
    return {}

def _flatten_events(any_ctx: Any) -> List[Dict[str, Any]]:
    flat: List[Dict[str, Any]] = []
    if isinstance(any_ctx, dict):
        if isinstance(any_ctx.get("events"), list):
            for e in any_ctx["events"]:
                if isinstance(e, dict):
                    if "category" not in e: e["category"] = "WorldDays"
                    flat.append(e)
        else:
            for cat, arr in any_ctx.items():
                if isinstance(arr, list):
                    for e in arr:
                        if isinstance(e, dict):
                            if "category" not in e: e = {"category": cat, **e}
                            flat.append(e)
    elif isinstance(any_ctx, list):
        for e in any_ctx:
            if isinstance(e, dict):
                if "category" not in e: e["category"] = "WorldDays"
                flat.append(e)
    return flat

def research_local_events_with_llm(target_day: date, country: str, window_days: int,
                                   model: str, temperature: float, thinking_off: bool,
                                   max_per_category: int=3) -> Tuple[Dict[str, List[Dict[str, Any]]], Optional[str]]:
    start_date = (target_day - timedelta(days=window_days)).isoformat()
    end_date   = (target_day + timedelta(days=window_days)).isoformat()
    prompt = f"""
당신은 {country} 시장 소셜마케팅 리서처다.
{country}에서 {start_date}~{end_date} (±{window_days}일)에 소셜 포스팅에 유용한 '로컬 이벤트'를 제시하라.
카테고리 {EVENT_CATEGORIES} 중 **신뢰도 낮은 카테고리는 생략** 가능.

필수 체크:
- 국가 최대 명절/공휴일(대체공휴일 포함)
- WorldDays(예: 8/8 세계 고양이의 날, 10/20 국제 나무늘보의 날, 6/5 환경의 날, 4/23 책의 날 등)
- Sports: 인기 종목 프로리그 + 국가대표/국제대회 + e스포츠 메이저

구체성 규칙:
- 리그/대표팀은 매치업/라운드/장소
- 명절/공휴일은 '연휴 시작~끝'
- 콘서트/방문은 아티스트/장소

반환(JSON; dict of lists 또는 events 배열). 각 이벤트 스키마:
{_brace_escape(RESEARCH_EVENT_SCHEMA)}
"""
    raw, err = call_gemini_json(prompt, model=model, temperature=temperature, thinking_off=thinking_off)
    if err: return {}, err
    data = normalize_event_context(raw)
    if not isinstance(data, dict) or not data:
        return {}, "리서치 결과 형식 오류"

    out: Dict[str, List[Dict[str, Any]]] = {}
    for cat, items in data.items():
        if cat not in EVENT_CATEGORIES or not isinstance(items, list): continue
        pruned = []
        for it in items:
            d = it.get("date")
            try:
                if d:
                    dd = datetime.fromisoformat(d).date()
                    if abs((dd - target_day).days) <= window_days:
                        pruned.append(it)
                else:
                    if len(pruned) < 1:
                        pruned.append(it)
            except Exception:
                pass
            if len(pruned) >= max_per_category: break
        if pruned: out[cat] = pruned

    if not out: return {}, "기간 내 적합한 이벤트를 찾지 못했습니다."
    return out, None

def _avg(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return sum(xs)/len(xs) if xs else 0.0

def _match_event_pair(name: str, cat: str, ctx: Dict[str, List[Dict[str, Any]]]) -> Tuple[float, float]:
    for ev in ctx.get(cat, []):
        if ev.get("name","").lower() == (name or "").lower():
            return float(ev.get("confidence",0.0) or 0.0), float(ev.get("specific_confidence",0.0) or 0.0)
    return 0.0, 0.0

def _score_card(card: Dict[str, Any], ctx: Dict[str, Any]) -> float:
    evs = card.get("targeted_events", []) or []
    pairs = [_match_event_pair(e.get("name",""), e.get("category",""), ctx) for e in evs]
    ev_conf = _avg([p[0] for p in pairs])
    ev_spec = _avg([p[1] for p in pairs])
    card_spec = float(card.get("specificity_confidence", 0.0) or 0.0)
    ic_len = len(card.get("image_concept",""))
    density_bonus = min(0.2, ic_len / 600.0)
    return round(max(0.0, min(1.0, 0.55*ev_conf + 0.3*max(ev_spec, card_spec) + density_bonus)), 4)

def generate_idea_cards_with_llm(target_day: date, channels: List[str], goals: List[str], brand: str,
                                 country: str, event_context: Dict[str, Any], n_cards: int, model: str,
                                 temperature: float, thinking_off: bool) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if not event_context:
        return [], "이벤트 컨텍스트가 비어 있습니다."
    n_req = min(12, max(n_cards, n_cards + 3))
    local_lang_kor, local_lang_eng = detect_local_language(country)
    bilingual_needed = (country not in {"대한민국","Korea","South Korea","Republic of Korea"} and local_lang_eng != "Korean")
    bilingual_note = (
        f"- 캡션은 **이중언어**로 작성: `copy_draft_ko`(한국어) + `copy_draft_local`({local_lang_kor}).\n"
        if bilingual_needed else
        "- 한국 대상이면 `copy_draft_ko`만 작성(또는 copy_draft 호환).\n"
    )

    prompt = f"""
당신은 {country}의 소셜 마케팅 전문가다.
아래 **브랜드/제품(또는 카테고리)**의 USP/페인포인트/대표 사용 시나리오를 간단 요약한 뒤,
로컬 이벤트와 전략적으로 매칭하여 *아이디어 카드*를 정확히 {n_req}개 생성하라.
- 이벤트 인사이트 ↔ 제품 USP를 설득력 있게 연결.
- 이미지는 텍스트 컨셉만(구도/피사체/소품/라이팅/색감까지).
- 캡션은 실제 소셜 톤(멘션/해시태그 허용).
{bilingual_note}
입력:
- 대상일: {target_day.isoformat()}
- 국가: {country}
- 브랜드/제품/카테고리: {brand or 'N/A'}
- 채널 후보: {", ".join(channels) if channels else "N/A"}
- 목표: {", ".join(goals) if goals else "N/A"}

로컬 이벤트 컨텍스트(±7일):
{json.dumps(event_context, ensure_ascii=False, indent=2)}

반환(JSON 배열, 정확히 {n_req}개):
{_brace_escape(IDEA_CARD_SCHEMA)}
"""
    ideas, err = call_gemini_json(prompt, model=model, temperature=temperature, thinking_off=thinking_off)
    if err: return [], err
    if not isinstance(ideas, list) or not ideas:
        return [], "아이디어 생성 결과가 비어 있거나 형식이 아닙니다."

    for i, it in enumerate(ideas, 1):
        it.setdefault("id", f"card_{i}")
        it["specificity_confidence"] = float(it.get("specificity_confidence", 0.0) or 0.0)
        it["confidence"] = _score_card(it, event_context)
        if "copy_draft_ko" not in it and "copy_draft" in it:
            it["copy_draft_ko"] = it.get("copy_draft","")

    ideas_sorted = sorted(ideas, key=lambda x: x.get("confidence", 0.0), reverse=True)[:n_cards]
    return ideas_sorted, None

def refine_card_with_llm(base_card: Dict[str, Any], instruction: str, country: str,
                         model: str, temperature: float) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    prompt = f"""
당신은 {country}의 소셜 카피/아이디어 디렉터다.
다음 '기존 카드'를 사용자의 지시에 맞춰 **작게 수정**하되, 이벤트 타깃팅의 정합성을 유지하고
스키마를 그대로 따르라(필드 누락 금지). JSON 오브젝트 1개만 반환.

[지시]
{instruction}

[기존 카드(JSON)]
{json.dumps(base_card, ensure_ascii=False, indent=2)}

[반환 스키마]
{_brace_escape(IDEA_CARD_SCHEMA)}
"""
    data, err = call_gemini_json(prompt, model=model, temperature=temperature, thinking_off=True)
    if err:
        return None, err
    if not isinstance(data, dict):
        return None, "수정 결과 형식 오류"
    return data, None

# ===============================
# 연간 이벤트 생성/파일화
# ===============================
YEAR_EVENTS_PROMPT_TEMPLATE = """
당신은 {country} 시장의 **연간 마케팅 캘린더** 작성자다.
연도: {year}, 국가: {country}.
카테고리: {categories}
월별 **최소 10개 이상** 이벤트를 JSON 배열로 생성하라(부족 시 WorldDays/스포츠/문화로 보강).
반환 스키마:
{schema}
""".strip()

def generate_year_events_with_llm(year: int, country: str, model: str, temperature: float, thinking_off: bool) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    prompt = YEAR_EVENTS_PROMPT_TEMPLATE.format(
        year=year, country=country, categories=", ".join(EVENT_CATEGORIES),
        schema=_brace_escape(RESEARCH_EVENT_SCHEMA)
    )
    raw, err = call_gemini_json(prompt, model=model, temperature=temperature, thinking_off=thinking_off)
    if err: return [], err
    flat = _flatten_events(raw)
    if not flat: return [], "연간 이벤트 결과가 비어 있습니다."
    flat = _ensure_month_minimum(flat, year, min_per_month=10)

    def _key(e):
        d = e.get("date")
        try: return (0, datetime.fromisoformat(d).date()) if d else (1, date(year, 12, 31))
        except Exception: return (1, date(year, 12, 31))
    flat.sort(key=_key)
    return flat, None

def _ensure_month_minimum(events: List[Dict[str, Any]], year: int, min_per_month: int=10) -> List[Dict[str, Any]]:
    by_month: Dict[int, List[Dict[str, Any]]] = {m: [] for m in range(1, 13)}
    seen = set()
    for e in events:
        d = e.get("date"); m = 0
        if d:
            try: m = datetime.fromisoformat(d).month
            except Exception: m = 0
        if 1 <= m <= 12: by_month[m].append(e)
        seen.add((e.get("name",""), e.get("date","")))
    padded: List[Dict[str, Any]] = events[:]
    for m in range(1, 13):
        cur = by_month[m]
        if len(cur) >= min_per_month: continue
        candidates = WORLD_DAYS_DB.get(m, [])
        for day, nm in candidates:
            if len(cur) >= min_per_month: break
            dstr = f"{year}-{m:02d}-{day:02d}"
            key = (nm, dstr)
            if key in seen: continue
            ev = {"category":"WorldDays","name":nm,"date":dstr,"note":"고정 국제 기념일(월별 보강)","confidence":0.9,"specific_confidence":0.95,"sources":[f"WorldDays {nm}"]}
            padded.append(ev); by_month[m].append(ev); seen.add(key)
    return padded

def build_year_events_file(year_events: List[Dict[str, Any]], year: int) -> Tuple[bytes, str, str]:
    cols = ["date","name","category","note","confidence","specific_confidence","sources"]
    rows = []
    for e in year_events:
        rows.append([e.get("date",""), e.get("name",""), e.get("category",""), e.get("note",""),
                     e.get("confidence",""), e.get("specific_confidence",""),
                     ", ".join(e.get("sources", [])) if isinstance(e.get("sources", []), list) else (e.get("sources","") or "")])
    try:
        import pandas as pd
        df = pd.DataFrame(rows, columns=cols)
        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name=str(year))
        return bio.getvalue(), f"marketing_events_{year}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        bio = io.StringIO()
        cw = csv.writer(bio)
        cw.writerow(cols)
        cw.writerows(rows)
        return bio.getvalue().encode("utf-8-sig"), f"marketing_events_{year}.csv", "text/csv"

# ===============================
# 스타일 + 모달
# ===============================
PAGE_CSS = """
<style>
:root { --spost-h: 520px; }

[data-testid="stAppViewContainer"] .main .block-container { 
  max-width: 1530px !important; 
  padding-top: 1rem; 
  margin: 0 auto;
}
button[data-testid="baseButton-primary"]{background:#DC2626 !important; border-color:#DC2626 !important; color:#fff !important;}
button[data-testid="baseButton-primary"]:hover{background:#B91C1C !important; border-color:#B91C1C !important;}
button[data-testid="baseButton-secondary"]{background:#FEE2E2 !important; color:#7F1D1D !important; border-color:#FCA5A5 !important;}
button[data-testid="baseButton-secondary"]:hover{background:#FECACA !important; border-color:#F87171 !important;}

.pills {display:flex; flex-wrap:wrap; gap:6px; margin: 6px 0 8px 0;}
.pill {display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; color:#111827; border:1px solid rgba(17,24,39,.08);}

.spost {border:1px solid #E5E7EB; border-radius:14px; background:#fff; overflow:hidden; margin-bottom:10px;
        height: var(--spost-h); display:flex; flex-direction:column;}
.spost .sp-header {display:flex; align-items:center; gap:10px; padding:12px 14px; border-bottom:1px solid #F3F4F6;}
.spost .avatar {width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#fde68a,#fca5a5); display:flex; align-items:center; justify-content:center; font-weight:700; color:#fff;}
.spost .meta-line {font-size:12px; color:#6B7280;}
.spost .brand {font-weight:700; font-size:14px;}
.spost .platform {font-size:12px; color:#6B7280; margin-left:auto;}
.spost .sp-body {padding:12px 14px; font-size:14px; line-height:1.55; display:flex; flex-direction:column; flex:1; min-height:0; position:relative;}

.spost .concept-outer{ background:#F3F4F6; border:1px solid #E5E7EB; border-radius:12px; padding:10px; margin:10px 0; flex:0 0 auto; position:relative;}
.spost .concept-inner{ background:#FFFFFF; border:1.5px dashed #CBD5E1; border-radius:10px; padding:12px; }
.spost .concept-inner pre{ white-space:pre-wrap; word-break:break-word; margin:0; font-size:13.5px; line-height:1.5; font-family: inherit; color:#6B7280; font-style: italic; max-height:120px; overflow:auto; }

/* 이미지 생성하기 — 박스 '내' 우하단 텍스트 링크 */
.concept-link { position:absolute; right:12px; bottom:8px; font-size:12px; color:#2563EB; text-decoration:none; }
.concept-link:hover { text-decoration:underline; }

.capline{ margin:8px 0 0 0; display:-webkit-box; -webkit-line-clamp:4; -webkit-box-orient:vertical; overflow:hidden; }
.small-btn-row{display:flex; gap:8px; margin-top:auto;}
.badge{display:inline-block; padding:2px 8px; border-radius:999px; background:#F3F4F6; border:1px solid #E5E7EB; font-size:12px; color:#374151; margin-right:6px;}

/* 모달 느낌(컨테이너로 대체) */
.modal-wrap {background:rgba(0,0,0,.45); padding:10px; border-radius:12px;}
</style>
"""

st.set_page_config(page_title="Social Marcom Ideamaker", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# 쿼리파라미터로 '이미지 생성하기' 클릭 감지 → 토스트 표시 후 파라미터 제거
try:
    qp = st.query_params
    if "img" in qp:
        st.toast("Visual Sourcing Agent 연계가 필요합니다.", icon="❗")
        try:
            del st.query_params["img"]
        except Exception:
            st.query_params.clear()
except Exception:
    pass

# ===============================
# UI — 헤더
# ===============================
st.title("💡 Social Marcom Ideamaker")

with st.form("input_form"):
    col1, col2, col3, col4 = st.columns([1.2, 1, 1.1, 1.8])
    with col1:
        brand = st.text_input("브랜드 / 제품명 또는 카테고리", value="")
        target_day = st.date_input("대상 날짜 (해당 포스트를 게시하고자 하는 날짜)", value=date.today() + timedelta(days=3))
    with col2:
        country = st.text_input("대상 국가", value=DEFAULT_COUNTRY)  # 예시 문구 제거
        channels = st.multiselect("대상 채널", options=CHANNELS, default=["Instagram", "X(Twitter)"])
    with col3:
        # [Social Marketing 목표 설정] 삭제됨
        n_cards = st.slider("생성 카드 수", min_value=1, max_value=10, value=6, step=1)
    with col4:
        # [모델] 삭제됨 → 내부 디폴트 사용
        # [창의성] 삭제됨 → 내부 디폴트 사용
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.markdown("&nbsp;", unsafe_allow_html=True)
    submitted = st.form_submit_button("LLM 리서치 & 아이디어 생성")

# 세션 상태
ss = st.session_state
ss.setdefault("event_context", {})
ss.setdefault("idea_cards", [])
ss.setdefault("inputs_snapshot", {})
ss.setdefault("last_error", None)
ss.setdefault("year_events_cache", {})
ss.setdefault("modal_type", None)          # "preview" | "publish" | "edit" | None
ss.setdefault("modal_card_id", None)

# ===============================
# 실행 — 리서치 & 카드 생성
# ===============================
if submitted:
    ss.last_error = None
    if not brand.strip():
        st.error("브랜드와 제품명 또는 카테고리를 입력해주세요")
        st.stop()

    # 삭제된 목표 옵션 대신, 모든 목표를 포괄적으로 사용
    goals = GOALS[:]  # 전체 목표 사용

    # 삭제된 모델/창의성 옵션 대신 고정값 사용
    model = "gemini-2.5-flash"
    creativity = 0.60

    with st.status("🤖 AI가 해당 국가의 주요 Event를 리서치 및 정리하고 있어요.", state="running") as s:
        events, err1 = research_local_events_with_llm(
            target_day=target_day, country=country, window_days=7,
            model=model, temperature=0.35, thinking_off=True, max_per_category=3
        )
        if err1:
            ss.event_context = {}
            ss.last_error = f"리서치 실패: {err1}"
            s.update(label="❌ 리서치 실패", state="error")
            st.error(ss.last_error); st.stop()
        ss.event_context = events
        s.update(label="✅ 리서치 완료, 아이디어 카드 생성 중. 조금만 더 기다려 주세요.", state="running")

        cards, err2 = generate_idea_cards_with_llm(
            target_day=target_day, channels=channels, goals=goals, brand=brand, country=country,
            event_context=ss.event_context, n_cards=n_cards,
            model=model, temperature=creativity, thinking_off=True
        )
        if err2:
            flat = []
            for cat, arr in ss.event_context.items():
                for e in arr:
                    flat.append({"category": cat, **e})
            if not flat:
                ss.last_error = f"아이디어 생성 실패: {err2}"
                s.update(label="❌ 아이디어 생성 실패", state="error")
                st.error(ss.last_error); st.stop()
            rng = random.Random(target_day.toordinal() + len(flat))
            sampled = rng.sample(flat, k=min(n_cards, len(flat)))
            cards = [{
                "id": f"fb_{i}",
                "title": f"[{e['name']}] 타깃 아이디어",
                "image_concept": f"{e['name']} 현장과 {brand} 연관 소품/상황을 배치한 합성 컨셉.",
                "copy_draft_ko": f"{e['name']} 현장감을 살린 캡션. {brand}의 사용 순간을 포착하고 CTA 유도. #로컬이벤트",
                "copy_draft_local": "",
                "recommended_channels": channels[:3] or ["Instagram", "X(Twitter)"],
                "fit_goals": goals[:2] if goals else [],
                "targeted_events": [{"category": e["category"], "name": e["name"], "date": e.get("date"), "note": e.get("note","")}],
                "rationale": f"±7일 로컬 이벤트 '{e['name']}'와 {brand}의 USP 연결.",
                "expected_impact": "로컬 적합성으로 도달/ER 향상.",
                "specificity_confidence": float(e.get("specific_confidence", 0.3) or 0.3),
                "confidence": float(e.get("confidence", 0.5) or 0.5),
            } for i, e in enumerate(sampled, 1)]

        ss.idea_cards = cards
        ss.inputs_snapshot = {
            "brand": brand, "target_day": target_day.isoformat(), "channels": channels, "goals": goals,
            "model": model, "creativity": creativity, "country": country
        }
        s.update(label=f"✅ 아이디어 {len(cards)}개 생성 완료", state="complete")
        st.toast("아이디어 생성이 완료되었습니다.", icon="✅")

# ===============================
# 섹션: 주요 로컬 이벤트 (최소 5개 보장 + 저신뢰 경고)
# ===============================
st.markdown("<br>", unsafe_allow_html=True)

def _ensure_min_five(ctx: Dict[str, List[Dict[str, Any]]], tgt_day: date) -> Dict[str, List[Dict[str, Any]]]:
    total = sum(len(v) for v in ctx.values())
    if total >= 5:
        return ctx
    month = tgt_day.month
    add = []
    for day, nm in WORLD_DAYS_DB.get(month, []):
        dstr = date(tgt_day.year, month, day).isoformat()
        if abs((date.fromisoformat(dstr) - tgt_day).days) <= 7:
            add.append({"category":"WorldDays","name":nm,"date":dstr,"note":"월별 고정 국제 기념일","confidence":0.9,"specific_confidence":0.95})
        if total + len(add) >= 5:
            break
    if add:
        ctx = dict(ctx)
        ctx.setdefault("WorldDays", []).extend(add)
    return ctx

if ss.get("event_context"):
    st.subheader("주요 로컬 이벤트 정리")
    st.caption("대상 날짜 +-1주 내의 이벤트를 제시합니다.")
    def render_event_context_table(ctx: Dict[str, List[Dict[str, Any]]]):
        rows = []
        for cat, arr in ctx.items():
            color = CAT_COLORS.get(cat, "#E5E7EB")
            for e in arr:
                warn = ""
                conf = e.get("confidence", None)
                if isinstance(conf, (int, float)) and conf < 0.5:
                    warn = " (주의) 해당 이벤트는 연관성이 낮을 수 있습니다. 재확인을 해주세요."
                rows.append({
                    "cat": cat, "color": color,
                    "name": e.get("name",""),
                    "date": e.get("date",""),
                    "note": (e.get("note","") or "") + warn
                })
        html = ['<div class="table-wrap"><table>']
        html.append("<thead><tr><th>카테고리</th><th>이벤트</th><th>날짜</th><th>메모</th></tr></thead><tbody>")
        for r in rows:
            html.append(
                f"<tr>"
                f"<td><span class='pill' style='background:{r['color']}'>{_esc(r['cat'])}</span></td>"
                f"<td>{_esc(r['name'])}</td>"
                f"<td>{_esc(r['date'] or '—')}</td>"
                f"<td style='color:#6B7280'>{_esc(r['note'])}</td>"
                f"</tr>"
            )
        html.append("</tbody></table></div>")
        st.markdown("\n".join(html), unsafe_allow_html=True)
    tgt = date.fromisoformat(ss.get("inputs_snapshot", {}).get("target_day", date.today().isoformat()))
    ctx5 = _ensure_min_five(ss["event_context"], tgt)
    render_event_context_table(ctx5)

# ===============================
# 섹션: 아이디어 카드
# ===============================
st.markdown("<br>", unsafe_allow_html=True)

def _platform_emoji(name: str) -> str:
    return {"Instagram":"📸","Facebook":"🟦","X(Twitter)":"✖️"}.get(name,"📣")

def _format_time_for_header(d: date) -> str:
    return f"7:15 AM {d.strftime('%b %d, %Y')}"

if ss.get("idea_cards"):
    st.subheader("아이디어 카드")
    cards = ss["idea_cards"]; per_row = 3
    local_lang_kor, _ = detect_local_language(ss.get("inputs_snapshot", {}).get("country", DEFAULT_COUNTRY))

    def pills_html(evs):
        parts = []
        for e in (evs or []):
            color = CAT_COLORS.get(e.get("category", ""), "#E5E7EB")
            d = e.get("date")
            label = f"{e.get('name','')} ({d})".strip() if d else f"{e.get('name','')}".strip()
            parts.append(f"<span class='pill' style='background:{color}'>{_esc(label)}</span>")
        return "<div class='pills'>" + "".join(parts) + "</div>"

    for i in range(0, len(cards), per_row):
        row_cards = cards[i:i+per_row]
        cols = st.columns(per_row)
        for j, card in enumerate(row_cards):
            with cols[j]:
                platform = (card.get("recommended_channels") or ["Instagram"])[0]
                emoji = _platform_emoji(platform)
                evs = card.get("targeted_events", []) or []
                ko_caption = card.get("copy_draft_ko") or card.get("copy_draft") or ""
                local_caption = card.get("copy_draft_local","")

                cap_ko_html = f"<p class='capline'><b>KR</b> · {_esc(ko_caption)}</p>" if ko_caption else ""
                cap_local_html = f"<p class='capline'><b>{_esc(local_lang_kor)}</b> · {_esc(local_caption)}</p>" if local_caption else ""

                # 이미지 컨셉 박스 '내'에 텍스트 링크 삽입 (href=쿼리파라미터)
                img_link_html = f'<a class="concept-link" href="?img={_esc(card["id"])}">이미지 생성하기</a>'

                st.markdown(f"""
                <div class="spost">
                  <div class="sp-header">
                    <div class="avatar">{_esc((ss.get('inputs_snapshot',{}).get('brand') or 'B')[:1]).upper()}</div>
                    <div>
                      <div class="brand">{_esc(ss.get('inputs_snapshot',{}).get('brand') or 'Brand')}</div>
                      <div class="meta-line">{_esc(_format_time_for_header(date.fromisoformat(ss.get('inputs_snapshot',{}).get('target_day', date.today().isoformat()))))}</div>
                    </div>
                    <div class="platform">{_esc(platform)} {emoji}</div>
                  </div>
                  <div class="sp-body">
                    <div style="font-weight:600;margin-bottom:6px;">{_esc(card.get('title','아이디어'))}</div>
                    {pills_html(evs)}
                    <div class="concept-outer">
                      <div class="concept-inner">
                        <pre>[이미지 컨셉]
{_esc(card.get('image_concept',''))}</pre>
                      </div>
                      {img_link_html}
                    </div>
                    {cap_ko_html}{cap_local_html}
                    <div class="small-btn-row">
                      <span class="badge">신뢰도 {card.get('confidence',0):.2f}</span>
                      <span class="badge">구체성 {card.get('specificity_confidence',0):.2f}</span>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # 하단 액션: (미리보기 제거) 수정하기 / 발행하기
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("수정하기", key=f"edit_{card['id']}", type="secondary", use_container_width=True):
                        ss["modal_type"] = "edit"
                        ss["modal_card_id"] = card["id"]
                with b2:
                    if st.button("발행하기", key=f"pub_{card['id']}", type="primary", use_container_width=True):
                        ss["modal_type"] = "publish"
                        ss["modal_card_id"] = card["id"]

# ===============================
# 모달: 수정 / 발행
# ===============================
def render_edit_modal(card: Dict[str, Any]):
    st.markdown("<div class='modal-wrap'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**✍️ 아이디어 미세 조정**")
        instr = st.text_area("지시(예: CTA를 더 명확히 / 현지 해시태그 추가 / 톤 업)", key=f"instr_{card['id']}")
        # 한 줄에 '적용'과 '취소'를 붙여 배치
        col_apply, col_cancel = st.columns([1,1])
        with col_apply:
            if st.button("미세 조정 적용", type="primary", use_container_width=True):
                with st.status("✍️ 수정 반영 중…", state="running"):
                    new_card, err = refine_card_with_llm(
                        card, instr,
                        st.session_state.get("inputs_snapshot", {}).get("country", DEFAULT_COUNTRY),
                        st.session_state.get("inputs_snapshot", {}).get("model", "gemini-2.5-flash"),
                        st.session_state.get("inputs_snapshot", {}).get("creativity", 0.6)
                    )
                    if err or not new_card:
                        st.error(f"수정 실패: {err or '형식 오류'}")
                    else:
                        new_card["confidence"] = _score_card(new_card, st.session_state.get("event_context", {}))
                        for idx, c in enumerate(st.session_state.get("idea_cards", [])):
                            if c["id"] == card["id"]:
                                st.session_state["idea_cards"][idx] = new_card
                                break
                        st.success("수정 적용 완료")
                        st.session_state["modal_type"] = None
                        st.session_state["modal_card_id"] = None
                        st.rerun()
        with col_cancel:
            if st.button("취소", type="secondary", use_container_width=True):
                st.session_state["modal_type"] = None
                st.session_state["modal_card_id"] = None
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def render_publish_modal(card: Dict[str, Any]):
    st.markdown("<div class='modal-wrap'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("📤 소셜 포스트 발행 설정")
        P_PLATFORMS = ["Instagram", "Facebook", "X(Twitter)"]
        pc1, pc2, pc3 = st.columns([1.2, 1, 1])
        with pc1:
            platform = st.selectbox("플랫폼", P_PLATFORMS, index=0, key="pub_platform")
            use_local = st.checkbox("현지어 캡션 사용", value=bool(card.get("copy_draft_local")), key="pub_use_local")
        with pc2:
            sched_date = st.date_input("게시 날짜", value=date.fromisoformat(st.session_state.get("inputs_snapshot",{}).get("target_day", date.today().isoformat())), key="pub_date")
        with pc3:
            tz_default = TZ_BY_COUNTRY.get(st.session_state.get("inputs_snapshot",{}).get("country", DEFAULT_COUNTRY), "UTC")
            tz_options = sorted(set(list(TZ_BY_COUNTRY.values()) + ["UTC"]))
            tz_index = tz_options.index(tz_default) if tz_default in tz_options else 0
            local_tz = st.selectbox("현지 타임존", tz_options, index=tz_index, key="pub_tz")
            sched_time = st.time_input(
                f"게시 시간 (현지시간 → KST: {kst_equivalent(time(7,15), local_tz, sched_date)})",
                value=time(7,15), key="pub_time"
            )
            st.caption(f"현재 선택: 현지 {sched_time.strftime('%H:%M')} → KST {kst_equivalent(sched_time, local_tz, sched_date)}")

        cap = (card.get("copy_draft_local") if use_local and card.get("copy_draft_local") else card.get("copy_draft_ko")) or ""
        st.markdown("**게시 캡션 미리보기**")
        st.text_area(" ", value=cap, height=140, label_visibility="collapsed")

        cbt1, cbt2, cbt3 = st.columns([1,1,1])
        with cbt1:
            if st.button("포스트 미리보기", type="secondary", use_container_width=True, key="modal_preview_btn"):
                st.session_state["modal_type"] = "preview"
                st.rerun()
        with cbt2:
            if st.button("발행하기", type="primary", use_container_width=True, key="modal_publish_btn"):
                st.error("Sprinklr와의 계정 연계가 필요합니다.")
        with cbt3:
            if st.button("취소", type="secondary", use_container_width=True, key="modal_cancel_btn"):
                st.session_state["modal_type"] = None
                st.session_state["modal_card_id"] = None
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def render_post_preview_modal(card: Dict[str, Any]):
    st.markdown("<div class='modal-wrap'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**🔎 포스트 미리보기**")
        platform = (card.get("recommended_channels") or ["Instagram"])[0]
        emoji = _platform_emoji(platform)
        evs = card.get("targeted_events", []) or []
        local_lang_kor, _ = detect_local_language(st.session_state.get("inputs_snapshot", {}).get("country", DEFAULT_COUNTRY))
        cap_ko = card.get("copy_draft_ko") or ""
        cap_local = card.get("copy_draft_local","")

        def pills_html(evs):
            parts = []
            for e in (evs or []):
                color = CAT_COLORS.get(e.get("category", ""), "#E5E7EB")
                d = e.get("date")
                label = f"{e.get('name','')} ({d})".strip() if d else f"{e.get('name','')}".strip()
                parts.append(f"<span class='pill' style='background:{color}'>{_esc(label)}</span>")
            return "<div class='pills'>" + "".join(parts) + "</div>"

        cap_ko_html = f"<p class='capline'><b>KR</b> · {_esc(cap_ko)}</p>" if cap_ko else ""
        cap_local_html = f"<p class='capline'><b>{_esc(local_lang_kor)}</b> · {_esc(cap_local)}</p>" if cap_local else ""

        st.markdown(f"""
        <div class="spost">
          <div class="sp-header">
            <div class="avatar">{_esc((st.session_state.get('inputs_snapshot',{}).get('brand') or 'B')[:1]).upper()}</div>
            <div>
              <div class="brand">{_esc(st.session_state.get('inputs_snapshot',{}).get('brand') or 'Brand')}</div>
              <div class="meta-line">{_esc(_format_time_for_header(date.fromisoformat(st.session_state.get('inputs_snapshot',{}).get('target_day', date.today().isoformat()))))}</div>
            </div>
            <div class="platform">{_esc(platform)} {emoji}</div>
          </div>
          <div class="sp-body">
            <div style="font-weight:600;margin-bottom:6px;">{_esc(card.get('title','아이디어'))}</div>
            {pills_html(evs)}
            <div class="concept-outer">
              <div class="concept-inner">
                <pre>[이미지 컨셉]
{_esc(card.get('image_concept',''))}</pre>
              </div>
            </div>
            {cap_ko_html}{cap_local_html}
            <div class="small-btn-row">
              <span class="badge">신뢰도 {card.get('confidence',0):.2f}</span>
              <span class="badge">구체성 {card.get('specificity_confidence',0):.2f}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("미리보기 닫기", type="secondary"):
            st.session_state["modal_type"] = None
            st.session_state["modal_card_id"] = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 모달 렌더링
if ss.get("modal_type") in {"preview", "publish", "edit"} and ss.get("modal_card_id"):
    the_card = next((c for c in ss.get("idea_cards", []) if c["id"] == ss["modal_card_id"]), None)
    if the_card:
        if ss["modal_type"] == "preview":
            render_post_preview_modal(the_card)
        elif ss["modal_type"] == "publish":
            render_publish_modal(the_card)
        elif ss["modal_type"] == "edit":
            render_edit_modal(the_card)

# ===============================
# 섹션: 연간 이벤트 캘린더 (타이틀 축소 + 버튼 secondary)
# ===============================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div style="font-size:0.95rem; font-weight:400;">📅 (참고) 연간 이벤트 캘린더 생성 및 다운로드</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1,1,3])
with c1:
    year = st.number_input("연도", min_value=2024, max_value=2027, value=2025, step=1)
with c2:
    gen_clicked = st.button(f"{int(year)} 전체 이벤트 생성", type="secondary")

if gen_clicked:
    with st.status("🗂️ 연간 이벤트 생성 중…", state="running") as s3:
        rows, err = generate_year_events_with_llm(
            int(year),
            country=st.session_state.get("inputs_snapshot",{}).get("country", DEFAULT_COUNTRY),
            model=st.session_state.get("inputs_snapshot",{}).get("model","gemini-2.5-flash"),
            temperature=0.35, thinking_off=True
        )
        if err or not rows:
            s3.update(label=f"❌ 연간 이벤트 생성 실패: {err or '결과 없음'}", state="error")
            st.error(f"연간 이벤트 생성 실패: {err or '결과 없음'}")
        else:
            blob, fname, mime = build_year_events_file(rows, int(year))
            st.session_state.setdefault("year_events_cache", {})[int(year)] = {"rows": rows, "bytes": blob, "name": fname, "mime": mime}
            s3.update(label=f"✅ {int(year)}년 이벤트 {len(rows)}건 · (월별≥10 보장) · 다운로드 준비 완료", state="complete")
            st.toast("연간 이벤트 파일 생성 완료", icon="✅")

cached = st.session_state.get("year_events_cache", {}).get(int(year))
if cached:
    st.download_button(
        f"{int(year)} 연간 이벤트 다운로드",
        data=cached["bytes"],
        file_name=cached["name"],
        mime=cached["mime"]
    )
