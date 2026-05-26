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


REVERSE_DICT = build_reverse_dict()


def detect_language(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return "unknown"
    if text in PICA_DICT:
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


def confidence_label(score: float) -> str:
    if score >= 0.78:
        return "높음"
    if score >= 0.62:
        return "보통"
    return "낮음"


def similarity_candidates(word: str) -> list[dict]:
    results = []
    for candidate, meanings in PICA_DICT.items():
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


def analyze_pika_pattern(word: str) -> tuple[list[str], list[str]]:
    estimates = []
    reasons = []
    clean = word.replace(" ", "")

    pika_count = clean.count("피카")
    pi_count = clean.count("피")
    ka_count = clean.count("카")
    chu_count = clean.count("츄")
    long_vowel_count = clean.count("우") + clean.count("아") + clean.count("이")
    exclamation_count = clean.count("!")
    question_count = clean.count("?")
    dash_count = clean.count("-")
    wave_count = clean.count("~")

    if question_count > 0:
        if wave_count > 0 or dash_count > 0:
            estimates.append("상대의 상태를 확인하거나 부드럽게 되묻는 표현")
            reasons.append("물음표와 물결표/하이픈이 함께 있어 단순 질문보다 조심스럽거나 부드러운 확인 표현으로 보았습니다.")
        else:
            estimates.append("질문 또는 의문 표현")
            reasons.append("물음표가 포함되어 있어 질문형 표현으로 분류했습니다.")

    if exclamation_count >= 2:
        estimates.append("흥분, 전투, 강한 외침")
        reasons.append("느낌표가 여러 번 반복되어 감정이 강하거나 전투 상황에서 외치는 표현으로 보았습니다.")
    elif exclamation_count == 1:
        estimates.append("강조 또는 감정 반응")
        reasons.append("느낌표가 포함되어 있어 평서문보다 강조된 감정 반응으로 보았습니다.")

    if "우우" in clean or "츄우" in clean or long_vowel_count >= 5:
        estimates.append("전기 기술 또는 에너지를 모으는 공격 표현")
        reasons.append("'우우', '츄우'처럼 소리를 길게 끄는 패턴은 기술명이나 에너지 방출 표현에서 자주 쓰일 수 있습니다.")

    if dash_count >= 2:
        estimates.append("망설임, 조심스러운 감정, 특정 대상을 부르는 표현")
        reasons.append("하이픈이 여러 번 들어가 말이 끊기는 느낌이 강하므로 망설임이나 조심스러운 호칭으로 추정했습니다.")
    elif dash_count == 1:
        estimates.append("짧게 끊어 말하는 감정 표현")
        reasons.append("하이픈이 있어 일반 감탄보다 끊어서 말하는 표현으로 보았습니다.")

    if wave_count > 0:
        estimates.append("부드럽거나 감정을 늘여 말하는 표현")
        reasons.append("물결표가 있어 말끝을 늘이는 감정 표현으로 추정했습니다.")

    if pika_count >= 4:
        estimates.append("고조된 전투 기술명 또는 긴장감 있는 외침")
        reasons.append("'피카'가 여러 번 반복되어 단순 호칭보다 리듬감 있는 기술명 계열 표현으로 보았습니다.")
    elif pika_count >= 2:
        estimates.append("기쁨, 호명, 반복 강조 표현")
        reasons.append("'피카' 반복이 있어 단어 하나보다 강조된 감정이나 호명 표현으로 보았습니다.")

    if chu_count >= 2 and exclamation_count == 0:
        estimates.append("친근한 호칭 또는 부드러운 반응")
        reasons.append("'츄'가 반복되지만 강한 느낌표가 없어 공격보다는 부드러운 반응 쪽으로 추정했습니다.")

    if pi_count + ka_count + chu_count <= 3 and exclamation_count == 0 and question_count == 0:
        estimates.append("짧은 호칭 또는 짧은 반응")
        reasons.append("표현 길이가 짧고 강한 기호가 없어 짧은 호칭이나 간단한 반응일 가능성이 있습니다.")

    return estimates, reasons


def estimate_unknown_pika(word: str) -> tuple[list[str], list[str]]:
    estimates = []
    reasons = []

    pattern_estimates, pattern_reasons = analyze_pika_pattern(word)
    estimates += pattern_estimates
    reasons += pattern_reasons

    similar = similarity_candidates(word)
    if similar:
        best = similar[0]
        if best["score"] >= 0.78:
            estimates.insert(0, best["meaning"])
            reasons.insert(
                0,
                f'등록 표현 "{best["candidate"]}"와 매우 유사하여 대표 추정에 반영했습니다. 등록 뜻은 "{best["meaning"]}"이고 유사도는 {best["score"]:.2f}입니다.'
            )
        else:
            estimates.append(f'{best["meaning"]} 계열일 가능성')
            reasons.append(
                f'가장 가까운 등록 표현은 "{best["candidate"]}"입니다. 등록 뜻은 "{best["meaning"]}"이고 유사도는 {best["score"]:.2f}, 신뢰도는 {best["confidence"]}입니다.'
            )

        for item in similar[1:]:
            reasons.append(
                f'비교 후보: "{item["candidate"]}" → "{item["meaning"]}" / 유사도 {item["score"]:.2f}, 신뢰도 {item["confidence"]}'
            )

    estimates = list(dict.fromkeys(estimates))
    reasons = list(dict.fromkeys(reasons))
    if not estimates:
        estimates = ["새로운 피카츄어 표현"]
        reasons = ["등록된 표현과 충분히 비슷하지는 않지만, 피/카/츄 계열 음절로 구성되어 있어 새로운 피카츄어 표현으로 추정했습니다."]
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
    if text in PICA_DICT:
        estimates, reasons = estimate_registered(text, PICA_DICT[text])
        return [make_match(text, PICA_DICT[text], "등록된 표현", estimates, reasons)]
    matches = []
    remaining = text
    for key in sorted(PICA_DICT.keys(), key=len, reverse=True):
        if key in remaining:
            estimates, reasons = estimate_registered(key, PICA_DICT[key])
            matches.append(make_match(key, PICA_DICT[key], "등록된 표현", estimates, reasons))
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
    if text in REVERSE_DICT:
        return [make_match(text, REVERSE_DICT[text], "정확히 일치", ["등록된 한국어 뜻과 정확히 일치"], [f'한국어 뜻 "{text}"가 사전에 등록되어 있습니다.'])]
    matches = []
    used = set()
    for word in [part.strip() for part in text.split() if part.strip()]:
        if word in REVERSE_DICT:
            matches.append(make_match(word, REVERSE_DICT[word], "정확히 일치", ["등록된 한국어 뜻과 정확히 일치"], [f'한국어 뜻 "{word}"가 사전에 등록되어 있습니다.']))
            used.add(word)
    for key in sorted(REVERSE_DICT.keys(), key=len, reverse=True):
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
    for pika, meanings in PICA_DICT.items():
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
            mode = resolve_mode(user_input, auto_mode, manual_mode)
            matches = find_pika_to_korean(user_input) if mode == "피카츄어 → 한국어" else find_korean_to_pika(user_input)
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
    for pika, meanings in PICA_DICT.items():
        st.write(f"**{pika}** → {', '.join(meanings)}")
