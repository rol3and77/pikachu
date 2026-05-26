import base64
import json
import random
from difflib import SequenceMatcher

import requests
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
    "피카피카": [
        "꼬부기", "파이리", "라프라스", "코코리", "갸라도스", "아공이",
        "가재군", "이어롤", "핑복", "수댕이", "맘모꾸리", "터검니", "화살꼬빈"
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
    text = str(text)
    text = text.replace("！", "!").replace("？", "?").replace("，", ",")
    return " ".join(text.split()).strip()


def clean_korean(text: str) -> str:
    text = normalize_text(text)
    for char in ["!", "?", ".", "~", ",", "'", '"']:
        text = text.replace(char, "")
    return " ".join(text.split()).strip()


def normalize_meaning_key(text: str) -> str:
    return clean_korean(text).replace(" ", "").strip()


def github_config_ready() -> bool:
    required_keys = [
        "github_token",
        "github_repo",
        "github_branch",
        "github_json_path",
    ]
    return all(key in st.secrets for key in required_keys)


def get_github_headers() -> dict:
    return {
        "Authorization": f"Bearer {st.secrets['github_token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_github_file_url() -> str:
    repo = st.secrets["github_repo"]
    path = st.secrets["github_json_path"]
    return f"https://api.github.com/repos/{repo}/contents/{path}"


def clean_custom_dict(data: dict) -> dict[str, list[str]]:
    cleaned = {}

    if not isinstance(data, dict):
        return cleaned

    for pika, meanings in data.items():
        pika = normalize_text(str(pika))

        if isinstance(meanings, str):
            meanings = [meanings]

        if not isinstance(meanings, list):
            continue

        cleaned[pika] = []

        for meaning in meanings:
            meaning = normalize_text(str(meaning))
            if meaning and meaning not in cleaned[pika]:
                cleaned[pika].append(meaning)

        if not cleaned[pika]:
            del cleaned[pika]

    return cleaned


def load_custom_dict_from_github() -> dict[str, list[str]]:
    if not github_config_ready():
        return {}

    try:
        response = requests.get(
            get_github_file_url(),
            headers=get_github_headers(),
            params={"ref": st.secrets["github_branch"]},
            timeout=10,
        )

        if response.status_code != 200:
            return {}

        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        parsed = json.loads(content)

        return clean_custom_dict(parsed)

    except Exception:
        return {}


def save_custom_dict_to_github(custom_dict: dict[str, list[str]]) -> tuple[bool, str]:
    if not github_config_ready():
        return False, "GitHub Secrets 설정이 없습니다."

    try:
        file_url = get_github_file_url()
        headers = get_github_headers()
        branch = st.secrets["github_branch"]

        get_response = requests.get(
            file_url,
            headers=headers,
            params={"ref": branch},
            timeout=10,
        )

        sha = None
        if get_response.status_code == 200:
            sha = get_response.json().get("sha")

        json_text = json.dumps(
            custom_dict,
            ensure_ascii=False,
            indent=2,
        )

        encoded_content = base64.b64encode(
            json_text.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": "Update custom Pikachu dictionary",
            "content": encoded_content,
            "branch": branch,
        }

        if sha:
            payload["sha"] = sha

        put_response = requests.put(
            file_url,
            headers=headers,
            json=payload,
            timeout=10,
        )

        if put_response.status_code in [200, 201]:
            return True, "GitHub에 저장 완료"

        return False, f"GitHub 저장 실패: {put_response.status_code}"

    except Exception as error:
        return False, str(error)


if "custom_pica_dict" not in st.session_state:
    st.session_state.custom_pica_dict = load_custom_dict_from_github()

if "translation_result" not in st.session_state:
    st.session_state.translation_result = None

if "example_text" not in st.session_state:
    st.session_state.example_text = ""

if "show_all_results" not in st.session_state:
    st.session_state.show_all_results = False


def get_current_dict() -> dict[str, list[str]]:
    merged = {key: value[:] for key, value in PICA_DICT.items()}

    for key, value in st.session_state.custom_pica_dict.items():
        if key in merged:
            for meaning in value:
                if meaning not in merged[key]:
                    merged[key].append(meaning)
        else:
            merged[key] = value[:]

    return merged


def get_aliases(meaning: str) -> list[str]:
    aliases = [meaning, clean_korean(meaning), normalize_meaning_key(meaning)]

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


def get_current_reverse_dict() -> dict[str, list[str]]:
    reverse = {}
    current = get_current_dict()

    for pika, meanings in current.items():
        for meaning in meanings:
            for alias in get_aliases(meaning):
                keys = {
                    alias,
                    clean_korean(alias),
                    normalize_meaning_key(alias),
                }

                for key in keys:
                    if not key:
                        continue

                    reverse.setdefault(key, [])

                    if pika not in reverse[key]:
                        reverse[key].append(pika)

    return reverse


def make_match(
    phrase: str,
    meanings: list[str],
    match_type: str,
    estimates: list[str] | None = None,
    reasons: list[str] | None = None,
) -> dict:
    return {
        "phrase": phrase,
        "meanings": meanings,
        "type": match_type,
        "estimates": estimates or [],
        "reasons": reasons or [],
    }


def meaning_usage_hint(meaning: str) -> str:
    text = str(meaning)

    if any(token in text for token in ["안녕", "인사"]):
        return "인사하거나 처음 만났을 때"
    if any(token in text for token in ["작별", "잘가"]):
        return "헤어질 때"
    if any(token in text for token in ["미안", "사과"]):
        return "사과할 때"
    if any(token in text for token in ["괜찮아", "확인"]):
        return "상대 상태를 확인할 때"
    if any(token in text for token in ["응", "알았어", "맞아", "긍정"]):
        return "동의하거나 대답할 때"
    if any(token in text for token in ["아니", "싫어", "거절", "부정"]):
        return "거절하거나 부정할 때"
    if any(token in text for token in ["뭐라고", "질문", "?"]):
        return "되묻거나 질문할 때"

    if any(token in text for token in ["10만볼트", "번개", "아이언테일", "볼트태클", "일렉트릭", "스파킹", "울트라", "기술", "전투"]):
        return "전투 중 기술을 쓰거나 공격할 때"

    if any(token in text for token in ["기분 좋", "신난", "행복", "기쁨"]):
        return "기분이 좋거나 신날 때"
    if any(token in text for token in ["피곤", "지친", "힘든", "우울", "슬픔"]):
        return "피곤하거나 감정이 처졌을 때"
    if any(token in text for token in ["과제", "시험", "수업", "학교", "학점", "팀플"]):
        return "학교생활이나 대학생 상황에서"
    if any(token in text for token in ["종강", "방학", "해방", "탈출"]):
        return "끝나길 바라거나 해방감을 표현할 때"

    people = [
        "한지우", "사토시", "최이슬", "웅이", "봄이",
        "나빛나", "세레나", "시트론", "로켓단", "로사", "로이", "나옹"
    ]
    if any(person in text for person in people):
        return "특정 인물을 부를 때"

    pokemon = [
        "토게피", "이상해씨", "꼬부기", "파이리", "라프라스", "코코리",
        "갸라도스", "아공이", "가재군", "이어롤", "핑복", "수댕이",
        "맘모꾸리", "터검니", "화살꼬빈", "리자몽", "치코리타",
        "잉어킹", "찌르호크", "브케인", "고라파덕", "야나프",
        "버터플", "푸호꼬", "팽도리", "코코"
    ]
    if any(name in text for name in pokemon):
        return "특정 포켓몬을 부를 때"

    if "등록된 표현 없음" in text or "등록된 뜻 없음" in text:
        return "아직 사전에 정확히 등록되지 않은 표현"

    return "문맥에 따라 사용"


def detect_language(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return "unknown"

    current_dict = get_current_dict()
    if text in current_dict:
        return "pika"

    compact = text.replace(" ", "")
    hangul_chars = [ch for ch in compact if "가" <= ch <= "힣"]

    if not hangul_chars:
        return "unknown"

    pika_syllables = {"피", "카", "츄", "챠", "핏", "캇"}
    pika_like_count = sum(1 for ch in hangul_chars if ch in pika_syllables)
    pika_ratio = pika_like_count / max(len(hangul_chars), 1)

    pika_keywords = ["피카", "피캇", "피이카", "피피", "피핏", "핏카", "츄", "챠아"]

    korean_intent_keywords = [
        "하고", "싶", "원해", "바라", "됐으면", "해야", "해야되", "하기",
        "하고싶", "가고싶", "먹고싶", "자고싶", "나", "너", "우리", "내",
        "오늘", "내일", "어제", "지금", "진짜", "너무", "개", "겁나", "완전", "좀",

        "종강", "개강", "학교", "대학", "대학교", "수업", "강의", "교수", "조교",
        "출석", "결석", "지각", "과제", "레포트", "보고서", "발표", "팀플",
        "조별", "조모임", "실험", "실습", "퀴즈", "시험", "중간", "기말",
        "학점", "성적", "재수강", "드랍", "휴강", "보강", "공강", "시간표",
        "수강신청", "전공", "교양", "도서관", "열람실", "기숙사", "자취",
        "통학", "캠퍼스", "학식", "학생회관", "동아리", "졸업", "취업",
        "인턴", "스펙", "자소서", "면접", "알바", "장학금", "등록금",

        "피곤", "힘들", "지침", "지쳐", "졸려", "졸림", "잠와", "잠오",
        "배고", "배불", "아파", "아픔", "우울", "슬퍼", "울고", "외로",
        "공허", "불안", "걱정", "무서", "떨려", "긴장", "멘붕", "현타",
        "짜증", "화나", "빡", "열받", "킹받", "싫", "극혐", "별로",
        "귀찮", "하기싫", "노답", "망했", "망함", "좋아", "좋다", "신나",
        "행복", "기뻐", "최고", "개꿀", "꿀", "드디어", "재밌", "웃겨",
        "설레", "감동", "괜찮", "괜찬", "문제없", "오케이", "ㅇㅋ",
        "응", "맞아", "알았", "그래", "아니", "몰라",

        "집", "가기", "가고", "가자", "먹", "밥", "술", "커피", "카페",
        "편의점", "치킨", "라면", "마라탕", "떡볶이", "자고", "잠",
        "쉬고", "쉬자", "놀고", "놀자", "게임", "유튜브", "넷플",
        "노래방", "피시방", "공부", "암기", "복습", "예습", "벼락치기",
        "밤샘", "새벽", "운동", "약속", "데이트", "친구",

        "왜", "뭐", "무슨", "어떻게", "언제", "어디", "누구", "몇", "얼마",
        "가능", "될까", "맞나", "끝", "끝나", "끝났", "마무리",
        "탈출", "방학", "쉬고싶", "자유", "해방", "살려", "도망",
    ]

    has_pika_keyword = any(keyword in compact for keyword in pika_keywords)
    has_korean_intent = any(keyword in compact for keyword in korean_intent_keywords)

    if has_korean_intent:
        return "korean"

    if has_pika_keyword and pika_ratio >= 0.45:
        return "pika"

    if pika_ratio >= 0.70:
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
    ex = clean.count("!")
    q = clean.count("?")
    dash = clean.count("-")
    wave = clean.count("~")
    length = len(clean)

    if q >= 1:
        add_score(scores, "질문 또는 되묻는 표현", 45, "물음표가 포함되어 있어 질문형 표현 가능성이 큽니다.")
        if wave >= 1:
            add_score(scores, "부드럽게 확인하는 표현", 30, "물음표와 물결표가 함께 있어 부드럽게 되묻는 느낌이 강합니다.")
        if dash >= 1:
            add_score(scores, "조심스럽게 확인하는 표현", 25, "물음표와 하이픈이 함께 있어 조심스럽게 확인하는 말투로 볼 수 있습니다.")

    if long_u >= 3 or "츄우" in clean:
        add_score(scores, "전기 기술 또는 공격 표현", 50, "'우'가 길게 반복되거나 '츄우'가 들어가 에너지를 방출하는 기술 표현처럼 보입니다.")
    if ex >= 2:
        add_score(scores, "강한 외침 또는 전투 표현", 35, "느낌표가 여러 개라 감정이 강하거나 전투 중 외침처럼 보입니다.")
    if length >= 12 and ex >= 1:
        add_score(scores, "기술명 계열 표현", 35, "표현이 길고 느낌표가 있어 일반 대화보다 기술명에 가깝습니다.")
    if pika >= 4:
        add_score(scores, "고조된 기술명 계열 표현", 40, "'피카'가 여러 번 반복되어 리듬이 있는 기술명 패턴에 가깝습니다.")

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

    if similar and similar[0]["score"] >= 0.84:
        best = similar[0]
        estimates.append(best["meaning"])
        reasons.append(
            f'등록 표현 "{best["candidate"]}"와 거의 같은 형태입니다. '
            f'등록 뜻은 "{best["meaning"]}"이고 유사도는 {best["score"]:.2f}입니다.'
        )
        estimates += pattern_estimates[:2]
        reasons += pattern_reasons
    else:
        estimates += pattern_estimates
        reasons += pattern_reasons

        if similar:
            best = similar[0]
            estimates.append(f'{best["meaning"]} 계열 가능성')
            reasons.append(
                f'참고로 가장 가까운 등록 표현은 "{best["candidate"]}"입니다. '
                f'등록 뜻은 "{best["meaning"]}"이고 유사도는 {best["score"]:.2f}입니다. '
                f'다만 완전 일치가 아니므로 보조 근거로만 사용했습니다.'
            )

    for item in similar[1:3]:
        reasons.append(
            f'추가 비교 후보: "{item["candidate"]}" → "{item["meaning"]}" / 유사도 {item["score"]:.2f}'
        )

    estimates = list(dict.fromkeys(estimates))
    reasons = list(dict.fromkeys(reasons))
    return estimates, reasons


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


def add_intent_score(scores: dict, intent: str, pika: str, points: int, reason: str):
    if intent not in scores:
        scores[intent] = {"score": 0, "pika": pika, "reasons": []}
    scores[intent]["score"] += points
    scores[intent]["reasons"].append(reason)


def expression_length_level(text: str) -> str:
    compact = clean_korean(text).replace(" ", "")
    if len(compact) <= 3:
        return "short"
    if len(compact) <= 8:
        return "medium"
    return "long"


def pick_pika_expression(intent: str, text: str) -> str:
    level = expression_length_level(text)
    compact = clean_korean(text).replace(" ", "")

    intense = any(token in compact for token in ["진짜", "너무", "개", "완전", "제발", "살려", "미친", "ㅈㄴ", "겁나"])

    table = {
        "positive": {
            "short": ["피카!"],
            "medium": ["챠아~!"],
            "long": ["피카카~ 피카츄~!"],
        },
        "negative": {
            "short": ["츄-"],
            "medium": ["피-카..."],
            "long": ["피-카... 츄우..."],
        },
        "tired": {
            "short": ["핏..."],
            "medium": ["피-카츄..."],
            "long": ["피-카... 츄우..."],
        },
        "wish": {
            "short": ["피카~"],
            "medium": ["피카아~ 츄..."],
            "long": ["피카아~ 츄우..."],
        },
        "escape": {
            "short": ["츄우..."],
            "medium": ["피카아... 츄우우..."],
            "long": ["피이카아... 츄우우우..."],
        },
        "question": {
            "short": ["피카?"],
            "medium": ["피~카~?"],
            "long": ["피~카~츄~?"],
        },
        "sorry": {
            "short": ["피-"],
            "medium": ["피-카츄"],
            "long": ["피-카... 츄..."],
        },
        "yes": {
            "short": ["피!"],
            "medium": ["피카!"],
            "long": ["피카! 피카츄!"],
        },
        "battle": {
            "short": ["핏카!"],
            "medium": ["피이카-피카!"],
            "long": ["피이카아!! 츄우우!!"],
        },
        "food": {
            "short": ["피카?"],
            "medium": ["피카츄~ 피카!"],
            "long": ["피카피카~ 츄우~ 피카!"],
        },
        "school": {
            "short": ["피카..."],
            "medium": ["피카아... 피-카츄..."],
            "long": ["피카아... 피-카츄... 츄우..."],
        },
        "default": {
            "short": ["피카?"],
            "medium": ["핏카츄~"],
            "long": ["핏카츄~ 피카!"],
        },
    }

    result = table.get(intent, table["default"])[level][0]

    if intense and level != "short":
        if "!" in result:
            result = result.replace("!", "!!", 1)
        elif "..." in result:
            result = result.replace("...", "......", 1)
        else:
            result += "!"

    return result


def estimate_korean_to_pika(text: str) -> tuple[list[str], list[str]]:
    original = normalize_text(text)
    compact = clean_korean(text).replace(" ", "")
    scores = {}

    def has_any(words: list[str]) -> bool:
        return any(word in compact for word in words)

    def add(intent_name: str, intent_key: str, points: int, reason: str):
        pika = pick_pika_expression(intent_key, text)
        add_intent_score(scores, intent_name, pika, points, reason)

    if has_any(["종강", "방학", "휴강", "공강", "시험끝", "과제끝", "끝났", "끝나"]):
        add("종강이나 해방을 바라는 표현", "escape", 60, "종강, 방학, 끝남 계열 단어가 있어 해방감이나 간절함으로 판단했습니다.")
    if has_any(["과제", "레포트", "보고서", "발표", "팀플", "조별", "시험", "중간", "기말", "퀴즈", "학점", "재수강"]):
        add("학교 스트레스 표현", "school", 50, "과제, 시험, 팀플, 학점 등 대학 생활 스트레스 단어가 포함되어 있습니다.")
    if has_any(["수업", "강의", "교수", "조교", "출석", "지각", "결석", "수강신청"]):
        add("학교 상황 표현", "school", 35, "수업, 강의, 교수님 등 학교 상황 단어가 있어 일반 학교 관련 표현으로 판단했습니다.")
    if has_any(["하고싶", "싶다", "원해", "됐으면", "바라", "제발", "가고싶", "먹고싶", "자고싶"]):
        add("바람이나 소망 표현", "wish", 35, "하고 싶다, 원하다, 제발 같은 소망 표현이 있습니다.")
    if has_any(["살려", "탈출", "도망", "해방", "집가", "집에가", "퇴근", "하교"]):
        add("탈출하고 싶은 표현", "escape", 60, "살려, 탈출, 집에 가고 싶다 계열 표현이 있어 강한 탈출 욕구로 판단했습니다.")
    if has_any(["피곤", "힘들", "지침", "지쳐", "졸려", "졸림", "잠와", "잠오", "밤샘", "새벽", "무기력"]):
        add("피곤하거나 지친 표현", "tired", 60, "피곤함, 졸림, 밤샘, 지침 계열 단어가 있어 축 처진 감정으로 판단했습니다.")
    if has_any(["현타", "멘붕", "망했", "망함", "노답", "조졌다", "망"]):
        add("멘붕 또는 망했다는 표현", "negative", 55, "현타, 멘붕, 망함 계열 단어가 있어 절망이나 당황 감정으로 판단했습니다.")
    if has_any(["좋아", "좋다", "신나", "행복", "기뻐", "최고", "개꿀", "꿀", "드디어", "재밌", "설레", "감동"]):
        add("기쁨 또는 신남 표현", "positive", 60, "좋다, 신난다, 행복하다, 개꿀 등 긍정 감정 단어가 있습니다.")
    if has_any(["짜증", "화나", "빡", "열받", "킹받", "극혐", "싫어", "싫다", "별로", "귀찮", "하기싫", "가기싫"]):
        add("짜증 또는 거절 표현", "negative", 65, "짜증, 화남, 싫음, 귀찮음 계열 단어가 있어 부정 표현으로 판단했습니다.")
    if has_any(["슬퍼", "우울", "울고", "외로", "공허", "불안", "걱정", "무서"]):
        add("슬픔 또는 불안 표현", "tired", 55, "슬픔, 불안, 외로움 계열 단어가 있어 처진 감정 표현으로 판단했습니다.")
    if has_any(["억울", "어이없", "황당", "말도안", "에바", "개에바"]):
        add("황당하거나 어이없는 표현", "question", 55, "어이없다, 황당하다, 에바 같은 표현이 있어 되묻는 말투로 판단했습니다.")

    if has_any(["안녕", "하이", "반가", "ㅎㅇ", "헬로"]):
        add_intent_score(scores, "인사 표현", "피캇츄~!", 80, "인사 표현은 등록 표현 피캇츄~!와 직접 연결됩니다.")
    if has_any(["잘가", "바이", "빠이", "작별", "나중에", "낼봐", "내일보자"]):
        add_intent_score(scores, "작별 표현", "피카-피카!", 80, "작별 표현은 등록 표현 피카-피카!와 직접 연결됩니다.")
    if has_any(["미안", "죄송", "사과"]):
        add("사과 표현", "sorry", 80, "사과 표현을 조심스럽게 말하는 피카츄어로 변환했습니다.")
    if has_any(["괜찮", "괜찬", "문제없", "괜츈"]):
        add_intent_score(scores, "괜찮은지 확인하는 표현", "피-카-츄~?", 75, "괜찮다 계열 표현은 등록 표현 피-카-츄~?와 연결됩니다.")
    if has_any(["응", "맞아", "알았", "그래", "오케이", "ㅇㅋ", "ㅇㅇ"]):
        add("긍정 또는 동의 표현", "yes", 75, "응, 맞아, 알았어 계열 표현을 짧은 긍정 피카츄어로 변환했습니다.")
    if has_any(["아니", "ㄴㄴ", "노노", "싫어"]):
        add_intent_score(scores, "부정 또는 거절 표현", "츄-", 75, "아니, 싫어 계열 표현은 등록 표현 츄-와 연결됩니다.")

    if "?" in original or has_any(["왜", "뭐", "무슨", "어떻게", "언제", "어디", "누구", "몇", "얼마", "될까", "가능", "맞나"]):
        add("질문 또는 되묻는 표현", "question", 60, "질문어 또는 물음표가 있어 되묻는 표현으로 판단했습니다.")

    if has_any(["배고", "밥먹", "먹고싶", "마라탕", "떡볶이", "치킨", "라면", "학식"]):
        add("배고픔 또는 먹고 싶은 표현", "food", 50, "배고픔이나 음식 욕구가 있어 밝은 요구 표현으로 변환했습니다.")
    if has_any(["술", "맥주", "소주", "취하고", "마시고싶"]):
        add("놀고 싶거나 해방되고 싶은 표현", "positive", 45, "술, 마시고 싶다 계열 표현이 있어 해방감이나 놀고 싶은 감정으로 판단했습니다.")
    if has_any(["커피", "카페", "아아", "아메리카노", "카페인"]):
        add("카페인이 필요한 표현", "tired", 45, "커피와 카페인 단어가 있어 피곤하지만 버티려는 표현으로 변환했습니다.")
    if has_any(["자고", "잠", "쉬고", "쉬자", "눕고", "침대"]):
        add("쉬고 싶거나 자고 싶은 표현", "tired", 55, "잠, 쉬고 싶다, 눕고 싶다 계열 단어가 있어 피곤한 표현으로 판단했습니다.")
    if has_any(["가자", "해보자", "이기", "화이팅", "파이팅", "불태우", "전투", "공격", "시작"]):
        add("전투 준비 또는 의지 표현", "battle", 60, "가자, 해보자, 파이팅 계열 단어가 있어 전투 준비 표현으로 바꿨습니다.")

    if not scores:
        default_pika = pick_pika_expression("default", text)
        return [default_pika], ["명확한 감정 단어는 없지만 입력 길이에 맞춰 피카츄어 표현을 생성했습니다."]

    ranked = sorted(scores.items(), key=lambda item: item[1]["score"], reverse=True)
    top_score = ranked[0][1]["score"]

    selected = []
    for intent, data in ranked:
        if len(selected) >= 2:
            break
        if data["score"] >= top_score - 20:
            selected.append((intent, data))

    estimates = []
    reasons = []

    for intent, data in selected:
        if data["pika"] not in estimates:
            estimates.append(data["pika"])
        reasons.append(f"{intent}: {data['score']}점")
        for reason in data["reasons"][:2]:
            reasons.append("- " + reason)

    if len(estimates) >= 2:
        combined = " ".join(estimates)
        estimates.insert(0, combined)
        reasons.insert(0, "여러 감정이나 의도가 함께 감지되어 길이에 맞는 피카츄어 표현을 이어 붙였습니다.")

    return estimates, list(dict.fromkeys(reasons))


def find_pika_to_korean(text: str) -> list[dict]:
    text = normalize_text(text)
    current_dict = get_current_dict()

    if not text:
        return []

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
    raw_text = normalize_text(text)
    text = clean_korean(text)
    meaning_key = normalize_meaning_key(text)
    reverse_dict = get_current_reverse_dict()

    if not text:
        return []

    if meaning_key in reverse_dict:
        return [
            make_match(
                text,
                reverse_dict[meaning_key],
                "정확히 일치",
                ["등록된 한국어 뜻과 정확히 일치"],
                [f'한국어 뜻 "{raw_text}"가 사전에 등록되어 있어 기존 피카츄어 표현을 우선 사용했습니다.'],
            )
        ]

    matches = []
    used = set()

    for word in [part.strip() for part in text.split() if part.strip()]:
        word_key = normalize_meaning_key(word)

        if word_key in reverse_dict:
            matches.append(
                make_match(
                    word,
                    reverse_dict[word_key],
                    "정확히 일치",
                    ["등록된 한국어 뜻과 정확히 일치"],
                    [f'한국어 뜻 "{word}"가 사전에 등록되어 있어 기존 피카츄어 표현을 우선 사용했습니다.'],
                )
            )
            used.add(word_key)

    for key in sorted(reverse_dict.keys(), key=len, reverse=True):
        cleaned_key = normalize_meaning_key(key)

        if cleaned_key and cleaned_key not in used and cleaned_key in meaning_key:
            matches.append(
                make_match(
                    key,
                    reverse_dict[key],
                    "부분 번역",
                    ["입력 문장 안에 등록된 뜻이 포함됨"],
                    [f'입력문 안에 등록된 한국어 뜻 "{key}"가 포함되어 있습니다.'],
                )
            )
            used.add(cleaned_key)

    if matches:
        return matches

    estimates, reasons = estimate_korean_to_pika(text)
    return [
        make_match(
            text,
            ["등록된 표현 없음"],
            "한국어 문장 추정",
            estimates,
            reasons,
        )
    ]


def match_quality(matches: list[dict]) -> int:
    if not matches:
        return 0

    score = 0

    for match in matches:
        match_type = match.get("type", "")
        meanings = match.get("meanings", [])
        estimates = match.get("estimates", [])

        if match_type in ["등록된 표현", "정확히 일치"]:
            score += 120
        elif match_type == "부분 번역":
            score += 80
        elif match_type == "한국어 문장 추정":
            score += 65
        elif match_type == "추정":
            score += 30

        if meanings and meanings[0] not in ["등록된 뜻 없음", "등록된 표현 없음"]:
            score += 25
        if estimates:
            score += 10

    return score


def translate_safely(text: str, auto_mode: bool, manual_mode: str) -> tuple[str, list[dict]]:
    if not text.strip():
        return resolve_mode(text, auto_mode, manual_mode), []

    if not auto_mode:
        mode = manual_mode
        matches = find_pika_to_korean(text) if mode == "피카츄어 → 한국어" else find_korean_to_pika(text)
        return mode, matches

    detected = detect_language(text)
    pika_matches = find_pika_to_korean(text)
    korean_matches = find_korean_to_pika(text)

    pika_score = match_quality(pika_matches)
    korean_score = match_quality(korean_matches)

    if detected == "korean":
        has_exact_pika = any(m.get("type") == "등록된 표현" for m in pika_matches)
        if has_exact_pika and pika_score >= korean_score + 40:
            return "피카츄어 → 한국어", pika_matches
        return "한국어 → 피카츄어", korean_matches

    if detected == "pika":
        has_exact_korean = any(m.get("type") == "정확히 일치" for m in korean_matches)
        if has_exact_korean and korean_score >= pika_score + 40:
            return "한국어 → 피카츄어", korean_matches
        return "피카츄어 → 한국어", pika_matches

    if korean_score >= pika_score:
        return "한국어 → 피카츄어", korean_matches

    return "피카츄어 → 한국어", pika_matches


def clean_learned_meaning(korean_meaning: str) -> str:
    meaning = normalize_text(korean_meaning)

    meaning = meaning.replace("계열일 가능성", "")
    meaning = meaning.replace("가능성이 큼", "")
    meaning = meaning.replace("가능성이 있습니다", "")
    meaning = meaning.replace("표현으로 해석할 수 있음", "표현")
    meaning = meaning.replace("또는", "/")
    meaning = meaning.replace("  ", " ").strip(" ,./")

    if any(token in meaning for token in ["전기 기술", "공격", "에너지"]):
        return "전기 기술 표현"
    if any(token in meaning for token in ["질문", "되묻", "의문"]):
        return "되묻는 말"
    if "확인" in meaning:
        return "확인하는 말"
    if any(token in meaning for token in ["기분 좋은", "부드럽", "감정", "기쁨", "신남"]):
        return "기분 좋은 감정 표현"
    if any(token in meaning for token in ["강한 외침", "전투", "기술명"]):
        return "전투 중 외침"
    if any(token in meaning for token in ["망설임", "조심", "미안"]):
        return "조심스러운 감정 표현"
    if any(token in meaning for token in ["짧은 호칭", "호칭", "대상 지칭", "이름"]):
        return "대상을 부르는 말"
    if any(token in meaning for token in ["부정", "거절", "싫"]):
        return "싫거나 거절하는 말"
    if any(token in meaning for token in ["긍정", "대답", "응답"]):
        return "긍정하는 말"

    if len(meaning) > 18:
        return "새로운 피카츄어 표현"

    return meaning if meaning else "새로운 피카츄어 표현"


def learn_generated_translation(korean_text: str, pika_text: str) -> bool:
    pika_text = normalize_text(pika_text)
    korean_text = normalize_text(korean_text)

    if not pika_text or not korean_text:
        return False

    current_dict = get_current_dict()
    if pika_text in current_dict:
        return False

    custom = st.session_state.get("custom_pica_dict", {})
    custom.setdefault(pika_text, [])

    if korean_text not in custom[pika_text]:
        custom[pika_text].append(korean_text)
        st.session_state.custom_pica_dict = custom
        return True

    st.session_state.custom_pica_dict = custom
    return False


def is_new_pika_expression(user_input: str, matches: list[dict]) -> bool:
    text = normalize_text(user_input)
    current_dict = get_current_dict()

    if not text or text in current_dict:
        return False

    if not matches:
        return False

    return any(match.get("type") == "추정" for match in matches)


def register_selected_pika_meaning(pika_text: str, selected_meaning: str) -> tuple[bool, str]:
    pika_text = normalize_text(pika_text)
    selected_meaning = clean_learned_meaning(selected_meaning)

    if not pika_text or not selected_meaning:
        return False, "등록할 피카츄어와 뜻이 비어 있습니다."

    current_dict = get_current_dict()
    if pika_text in current_dict:
        return False, "이미 사전에 등록된 피카츄어입니다."

    custom = st.session_state.get("custom_pica_dict", {})
    custom.setdefault(pika_text, [])

    if selected_meaning not in custom[pika_text]:
        custom[pika_text].append(selected_meaning)

    st.session_state.custom_pica_dict = custom

    saved, message = save_custom_dict_to_github(st.session_state.custom_pica_dict)

    if saved:
        return True, "선택한 해석으로 등록했고, GitHub에도 저장했습니다."

    return True, f"선택한 해석으로 임시 등록했습니다. GitHub 저장은 실패했습니다: {message}"


def representative_items(matches: list[dict]) -> list[dict]:
    items = []

    bad_items = {
        "등록된 한국어 뜻과 정확히 일치",
        "입력 문장 안에 등록된 뜻이 포함됨",
        "새로운 피카츄어 표현",
        "등록된 표현 없음",
        "등록된 뜻 없음",
    }

    for match in matches:
        meanings = match.get("meanings", [])
        estimates = match.get("estimates", [])
        match_type = match.get("type", "")

        valid_meanings = [
            meaning for meaning in meanings
            if meaning not in ["등록된 뜻 없음", "등록된 표현 없음"]
        ]

        if valid_meanings:
            source_items = valid_meanings
            base_score = 100 if match_type in ["등록된 표현", "정확히 일치"] else 80
        else:
            source_items = estimates
            base_score = 60

        for index, item in enumerate(source_items):
            if not item:
                continue
            if item in bad_items:
                continue
            if "계열 가능성" in item:
                continue

            items.append({
                "text": item,
                "usage": meaning_usage_hint(item),
                "score": base_score - index,
            })

    unique = []
    seen = set()

    for item in items:
        key = item["text"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    unique.sort(key=lambda x: x.get("score", 0), reverse=True)
    return unique


def representative_sentence(matches: list[dict], mode: str) -> str:
    items = representative_items(matches)

    if not items:
        return ""

    return "\n".join(item["text"] for item in items)


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

    meanings = match.get("meanings", [])
    valid_meanings = [
        meaning for meaning in meanings
        if meaning not in ["등록된 뜻 없음", "등록된 표현 없음"]
    ]

    if valid_meanings:
        st.write("등록된 뜻:")
        for meaning in valid_meanings:
            usage = meaning_usage_hint(meaning)
            st.markdown(f"- **{meaning}**  \n  사용 상황: {usage}")
    else:
        st.write("등록된 뜻:", ", ".join(meanings))

    if match.get("estimates"):
        st.write("추정 해석:")
        for estimate in match["estimates"]:
            if estimate in ["새로운 피카츄어 표현"] or "계열 가능성" in estimate:
                continue
            usage = meaning_usage_hint(estimate)
            st.markdown(f"- **{estimate}**  \n  사용 상황: {usage}")

    if match.get("reasons"):
        with st.expander("왜 그렇게 추정했는지 보기", expanded=False):
            for reason in match["reasons"]:
                st.write("-", reason)


st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, #fff2a8 0, transparent 35%),
            radial-gradient(circle at bottom right, #ffe066 0, transparent 30%),
            #fff8d6;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -0.06em;
        color: #5c3b18;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        color: #75684f;
        font-size: 1.05rem;
        line-height: 1.7;
        margin-bottom: 1.2rem;
    }
    .result-panel {
        min-height: 120px;
        background: #fffdf3;
        border: 2px dashed #ead17d;
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .sentence-card {
        background: #ffffff;
        border: 2px solid #ffd43b;
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 8px 18px rgba(242,183,5,0.14);
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">⚡ 피카츄어 번역기</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">입력한 언어를 자동 감지해서 번역합니다. 등록된 표현은 등록 뜻을 우선하고, 등록되지 않은 표현은 패턴과 감정을 바탕으로 추정합니다.</div>',
    unsafe_allow_html=True,
)

if not github_config_ready():
    st.info("GitHub 자동 저장 설정이 없으면 새 표현은 현재 세션에만 저장됩니다. 아래 백업 기능으로 JSON을 저장할 수 있습니다.")

auto_mode = st.toggle("언어 자동 감지", value=True)

manual_mode = "피카츄어 → 한국어"
if not auto_mode:
    manual_mode = st.radio(
        "번역 방향",
        ["피카츄어 → 한국어", "한국어 → 피카츄어"],
        horizontal=True,
    )

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("번역할 언어 입력")

    user_input = st.text_area(
        "입력",
        value=st.session_state.example_text,
        height=260,
        placeholder="예: 피캇츄~! 피카피 피카! 또는 종강하고싶다",
        label_visibility="collapsed",
    )

    translate_clicked = st.button("번역하기", type="primary", use_container_width=True)

    if translate_clicked:
        st.session_state.show_all_results = False

        if not user_input.strip():
            st.session_state.translation_result = {
                "status": "empty",
                "message": "번역할 문장을 입력해주세요.",
            }
        else:
            mode, matches = translate_safely(user_input, auto_mode, manual_mode)
            sentence = representative_sentence(matches, mode)

            learned = False

            if mode == "한국어 → 피카츄어" and sentence:
                current_dict = get_current_dict()
                if sentence not in current_dict:
                    learned = learn_generated_translation(user_input, sentence)

            if learned:
                save_custom_dict_to_github(st.session_state.custom_pica_dict)

            st.session_state.translation_result = {
                "status": "ok",
                "mode": mode,
                "sentence": sentence,
                "matches": matches,
                "learned": learned,
            }

    if st.button("랜덤 예문 넣기", use_container_width=True):
        st.session_state.example_text = random.choice([
            "피캇츄~! 피카피 피카!",
            "피이카-피카! 피이카츄우우우우우",
            "피~카~?",
            "종강하고싶다",
            "과제하기싫고 집가고싶다",
            "전투 준비 완료 10만볼트",
        ])
        st.session_state.translation_result = None
        st.session_state.show_all_results = False
        st.rerun()


with right:
    st.subheader("해석 결과")
    saved = st.session_state.translation_result

    if saved is None:
        st.markdown(
            '<div class="result-panel">왼쪽 입력칸에 문장을 입력하고 번역하기 버튼을 눌러주세요.</div>',
            unsafe_allow_html=True,
        )

    elif saved.get("status") == "empty":
        st.markdown(
            f'<div class="result-panel">{saved.get("message", "번역할 문장을 입력해주세요.")}</div>',
            unsafe_allow_html=True,
        )

    else:
        mode = saved.get("mode", "")
        matches = saved.get("matches", [])
        items = representative_items(matches)

        if saved.get("learned"):
            st.success("이번에 생성한 새 피카츄어 표현을 임시 사전에 학습했습니다.")

display_items = items if st.session_state.show_all_results else items[:3]

if display_items:
    item_html = ""
    for item in display_items:
        item_html += f"""
        <div class="result-item-box">
            <div class="result-main-text">{item["text"]}</div>
            <div class="result-usage-text">{item["usage"]}</div>
        </div>
        """
else:
    item_html = """
    <div class="result-item-box">
        <div class="result-main-text">해석 결과 없음</div>
        <div class="result-usage-text">입력 내용을 다시 확인해주세요.</div>
    </div>
    """

if len(items) > 3 and not st.session_state.show_all_results:
    more_notice = f"""
    <div class="more-notice">
        전체 {len(items)}개 중 점수가 높은 3개만 표시 중입니다.
    </div>
    """
elif len(items) > 3 and st.session_state.show_all_results:
    more_notice = f"""
    <div class="more-notice">
        전체 {len(items)}개 해석을 모두 표시 중입니다.
    </div>
    """
else:
    more_notice = ""

        st.markdown(
            f"""
            <div class="result-panel" style="position:relative;">
                <div style="position:absolute; top:0.75rem; right:1rem; color:#75684f; font-size:0.85rem; white-space:nowrap;">
                    {mode}
                </div>
        
                <div class="sentence-card" style="margin-top:1.6rem;">
                    <div class="small-label">대표 해석</div>
                    <div style="color:#75684f; font-size:0.9rem; margin-bottom:0.75rem;">
                        점수가 높은 해석부터 표시됩니다.
                    </div>
                    {item_html}
                    {more_notice}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        if len(items) > 3:
            if not st.session_state.show_all_results:
                if st.button("더보기", use_container_width=True):
                    st.session_state.show_all_results = True
                    st.rerun()
            else:
                if st.button("접기", use_container_width=True):
                    st.session_state.show_all_results = False
                    st.rerun()

        new_pika_can_register = False
        register_candidates = []
        register_pika_text = ""

        if mode == "피카츄어 → 한국어":
            raw_input = normalize_text(user_input)

            if raw_input and raw_input not in get_current_dict():
                for match in matches:
                    if match.get("type") == "추정":
                        for estimate in match.get("estimates", []):
                            cleaned = clean_learned_meaning(estimate)

                            if cleaned in ["새로운 피카츄어 표현"]:
                                continue

                            if cleaned and cleaned not in register_candidates:
                                register_candidates.append(cleaned)

                if register_candidates:
                    new_pika_can_register = True
                    register_pika_text = raw_input

        if new_pika_can_register:
            st.markdown("#### 새 표현으로 등록하기")
            st.caption("사전에 없는 새로운 피카츄어라면, 가장 알맞은 해석을 골라 등록할 수 있습니다.")

            selected_meaning = st.radio(
                "등록할 해석 선택",
                register_candidates,
                key=f"select_meaning_{register_pika_text}",
            )

            custom_meaning = st.text_input(
                "직접 수정해서 등록하기",
                value=selected_meaning,
                key=f"custom_meaning_{register_pika_text}",
            )

            if st.button("선택한 해석으로 등록", use_container_width=True, key=f"register_{register_pika_text}"):
                ok, message = register_selected_pika_meaning(register_pika_text, custom_meaning)

                if ok:
                    st.success(message)
                    st.session_state.translation_result = None
                    st.session_state.show_all_results = False
                    st.rerun()
                else:
                    st.warning(message)

        with st.expander("단어별 해석 보기", expanded=False):
            for match in matches:
                render_match_card(match)
                st.divider()


st.divider()

st.subheader("새 피카츄어 표현 등록")
st.caption("새 표현은 현재 사전에 추가됩니다. GitHub 설정이 되어 있으면 자동 저장됩니다.")

with st.form("add_new_expression", clear_on_submit=True):
    form_col1, form_col2 = st.columns([1, 1], gap="medium")

    with form_col1:
        new_pika = st.text_input("새 피카츄어", placeholder="예: 피카츄우웅!")

    with form_col2:
        new_meaning = st.text_input("뜻", placeholder="예: 신난 피카츄의 외침")

    submitted = st.form_submit_button("사전에 등록하기", use_container_width=True)

    if submitted:
        new_pika = normalize_text(new_pika)
        new_meaning = normalize_text(new_meaning)

        if not new_pika or not new_meaning:
            st.warning("피카츄어와 뜻을 모두 입력해주세요.")
        else:
            current_custom = st.session_state.custom_pica_dict
            current_custom.setdefault(new_pika, [])

            if new_meaning not in current_custom[new_pika]:
                current_custom[new_pika].append(new_meaning)

            st.session_state.custom_pica_dict = current_custom
            st.session_state.translation_result = None
            st.session_state.show_all_results = False

            saved, message = save_custom_dict_to_github(st.session_state.custom_pica_dict)

            if saved:
                st.success(f'"{new_pika}" → "{new_meaning}" 등록 완료. GitHub에 자동 저장됐습니다.')
            else:
                st.warning(f'"{new_pika}" → "{new_meaning}" 임시 등록 완료. GitHub 저장은 실패했습니다.')
                st.caption(message)


if st.session_state.custom_pica_dict:
    with st.expander("내가 새로 등록한 표현 보기 / 삭제", expanded=False):
        delete_target = None

        for index, (pika, meanings) in enumerate(list(st.session_state.custom_pica_dict.items())):
            row_left, row_right = st.columns([5, 1])

            with row_left:
                st.markdown(f"**{pika}**  →  {', '.join(meanings)}")

            with row_right:
                if st.button("삭제", key=f"delete_custom_{index}", use_container_width=True):
                    delete_target = pika

        if delete_target:
            del st.session_state.custom_pica_dict[delete_target]
            st.session_state.translation_result = None
            st.session_state.show_all_results = False

            saved, message = save_custom_dict_to_github(st.session_state.custom_pica_dict)

            if saved:
                st.success(f'"{delete_target}" 표현을 삭제했고, GitHub에도 반영했습니다.')
            else:
                st.warning(f'"{delete_target}" 표현은 현재 세션에서 삭제됐지만, GitHub 저장은 실패했습니다.')
                st.caption(message)

            st.rerun()
else:
    st.info("아직 새로 등록한 표현이 없습니다.")


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


st.divider()

with st.expander("백업 / 복원", expanded=False):
    st.caption("새로 등록한 표현을 JSON으로 저장하거나, 이전에 저장한 JSON을 다시 불러올 수 있습니다.")

    backup_col, restore_col = st.columns([1, 1], gap="large")

    with backup_col:
        st.markdown("#### 백업")

        if st.session_state.custom_pica_dict:
            custom_json = json.dumps(
                st.session_state.custom_pica_dict,
                ensure_ascii=False,
                indent=2,
            )

            st.download_button(
                label="JSON 다운로드",
                data=custom_json,
                file_name="custom_pikachu_dictionary.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.info("다운로드할 새 표현이 없습니다.")

    with restore_col:
        st.markdown("#### 복원")

        uploaded_json = st.file_uploader(
            "JSON 업로드",
            type=["json"],
            help="이전에 다운로드한 custom_pikachu_dictionary.json 파일을 업로드하세요.",
            label_visibility="collapsed",
        )

        if uploaded_json is not None:
            try:
                uploaded_data = json.load(uploaded_json)

                if not isinstance(uploaded_data, dict):
                    st.error('올바른 사전 JSON 형식이 아닙니다. {"피카츄어": ["뜻"]} 형태여야 합니다.')
                else:
                    restored_count = 0
                    custom = st.session_state.custom_pica_dict

                    for pika, meanings in uploaded_data.items():
                        pika = normalize_text(str(pika))

                        if isinstance(meanings, str):
                            meanings = [meanings]

                        if not isinstance(meanings, list):
                            continue

                        for meaning in meanings:
                            meaning = normalize_text(str(meaning))

                            if not pika or not meaning:
                                continue

                            custom.setdefault(pika, [])

                            if meaning not in custom[pika]:
                                custom[pika].append(meaning)
                                restored_count += 1

                    st.session_state.custom_pica_dict = custom
                    st.session_state.translation_result = None
                    st.session_state.show_all_results = False

                    if restored_count > 0:
                        saved, message = save_custom_dict_to_github(st.session_state.custom_pica_dict)

                        if saved:
                            st.success(f"JSON에서 새 표현 {restored_count}개를 복원했고, GitHub에도 저장했습니다.")
                        else:
                            st.warning(f"JSON에서 새 표현 {restored_count}개를 복원했습니다. GitHub 저장은 실패했습니다.")
                            st.caption(message)
                    else:
                        st.info("새로 추가할 표현이 없습니다. 이미 등록된 내용일 수 있습니다.")

            except Exception as error:
                st.error("JSON 파일을 읽는 중 오류가 발생했습니다.")
                st.caption(str(error))
