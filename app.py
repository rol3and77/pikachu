import streamlit as st
from difflib import get_close_matches, SequenceMatcher

st.set_page_config(
    page_title="피카츄어 번역기",
    page_icon="⚡",
    layout="centered",
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
    "피카피카": [
        "꼬부기", "파이리", "라프라스", "코코리", "갸라도스", "아공이", "가재군",
        "이어롤", "핑복", "수댕이", "맘모꾸리", "터검니", "화살꼬빈"
    ],
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
    return (
        text.replace("！", "!")
        .replace("？", "?")
        .replace("，", ",")
        .strip()
    )


def clean_korean(text: str) -> str:
    remove_chars = "!?.~"
    cleaned = normalize_text(text)
    for char in remove_chars:
        cleaned = cleaned.replace(char, "")
    return " ".join(cleaned.split()).strip()


def get_aliases(meaning: str) -> list[str]:
    plain = clean_korean(meaning)
    aliases = [meaning, plain]

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


def guess_pika_meaning(word: str) -> list[str]:
    guesses = []

    if "우우우" in word or "츄우" in word:
        guesses.append("전기 기술 또는 강한 공격 표현일 가능성이 큼")
    if "?" in word:
        guesses.append("질문, 확인, 되묻는 표현일 가능성이 큼")
    if "!" in word and len(word) > 12:
        guesses.append("기술명 또는 강한 감정 표현일 가능성이 큼")
    elif "!" in word:
        guesses.append("강조, 기쁨, 놀람 계열 표현일 가능성이 큼")
    if "~" in word:
        guesses.append("감정을 길게 늘여 말하는 표현일 가능성이 큼")
    if "-" in word:
        guesses.append("감정이 끊기거나 조심스럽게 말하는 표현일 가능성이 있음")

    guesses += guess_by_similarity(word)

    if not guesses:
        guesses.append("아직 사전에 없는 표현입니다. 비슷한 등록 표현도 뚜렷하지 않습니다.")

    return list(dict.fromkeys(guesses))


def guess_by_similarity(word: str) -> list[str]:
    guesses = []
    candidates = get_close_matches(word, PICA_DICT.keys(), n=3, cutoff=0.55)

    for candidate in candidates:
        if candidate == word:
            continue
        score = SequenceMatcher(None, word, candidate).ratio()
        meaning = ", ".join(PICA_DICT[candidate])
        guesses.append(f'등록 표현 "{candidate}"와 비슷함: {meaning} 계열일 가능성 있음 / 유사도 {score:.2f}')

    return guesses


def estimate_registered_pika(word: str, meanings: list[str]) -> list[str]:
    estimates = []
    joined = ", ".join(meanings)

    if any(token in joined for token in ["10만볼트", "번개", "아이언테일", "볼트태클", "일렉트릭", "스파킹", "울트라"]):
        estimates.append("기술명 또는 전투 중 공격 표현으로 해석할 수 있음")
    if any(token in joined for token in ["안녕", "작별", "뭐라고", "괜찮아", "미안", "응", "아니", "싫어"]):
        estimates.append("일상 대화나 감정 반응 표현으로 해석할 수 있음")
    if len(meanings) >= 2:
        estimates.append("하나의 표현에 여러 뜻이 있으므로 문맥에 따라 의미가 달라질 수 있음")
    if any(token in joined for token in ["한지우", "최이슬", "웅이", "봄이", "나빛나", "세레나", "시트론", "로켓단"]):
        estimates.append("특정 인물이나 대상을 부르는 호칭으로 해석할 수 있음")
    if any(token in joined for token in ["꼬부기", "파이리", "리자몽", "버터플", "브케인", "팽도리", "코코"]):
        estimates.append("특정 포켓몬을 가리키는 호칭으로 해석할 수 있음")

    if not estimates:
        estimates.append("등록된 뜻을 기준으로 해석하는 표현입니다")

    return estimates


def find_pika_to_korean(text: str) -> list[dict]:
    text = normalize_text(text)
    if not text:
        return []

    if text in PICA_DICT:
        return [{
            "phrase": text,
            "meanings": PICA_DICT[text],
            "type": "등록된 표현",
            "estimates": estimate_registered_pika(text, PICA_DICT[text]),
        }]

    matches = []
    remaining = text

    for key in sorted(PICA_DICT.keys(), key=len, reverse=True):
        if key in remaining:
            matches.append({
                "phrase": key,
                "meanings": PICA_DICT[key],
                "type": "등록된 표현",
                "estimates": estimate_registered_pika(key, PICA_DICT[key]),
            })
            remaining = remaining.replace(key, " ")

    leftovers = [item.strip() for item in remaining.split() if item.strip()]
    for item in leftovers:
        matches.append({
            "phrase": item,
            "meanings": ["등록된 뜻 없음"],
            "type": "추정",
            "estimates": guess_pika_meaning(item),
        })

    if not matches:
        matches.append({
            "phrase": text,
            "meanings": ["등록된 뜻 없음"],
            "type": "추정",
            "estimates": guess_pika_meaning(text),
        })

    return matches


def find_korean_to_pika(text: str) -> list[dict]:
    text = clean_korean(text)
    if not text:
        return []

    if text in REVERSE_DICT:
        return [{"phrase": text, "meanings": REVERSE_DICT[text], "type": "정확히 일치"}]

    matches = []
    for key in sorted(REVERSE_DICT.keys(), key=len, reverse=True):
        cleaned_key = clean_korean(key)
        if cleaned_key and cleaned_key in text:
            matches.append({"phrase": key, "meanings": REVERSE_DICT[key], "type": "부분 번역"})

    if not matches:
        matches.append({"phrase": text, "meanings": ["아직 대응되는 피카츄어가 사전에 없습니다"], "type": "추정"})

    return matches


def make_sentence(matches: list[dict], mode: str) -> str:
    valid = [m for m in matches if m["type"] != "추정"]
    if len(valid) < 2:
        return ""

    pieces = [m["meanings"][0] for m in valid if m.get("meanings")]

    if mode == "한국어 → 피카츄어":
        return " ".join(pieces)

    sentence = pieces[0]
    for word in pieces[1:]:
        clean = word.replace("의 표현", "").replace("일 때의 표현", "").strip()

        if any(token in clean for token in ["응", "알았어", "맞아"]):
            sentence += ", 알았어!"
        elif any(token in clean for token in ["아니", "싫어"]):
            sentence += ", 아니야."
        elif "미안" in clean:
            sentence += ", 미안해."
        elif "괜찮아" in clean:
            sentence += ", 괜찮아?"
        elif "전투 준비" in clean:
            sentence += ", 전투 준비 완료!"
        elif any(token in clean for token in ["10만볼트", "번개", "아이언테일", "볼트태클", "일렉트릭", "스파킹", "울트라"]):
            sentence += f", {clean}!"
        else:
            sentence += f" {clean}"

    return sentence


st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #fff2a8 0, transparent 35%),
                    radial-gradient(circle at bottom right, #ffe066 0, transparent 30%),
                    #fff8d6;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -0.06em;
        color: #5c3b18;
        margin-bottom: 0.4rem;
    }
    .subtitle {
        color: #75684f;
        font-size: 1.05rem;
        line-height: 1.7;
        margin-bottom: 1.2rem;
    }
    .result-panel {
        min-height: 220px;
        background: #fffdf3;
        border: 2px dashed #ead17d;
        border-radius: 18px;
        padding: 1rem;
    }
    .result-card {
        background: #fff5bf;
        border: 1px solid #efd56f;
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .sentence-card {
        background: #ffffff;
        border: 2px solid #ffd43b;
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 18px rgba(242, 183, 5, 0.14);
    }
    .small-label {
        display: inline-block;
        background: white;
        color: #8a6a00;
        border: 1px solid #ecd276;
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 800;
        margin-bottom: 0.4rem;
    }
    .phrase {
        font-size: 1.1rem;
        font-weight: 900;
        color: #5c3b18;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">⚡ 피카츄어 번역기</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">왼쪽에 피카츄어 또는 한국어를 입력하면 오른쪽에 번역 결과가 표시됩니다. 두 단어 이상 해석되면 자연스럽게 이어진 문장도 함께 보여줍니다.</div>',
    unsafe_allow_html=True,
)

mode = st.radio(
    "번역 방향",
    ["피카츄어 → 한국어", "한국어 → 피카츄어"],
    horizontal=True,
)

input_col, output_col = st.columns([1, 1], gap="large")

with input_col:
    st.subheader("번역할 언어 입력")
    user_input = st.text_area(
        "",
        value="",
        height=260,
        placeholder="예: 피캇츄~! 피카피 피카!" if mode == "피카츄어 → 한국어" else "예: 안녕 한지우 알았어",
        label_visibility="collapsed",
    )
    translate_clicked = st.button("번역하기", type="primary", use_container_width=True)

with output_col:
    st.subheader("해석 결과")
    st.markdown('<div class="result-panel">', unsafe_allow_html=True)

    if not translate_clicked:
        st.markdown(
            '<div class="empty">왼쪽 입력칸에 문장을 입력하고 번역하기 버튼을 눌러주세요.</div>',
            unsafe_allow_html=True,
        )
    elif not user_input.strip():
        st.markdown(
            '<div class="empty">번역할 문장을 입력해주세요.</div>',
            unsafe_allow_html=True,
        )
    else:
        matches = find_pika_to_korean(user_input) if mode == "피카츄어 → 한국어" else find_korean_to_pika(user_input)
        sentence = make_sentence(matches, mode)

        if sentence:
            st.markdown(
                f"""
                <div class="sentence-card">
                    <div class="small-label">문장으로 연결한 해석</div>
                    <div class="phrase">{sentence}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("단어별 해석 보기", expanded=False):
            for match in matches:
                meanings = match["meanings"]
                if len(meanings) == 1:
                    meaning_html = meanings[0]
                else:
                    meaning_html = "<ul>" + "".join(f"<li>{item}</li>" for item in meanings) + "</ul>"

                estimates = match.get("estimates", [])
                if estimates:
                    estimate_html = "<hr style='border:0;border-top:1px solid #efd56f;margin:0.75rem 0;'>"
                    estimate_html += "<b>추정 해석</b>"
                    estimate_html += "<ul>" + "".join(f"<li>{item}</li>" for item in estimates) + "</ul>"
                else:
                    estimate_html = ""

                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="small-label">{match['type']}</div>
                        <div class="phrase">{match['phrase']}</div>
                        <div><b>등록된 뜻</b></div>
                        <div>{meaning_html}</div>
                        <div>{estimate_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
with st.expander("등록된 피카츄어 사전 보기"):
    for pika, meanings in PICA_DICT.items():
        st.write(f"**{pika}** → {', '.join(meanings)}")
