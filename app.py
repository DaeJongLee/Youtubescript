import streamlit as st
import re
import textwrap
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    parsed_url = urlparse(url)
    if "youtube.com" in parsed_url.netloc:
        query = parse_qs(parsed_url.query)
        return query.get("v", [None])[0]
    elif "youtu.be" in parsed_url.netloc:
        return parsed_url.path.strip("/")
    return None

def get_transcript(video_id):
    """유튜브 자막 가져오기 (한국어 우선, 그다음 영어)"""
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        print("[디버그] 사용 가능한 자막 목록:")
        for t in transcripts:
            print(f" - {t.language_code} | {t.language} | {'자동 생성' if t.is_generated else '사용자 제공'}")
        
        transcript = transcripts.find_transcript(['ko', 'en'])
        print(f"[디버그] 선택된 자막 언어: {transcript.language_code}")
        text = '\n'.join([entry.text for entry in transcript.fetch()])
        return text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"[디버그] 자막 없음 오류: {e}")
        return None

def structure_transcript(raw_text):
    """텍스트를 의미 단위로 나누고, 요약 제목과 키워드 기반 헤드라인 생성"""
    import nltk
    nltk.download('punkt', quiet=True)
    from nltk.tokenize import sent_tokenize
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    # 문장 나누기
    sentences = sent_tokenize(raw_text)
    chunk_size = 4
    chunks = [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]

    structured = ""
    for i, chunk in enumerate(chunks, 1):
        paragraph = ' '.join(chunk)

        # 키워드 추출용 TF-IDF
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            X = vectorizer.fit_transform([paragraph])
            indices = np.argsort(X.toarray()[0])[::-1]
            features = vectorizer.get_feature_names_out()
            top_keywords = [features[j] for j in indices[:3] if j < len(features)]
            keyword_str = ", ".join(top_keywords)
        except:
            keyword_str = "내용 요약"

        headline = f"🔹 섹션 {i} - 핵심어: {keyword_str}"
        structured += f"{headline}\n{paragraph.strip()}\n\n"

    return structured.strip()

def to_formal_writing(text):
    """구어체를 문서체로 변환 (예시 수준 변환)"""
    conversions = {
        "그니까": "따라서",
        "근데": "하지만",
        "그래서": "그러므로",
        "어쨌든": "결론적으로",
        "뭔가": "어떤",
        "진짜": "정말",
        "되게": "매우",
        "약간": "조금",
        "좀": "조금",
        "이거": "이것은",
        "저거": "저것은"
    }
    for informal, formal in conversions.items():
        text = text.replace(informal, formal)
    return text

def main():
    st.title("🎬 유튜브 자막 추출기")
    url = st.text_input("유튜브 URL을 입력하세요")

    if url:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("유효한 유튜브 URL이 아닙니다.")
            return

        transcript = get_transcript(video_id)
        if transcript:
            structured = structure_transcript(transcript)
            formal = to_formal_writing(structured)

            st.text_area("📜 원본 스크립트", transcript, height=200)
            st.text_area("🧾 구조화된 자막", structured, height=300)
            st.text_area("📝 문서화된 자막", formal, height=300)
            
        else:
            st.warning("❌ 스크립트를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()