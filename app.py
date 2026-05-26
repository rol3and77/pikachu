import random
from difflib import SequenceMatcher

import streamlit as st

st.set_page_config(
    page_title="피카츄어 번역기",
    page_icon="⚡",
    layout="wide",
)

PICA_DICT = {
    "피캇츄~!": ["안녕!"],
    "피카피": ["한지우(사토시)"],
    "피피피~!": ["토게피"],
    "피핏카츄": ["로켓단 삼인방", "로사", "로이", "나옹"],
    "핏피카츄~!": ["넌 내꺼야!", "지우가 배지, Z크리스탈, 새로운 포켓몬을 얻었을 때의 표현"],
    "피카츄피": ["최이슬"],
    "피카츄": ["웅이", "데덴네"],
    "피피카": ["봄이"],
    "피카카": ["나빛나"],
    "피-카-": ["세레나"],
    "피-카츄": ["미안해"],
    "피-카-츄~?": ["괜찮아?"],
    "피카?": ["?", "질문"],
    "피카카피카": ["이상해씨"],
    "피카피카": ["꼬부기", "파이리", "라프라스", "코코리", "갸라도스", "아공이", "가재군", "이어롤", "핑복", "수댕이", "맘모꾸리", "터검니", "화살꼬빈"],
    "피카-피카": ["리자몽", "메리(니드런 암컷)"],
    "피카-피카!": ["작별 인사"],
    "피카-카": ["코산호", "몽얌나"],
    "피카, 피카츄!": ["난 피카츄!"],
    "피카피-카": ["치코리타", "잉어킹", "찌르호크"],
    "피카피-카-": ["시트론"],
    "피카피카츄": ["브케인"],
    "피캇피": ["고라파덕", "야나프"],
    "피카츄우": ["버터플"],
    "핏-카-": ["푸호꼬"],
    "핏카츄": ["팽도리"],
    "챠아~!": ["기분 좋을 때"],
    "피이카-피카!": ["전투 준비 완료!"],
    "피이카츄우우우우우": ["10만볼트"],
    "피카아, 츄우우우우우": ["번개"],
    "츄우-핏카!": ["아이언테일"],
    "피카피카피카피카-피카핏-카!": ["볼트태클"],
    "피카피카피카피카-츄피!": ["일렉트릭볼"],
    "피카피카피카피카-츄핏-카!": ["일렉트릭네트"],
    "피카!": ["응!", "알았어!", "맞아!"],
    "츄-": ["아니", "싫어"],
    "피~카~?": ["뭐라고~?"],
    "피카!! 피카츄우!! 피카츄우!! 피카!!": ["스파킹기가볼트"],
    "피카!! 피카 피카 피카!!": ["울트라대시어택"],
    "피이카아!! 피카카카카카피카피카아~!!": ["1000만볼트"],
    "피피!": ["코코"],
}


def normalize_text(text: str) -> str:
    text = text.replace("！", "!").replace("？", "?").replace("，", ",")
    return " ".join(text.split()).strip()


def clean_korean(text: str) -> str:
    text = normalize_text(text)
    for char in ["!", "?", ".", "~", ",", "'", '"']:
        text = text.replace(char, "")
    return " ".join(text.split()).strip()


def get_aliases(meaning: str) -> list[str]:
    aliases = [meaning, clean_korean(meaning)]
    if "한지우" in meaning:
        aliases += ["지우", "사토시", "한지우"]
    if "로켓단" in meaning:
        aliases += ["로켓단", "로사", "로이", "나옹"]
    if "전투 준비" in meaning:
        aliases += ["전투 준비", "전투 준비 완료"]
    if "작별" in meaning:
        aliases += ["작별", "잘가", "안녕히 가세요"]
    if "기분 좋" in meaning:
        aliases += ["기분 좋음", "좋아", "행복"]
    if "아니" in meaning or "싫어" in meaning:
        aliases += ["아니", "싫어"]
    if "응" in meaning or "알았어" in meaning or "맞아" in meaning:
        aliases += ["응", "알았어", "맞아"]
    if "넌 내꺼야" in meaning:
        aliases += ["넌 내꺼야", "내꺼야"]
    return list(dict.fromkeys([item for item in aliases if item]))


def build_reverse_dict() -> dict[str, list[str]]:
    reverse = {}
    for pika, meanings in PICA_DICT.items():
        for meaning in meanings:
            for alias in get_aliases(meaning):
                reverse.setdefault(alias, [])
                if pika not in reverse[alias]:
                    reverse[alias].append(pika)
    return reverse


BASE_REVERSE_DICT = build_reverse_dict()


def get_current_dict() -> dict[str, list[str]]:
    custom = st.session_state.get("custom_pica_dict", {})
    merged = {key: value[:] for key, value in PICA_DICT.items()}
    for key, value in custom.items():
        merged[key] = value[:]
    return merged


def get_current_reverse_dict() -> dict[str, list[str]]:
    current = get_current_dict()
    reverse = {}
    for pika, meanings in current.items():
        for meaning in meanings:
            for alias in get_aliases(meaning):
                reverse.setdefault(alias, [])
                if pika not in reverse[alias]:
                    reverse[alias].append(pika)
    return reverse


def detect_language(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return "unknown"
    current_dict = get_current_dict()
    if text in current_dict:
        return "pika"
    pika_keywords = ["피카", "피캇", "피이카", "피피", "피핏", "핏카", "츄", "챠아"]
    keyword_hits = sum(1 for keyword in pika_keywords if keyword in text)
    pika_chars = sum(text.count(ch) for ch in ["피", "카", "츄", "핏", "챠"])
    if keyword_hits >= 1 and pika_chars >= 2:
        return "pika"
    return "korean"


def resolve_mode(text: str, auto_mode: bool, manual_mode: str) -> str:
    if not auto_mode:
        return manual_mode
    return "피카츄어 → 한국어" if detect_language(text) == "pika" else "한국어 → 피카츄어"


def match_quality(matches: list[dict]) -> int:
    if not matches:
        return 0
    score = 0
    for match in matches:
        match_type = match.get("type", "")
        meanings = match.get("meanings", [])
        estimates = match.get("estimates", [])
        if match_type in ["등록된 표현", "정확히 일치"]:
            score += 100
        elif match_type == "부분 번역":
            score += 70
        elif match_type == "추정":
            score += 35
        if meanings and meanings[0] not in ["등록된 뜻 없음", "등록된 표현 없음"]:
            score += 25
        if estimates:
            score += 15
    return score


def translate_safely(text: str, auto_mode: bool, manual_mode: str) -> tuple[str, list[dict]]:
    if not text.strip():
        return resolve_mode(text, auto_mode, manual_mode), []

    if not auto_mode:
        mode = manual_mode
        matches = find_pika_to_korean(text) if mode == "피카츄어 → 한국어" else find_korean_to_pika(text)
        if matches:
            return mode, matches
        estimates, reasons = estimate_unknown_pika(text)
        return mode, [make_match(text, ["등록된 뜻 없음"], "추정", estimates, reasons)]

    pika_matches = find_pika_to_korean(text)
    korean_matches = find_korean_to_pika(text)
    pika_score = match_quality(pika_matches)
    korean_score = match_quality(korean_matches)

    # 피카츄어처럼 보이면 동점이어도 피카츄어 해석을 우선한다.
    detected = detect_language(text)
    if detected == "pika" and pika_score >= korean_score - 20:
        return "피카츄어 → 한국어", pika_matches
    if korean_score > pika_score:
        return "한국어 → 피카츄어", korean_matches
    if pika_matches:
        return "피카츄어 → 한국어", pika_matches

    estimates, reasons = estimate_unknown_pika(text)
    return "피카츄어 → 한국어", [make_match(text, ["등록된 뜻 없음"], "추정", estimates, reasons)]


def confidence_label(score: float) -> str:
    if score >= 0.78:
        return "높음"
    if score >= 0.62:
        return "보통"
    return "낮음"


def similarity_candidates(word: str) -> list[dict]:
    results = []
    current_dict = get_current_dict()
    for candidate, meanings in current_dict.items():
        score = SequenceMatcher(None, word, candidate).ratio()
        simple_word = word.replace("!", "").replace("?", "")
        simple_candidate = candidate.replace("!", "").replace("?", "")
        if simple_word and simple_word in simple_candidate:
            score += 0.12
        if simple_candidate and simple_candidate in simple_word:
            score += 0.12
        if "우우" in word and "우우" in candidate:
            score += 0.12
        if "피이카" in word and "피이카" in candidate:
            score += 0.08
        if "츄우" in word and "츄우" in candidate:
            score += 0.08
        score = min(score, 1.0)
        if candidate != word and score >= 0.48:
            results.append({
                "candidate": candidate,
                "meaning": meanings[0],
                "score": score,
                "confidence": confidence_label(score),
            })
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:3]


def estimate_registered(phrase: str, meanings: list[str]) -> tuple[list[str], list[str]]:
    joined = ", ".join(meanings)
    estimates = []
    reasons = [f'사전에 "{phrase}" 표현이 등록되어 있습니다.']
    if any(token in joined for token in ["10만볼트", "번개", "아이언테일", "볼트태클", "일렉트릭", "스파킹", "울트라"]):
        estimates.append("기술명 또는 전투 중 공격 표현")
    if any(token in joined for token in ["안녕", "작별", "뭐라고", "괜찮아", "미안", "응", "아니", "싫어"]):
        estimates.append("일상 대화 또는 감정 반응 표현")
    if any(token in joined for token in ["한지우", "최이슬", "웅이", "봄이", "나빛나", "세레나", "시트론", "로켓단"]):
        estimates.append("특정 인물이나 대상을 부르는 호칭")
    if any(token in joined for token in ["꼬부기", "파이리", "리자몽", "버터플", "브케인", "팽도리", "코코"]):
        estimates.append("특정 포켓몬을 가리키는 호칭")
    if len(meanings) >= 2:
        estimates.append("문맥에 따라 여러 의미로 해석될 수 있음")
    if not estimates:
        estimates.append("등록된 뜻을 기준으로 해석하는 표현")
    return estimates, reasons


def add_score(scores: dict, label: str, points: int, reason: str):
    if label not in scores:
        scores[label] = {"score": 0, "reasons": []}
    scores[label]["score"] += points
    scores[label]["reasons"].append(reason)


def pattern_score_estimation(word: str) -> tuple[list[str], list[str]]:
    scores = {}
    clean = word.replace(" ", "")

    pi = clean.count("피")
    ka = clean.count("카")
    chu = clean.count("츄")
    pika = clean.count("피카")
    long_u = clean.count("우")
    long_a = clean.count("아")
    ex = clean.count("!")
    q = clean.count("?")
    dash = clean.count("-")
    wave = clean.count("~")
    length = len(clean)

    # 의문/확인 계열
    if q >= 1:
        add_score(scores, "질문 또는 되묻는 표현", 45, "물음표가 포함되어 있어 질문형 표현 가능성이 큽니다.")
        if wave >= 1:
            add_score(scores, "부드럽게 확인하는 표현", 30, "물음표와 물결표가 함께 있어 단순 질문보다 부드럽게 되묻는 느낌이 강합니다.")
        if dash >= 1:
            add_score(scores, "조심스럽게 확인하는 표현", 25, "물음표와 하이픈이 함께 있어 조심스럽게 확인하는 말투로 볼 수 있습니다.")

    # 전투/기술 계열
    if long_u >= 3 or "츄우" in clean:
        add_score(scores, "전기 기술 또는 공격 표현", 50, "'우'가 길게 반복되거나 '츄우'가 들어가 에너지를 방출하는 기술 표현처럼 보입니다.")
    if ex >= 2:
        add_score(scores, "강한 외침 또는 전투 표현", 35, "느낌표가 여러 개라 감정 강도가 높고 전투 중 외침처럼 보입니다.")
    if length >= 12 and ex >= 1:
        add_score(scores, "기술명 계열 표현", 35, "표현이 길고 느낌표가 있어 일반 대화보다 기술명에 가깝습니다.")
    if pika >= 4:
        add_score(scores, "고조된 기술명 계열 표현", 40, "'피카'가 여러 번 반복되어 리듬이 있는 기술명 패턴에 가깝습니다.")

    # 일상 감정/반응 계열
    if ex == 1 and length <= 8:
        add_score(scores, "짧은 긍정 또는 감정 반응", 30, "짧은 표현에 느낌표가 하나 있어 간단한 반응이나 감정 표현으로 보입니다.")
    if wave >= 1 and q == 0:
        add_score(scores, "부드럽거나 기분 좋은 감정 표현", 30, "물결표가 있어 말끝을 늘이는 감정 표현으로 보입니다.")
    if dash >= 1 and q == 0:
        add_score(scores, "망설임 또는 조심스러운 감정 표현", 28, "하이픈이 있어 말이 끊기며 조심스럽거나 미안한 느낌을 줄 수 있습니다.")
    if clean == "츄" or clean.startswith("츄-"):
        add_score(scores, "부정 또는 거절 표현", 45, "등록 사전에서 '츄-'가 부정/거절 의미로 쓰이므로 비슷한 부정 반응으로 볼 수 있습니다.")
    if clean.startswith("피카") and ex == 1 and q == 0 and length <= 6:
        add_score(scores, "긍정 또는 짧은 대답", 35, "짧은 '피카' 계열 감탄은 응답이나 긍정 표현으로 쓰일 가능성이 있습니다.")

    # 호칭/대상 지칭 계열
    if 4 <= length <= 8 and ex == 0 and q == 0 and long_u <= 1:
        add_score(scores, "인물 또는 포켓몬을 부르는 호칭", 35, "길이가 짧고 강한 기호가 없어 특정 대상을 부르는 호칭일 가능성이 있습니다.")
    if pi + ka + chu >= 4 and ex == 0 and q == 0:
        add_score(scores, "대상 지칭 또는 이름 표현", 25, "피/카/츄 음절 조합이 중심이고 문장 기호가 없어 이름처럼 쓰였을 가능성이 있습니다.")

    if not scores:
        return ["새로운 피카츄어 표현"], ["뚜렷한 기호 패턴은 없지만 피카츄어 음절 조합으로 이루어져 있어 새로운 표현으로 추정했습니다."]

    ranked = sorted(scores.items(), key=lambda item: item[1]["score"], reverse=True)
    top_score = ranked[0][1]["score"]
    estimates = []
    reasons = []

    for label, data in ranked[:3]:
        if data["score"] >= max(25, top_score - 20):
            estimates.append(label)
            reasons.append(f'{label}: 점수 {data["score"]}점')
            for reason in data["reasons"][:2]:
                reasons.append("- " + reason)

    return estimates, reasons


def estimate_unknown_pika(word: str) -> tuple[list[str], list[str]]:
    pattern_estimates, pattern_reasons = pattern_score_estimation(word)
    similar = similarity_candidates(word)

    estimates = []
    reasons = []

    # 사전과 매우 비슷한 경우에만 사전 뜻을 1순위로 올림.
    if similar and similar[0]["score"] >= 0.84:
        best = similar[0]
        estimates.append(best["meaning"])
        reasons.append(
            f'등록 표현 "{best["candidate"]}"와 거의 같은 형태입니다. 등록 뜻은 "{best["meaning"]}"이고 유사도는 {best["score"]:.2f}입니다.'
        )
        estimates += pattern_estimates[:2]
        reasons += pattern_reasons
    else:
        # 애매하면 사전 뜻보다 패턴 해석을 먼저 보여줌.
        estimates += pattern_estimates
        reasons += pattern_reasons
        if similar:
            best = similar[0]
            estimates.append(f'{best["meaning"]} 계열 가능성')
            reasons.append(
                f'참고로 가장 가까운 등록 표현은 "{best["candidate"]}"입니다. 등록 뜻은 "{best["meaning"]}"이고 유사도는 {best["score"]:.2f}입니다. 다만 완전 일치가 아니므로 보조 근거로만 사용했습니다.'
            )

    for item in similar[1:3]:
        reasons.append(
            f'추가 비교 후보: "{item["candidate"]}" → "{item["meaning"]}" / 유사도 {item["score"]:.2f}'
        )

    estimates = list(dict.fromkeys(estimates))
    reasons = list(dict.fromkeys(reasons))
    return estimates, reasons


def make_match(phrase: str, meanings: list[str], match_type: str, estimates=None, reasons=None) -> dict:
    return {
        "phrase": phrase,
        "meanings": meanings,
        "type": match_type,
        "estimates": estimates or [],
        "reasons": reasons or [],
    }


def find_pika_to_korean(text: str) -> list[dict]:
    text = normalize_text(text)
    if not text:
        return []
    current_dict = get_current_dict()
    if text in current_dict:
        estimates, reasons = estimate_registered(text, current_dict[text])
        return [make_match(text, current_dict[text], "등록된 표현", estimates, reasons)]
    matches = []
    remaining = text
    for key in sorted(current_dict.keys(), key=len, reverse=True):
        if key in remaining:
            estimates, reasons = estimate_registered(key, current_dict[key])
            matches.append(make_match(key, current_dict[key], "등록된 표현", estimates, reasons))
            remaining = remaining.replace(key, " ")
    for item in [part.strip() for part in remaining.split() if part.strip()]:
        estimates, reasons = estimate_unknown_pika(item)
        matches.append(make_match(item, ["등록된 뜻 없음"], "추정", estimates, reasons))
    if not matches:
        estimates, reasons = estimate_unknown_pika(text)
        matches.append(make_match(text, ["등록된 뜻 없음"], "추정", estimates, reasons))
    return matches


def find_korean_to_pika(text: str) -> list[dict]:
    text = clean_korean(text)
    if not text:
        return []
    reverse_dict = get_current_reverse_dict()
    if text in reverse_dict:
        return [make_match(text, reverse_dict[text], "정확히 일치", ["등록된 한국어 뜻과 정확히 일치"], [f'한국어 뜻 "{text}"가 사전에 등록되어 있습니다.'])]
    matches = []
    used = set()
    for word in [part.strip() for part in text.split() if part.strip()]:
        if word in reverse_dict:
            matches.append(make_match(word, reverse_dict[word], "정확히 일치", ["등록된 한국어 뜻과 정확히 일치"], [f'한국어 뜻 "{word}"가 사전에 등록되어 있습니다.']))
            used.add(word)
    for key in sorted(reverse_dict.keys(), key=len, reverse=True):
        cleaned_key = clean_korean(key)
        if cleaned_key and cleaned_key not in used and cleaned_key in text:
            matches.append(make_match(key, REVERSE_DICT[key], "부분 번역", ["입력 문장 안에 등록된 뜻이 포함됨"], [f'입력문 안에 등록된 한국어 뜻 "{key}"가 포함되어 있습니다.']))
            used.add(cleaned_key)
    if matches:
        return matches
    return [make_match(text, ["등록된 표현 없음"], "추정", ["아직 대응되는 피카츄어가 사전에 없습니다"], ["한국어 뜻과 정확히 일치하거나 부분 일치하는 등록 항목을 찾지 못했습니다."])]


def representative_sentence(matches: list[dict], mode: str) -> str:
    pieces = []
    for match in matches:
        meanings = match.get("meanings", [])
        if meanings and meanings[0] not in ["등록된 뜻 없음", "등록된 표현 없음"]:
            pieces.append(meanings[0])
        elif match.get("estimates"):
            pieces.append(match["estimates"][0])
    if not pieces:
        return ""
    if len(pieces) == 1:
        return pieces[0]
    if mode == "한국어 → 피카츄어":
        return " ".join(pieces)
    sentence = pieces[0]
    for word in pieces[1:]:
        word = str(word).strip()
        if any(token in word for token in ["응", "알았어", "맞아"]):
            sentence += ", 알았어!"
        elif any(token in word for token in ["아니", "싫어"]):
            sentence += ", 아니야."
        elif "미안" in word:
            sentence += ", 미안해."
        elif "괜찮아" in word:
            sentence += ", 괜찮아?"
        elif any(token in word for token in ["10만볼트", "번개", "아이언테일", "볼트태클", "일렉트릭", "스파킹", "울트라"]):
            sentence += f", {word}!"
        else:
            sentence += f" {word}"
    return sentence


def search_dictionary(query: str) -> list[tuple[str, list[str]]]:
    query = clean_korean(query)
    if not query:
        return []
    results = []
    for pika, meanings in get_current_dict().items():
        joined = " ".join([pika] + meanings)
        if query in clean_korean(joined):
            results.append((pika, meanings))
    return results


def render_match_card(match: dict):
    st.markdown(f"**{match['phrase']}** · {match['type']}")
    st.write("등록된 뜻:", ", ".join(match.get("meanings", [])))
    if match.get("estimates"):
        st.write("추정 해석:", ", ".join(match["estimates"]))
    if match.get("reasons"):
        with st.expander("왜 그렇게 추정했는지 보기", expanded=False):
            for reason in match["reasons"]:
                st.write("-", reason)


st.markdown(
    """
    <style>
    .stApp {background: radial-gradient(circle at top left, #fff2a8 0, transparent 35%), radial-gradient(circle at bottom right, #ffe066 0, transparent 30%), #fff8d6;}
    .main-title {font-size: 3rem; font-weight: 900; letter-spacing: -0.06em; color: #5c3b18; margin-bottom: 0.25rem;}
    .subtitle {color: #75684f; font-size: 1.05rem; line-height: 1.7; margin-bottom: 1.2rem;}
    .result-panel {min-height: 260px; background: #fffdf3; border: 2px dashed #ead17d; border-radius: 18px; padding: 1rem;}
    .sentence-card {background: #ffffff; border: 2px solid #ffd43b; border-radius: 18px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 8px 18px rgba(242,183,5,0.14);}
    .small-label {display: inline-block; background: white; color: #8a6a00; border: 1px solid #ecd276; border-radius: 999px; padding: 0.2rem 0.55rem; font-size: 0.75rem; font-weight: 800; margin-bottom: 0.4rem;}
    .phrase {font-size: 1.2rem; font-weight: 900; color: #5c3b18; line-height: 1.6;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">⚡ 피카츄어 번역기</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">입력한 언어를 자동 감지해서 번역합니다. 등록된 표현은 등록 뜻을 우선하고, 등록되지 않은 표현은 비슷한 단어와 패턴을 바탕으로 추정합니다.</div>', unsafe_allow_html=True)

if "example_text" not in st.session_state:
    st.session_state.example_text = ""
if "translation_result" not in st.session_state:
    st.session_state.translation_result = None
if "custom_pica_dict" not in st.session_state:
    st.session_state.custom_pica_dict = {}

auto_mode = st.toggle("언어 자동 감지", value=True)
manual_mode = "피카츄어 → 한국어"
if not auto_mode:
    manual_mode = st.radio("번역 방향", ["피카츄어 → 한국어", "한국어 → 피카츄어"], horizontal=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("번역할 언어 입력")
    user_input = st.text_area(
        "입력",
        value=st.session_state.example_text,
        height=260,
        placeholder="예: 피캇츄~! 피카피 피카! 또는 안녕 한지우 알았어",
        label_visibility="collapsed",
    )

    translate_clicked = st.button("번역하기", type="primary", use_container_width=True)

    if translate_clicked:
        if not user_input.strip():
            st.session_state.translation_result = {
                "status": "empty",
                "message": "번역할 문장을 입력해주세요.",
            }
        else:
            mode, matches = translate_safely(user_input, auto_mode, manual_mode)
            sentence = representative_sentence(matches, mode)
            st.session_state.translation_result = {
                "status": "ok",
                "mode": mode,
                "sentence": sentence,
                "matches": matches,
            }

    if st.button("랜덤 예문 넣기", use_container_width=True):
        st.session_state.example_text = random.choice([
            "피캇츄~! 피카피 피카!",
            "피이카-피카! 피이카츄우우우우우",
            "피~카~?",
            "안녕 한지우 알았어",
            "전투 준비 완료 10만볼트",
        ])
        st.session_state.translation_result = None
        st.rerun()

with right:
    st.subheader("해석 결과")
    saved = st.session_state.translation_result

    if saved is None:
        st.markdown('<div class="result-panel">왼쪽 입력칸에 문장을 입력하고 번역하기 버튼을 눌러주세요.</div>', unsafe_allow_html=True)
    elif saved.get("status") == "empty":
        st.markdown(f'<div class="result-panel">{saved.get("message", "번역할 문장을 입력해주세요.")}</div>', unsafe_allow_html=True)
    else:
        mode = saved.get("mode", "")
        sentence = saved.get("sentence", "")
        matches = saved.get("matches", [])
        st.caption(f"감지된 번역 방향: {mode}")
        st.markdown(
            f'''
            <div class="result-panel">
                <div class="sentence-card">
                    <div class="small-label">대표 해석</div>
                    <div class="phrase">{sentence if sentence else "해석 결과 없음"}</div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        with st.expander("단어별 해석 보기", expanded=False):
            for match in matches:
                render_match_card(match)
                st.divider()

st.divider()
st.subheader("새 피카츄어 표현 등록")
st.caption("앱을 실행 중인 동안 새 표현이 바로 사전에 반영됩니다. Streamlit Cloud에서 재시작하면 기본 사전으로 돌아갈 수 있습니다.")

with st.form("add_new_expression", clear_on_submit=True):
    new_pika = st.text_input("새 피카츄어", placeholder="예: 피카츄우웅!")
    new_meaning = st.text_input("뜻", placeholder="예: 신난 피카츄의 외침")
    submitted = st.form_submit_button("사전에 등록하기", use_container_width=True)

    if submitted:
        new_pika = normalize_text(new_pika)
        new_meaning = normalize_text(new_meaning)
        if not new_pika or not new_meaning:
            st.warning("피카츄어와 뜻을 모두 입력해주세요.")
        else:
            current_custom = st.session_state.custom_pica_dict
            if new_pika in PICA_DICT:
                base_meanings = PICA_DICT[new_pika][:]
                if new_meaning not in base_meanings:
                    st.session_state.custom_pica_dict[new_pika] = base_meanings + [new_meaning]
                else:
                    st.session_state.custom_pica_dict[new_pika] = base_meanings
            else:
                current_custom.setdefault(new_pika, [])
                if new_meaning not in current_custom[new_pika]:
                    current_custom[new_pika].append(new_meaning)
                st.session_state.custom_pica_dict = current_custom
            st.session_state.translation_result = None
            st.success(f'"{new_pika}" → "{new_meaning}" 등록 완료')

if st.session_state.custom_pica_dict:
    with st.expander("내가 새로 등록한 표현 보기", expanded=False):
        for pika, meanings in st.session_state.custom_pica_dict.items():
            st.write(f"**{pika}** → {', '.join(meanings)}")

st.divider()
st.subheader("사전 검색")
query = st.text_input("피카츄어 또는 한국어 뜻 검색", placeholder="예: 꼬부기, 10만볼트, 피카피")
if query.strip():
    results = search_dictionary(query)
    if results:
        for pika, meanings in results:
            st.write(f"**{pika}** → {', '.join(meanings)}")
    else:
        st.info("검색 결과가 없습니다.")

with st.expander("등록된 피카츄어 사전 전체 보기", expanded=False):
    for pika, meanings in get_current_dict().items():
        st.write(f"**{pika}** → {', '.join(meanings)}")
