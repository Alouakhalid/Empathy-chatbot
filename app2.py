import streamlit as st
from langdetect import detect
import google.generativeai as genai
import json, uuid
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO
import edge_tts
import asyncio
import nest_asyncio
import speech_recognition as sr
import hashlib

nest_asyncio.apply()

API_KEY = "AIzaSyB_ei3R2CM7DRwYyZw3YkcPtTXhDe6vH14"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

CONVERSATIONS_FILE = "conversations.json"

def load_conversations():
    """تحميل المحادثات من ملف JSON"""
    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_conversations(conversations):
    """حفظ المحادثات في ملف JSON"""
    with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=4)

def detect_language(text):
    """تحديد اللغة (عربي أو إنجليزي)"""
    try:
        return "ar" if detect(text).startswith("ar") else "en"
    except:
        return "ar"

def get_image_hash(image):
    """توليد معرف فريد للصورة بناءً على محتواها"""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return hashlib.md5(buffered.getvalue()).hexdigest()

def analyze_image(image):
    """تحليل الصورة باستخدام Gemini API"""
    with st.spinner("جاري تحليل الصورة..."):
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        prompt = "حلل محتوى الصورة ورد بشكل ودي وطبيعي."
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_str}])
        return response.text.strip() if response.text else "حدث خطأ أثناء تحليل الصورة."

def generate_response(user_message, chat_id, conversations, image=None, image_hash=None):
    """توليد رد البوت مع مراعاة التاريخ"""
    history = conversations.get(chat_id, {"messages": []})["messages"]

    if image and image_hash:
        for msg in history[-2:]:
            if msg.get("role") == "user" and msg.get("input") == "📷 صورة مرفوعة" and msg.get("image_hash") == image_hash:
                return None  
    context = "\n".join([
        f"User: {m.get('input', 'غير متوفر')}\nBot: {m.get('output', 'غير متوفر')}"
        for m in history[-3:] if m.get('input') and m.get('output')
    ])

    with st.spinner("البوت بيفكر..."):
        if image:
            bot_reply = analyze_image(image)
        else:
            lang = detect_language(user_message) if user_message else "ar"
            prompt = (
                f"Language: {lang}\n"
                f"History:\n{context}\n"
                f"User: {user_message}\n"
                f"رد وتفهم المشاعر وتحللها كمان وترد على اساسها طبيعي وتعاطفي كأنك صديق مقرب."
            )
            response = model.generate_content(prompt)
            bot_reply = response.text.strip() if response.text else "حدث خطأ أثناء توليد الرد."

    history.append({
        "role": "user",
        "input": user_message if user_message else "📷 صورة مرفوعة",
        "timestamp": datetime.now().isoformat(),
        "image_hash": image_hash if image else None
    })
    history.append({
        "role": "assistant",
        "output": bot_reply,
        "timestamp": datetime.now().isoformat()
    })

    conversations[chat_id]["messages"] = history
    conversations[chat_id]["last_updated"] = datetime.now().isoformat()
    save_conversations(conversations)
    return bot_reply

async def text_to_speech(text, filename="output.mp3"):
    """تحويل النص إلى صوت باستخدام Edge TTS"""
    communicate = edge_tts.Communicate(text, voice="ar-EG-SalmaNeural")
    await communicate.save(filename)
    return filename

def play_tts(text):
    """تشغيل الصوت"""
    if not text:
        return
    filename = "output.mp3"
    asyncio.run(text_to_speech(text, filename))
    audio_file = open(filename, "rb").read()
    st.audio(audio_file, format="audio/mp3")

def speech_to_text():
    """التعرف على الصوت وتحويله إلى نص"""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.session_state.recording_status = "جاري التسجيل... (اضغط 'إيقاف التسجيل' للإنهاء)"
            st.info("🎤 اتكلم دلوقتي...")
            recognizer.adjust_for_ambient_noise(source, duration=1)  
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)
            with st.spinner("جاري معالجة الصوت..."):
                text = recognizer.recognize_google(audio, language="ar-EG")
            return text
    except sr.UnknownValueError:
        return "مافهمتش الصوت، جرب تتكلم بوضوح أكتر."
    except sr.RequestError as e:
        return f"في مشكلة في خدمة التعرف على الصوت، تأكد من الإنترنت: {str(e)}"
    except sr.WaitTimeoutError:
        return "ما سجلتش صوت، جرب تاني."
    except Exception as e:
        return f"حصل خطأ: {str(e)}. تأكد إن الميكروفون متوصل وشغال."

def start_recording():
    """بدء التسجيل"""
    if not st.session_state.get("is_recording", False):
        st.session_state.is_recording = True
        st.session_state.voice_text = None
        try:
            mic = sr.Microphone()
            mic.__enter__()  
            mic.__exit__(None, None, None)  
            st.session_state.voice_text = speech_to_text()
        except Exception as e:
            st.session_state.recording_status = f"فشل التسجيل: {str(e)}. تأكد إن الميكروفون متوصل."
            st.session_state.is_recording = False

def stop_recording(response_container, chat_id, conversations):
    """إيقاف التسجيل ومعالجة النص فورًا"""
    if st.session_state.get("is_recording", False):
        st.session_state.is_recording = False
        voice_text = st.session_state.get("voice_text", None)
        if voice_text and not voice_text.startswith(("مافهمتش", "في مشكلة", "حصل خطأ", "ما سجلتش")):
            st.session_state.recording_status = "تم التسجيل والمعالجة"
            with response_container.container():
                with st.chat_message("user", avatar="👤"):
                    st.markdown(voice_text)
            response = generate_response(voice_text, chat_id, conversations)
            if response:
                with response_container.container():
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(response)
                        play_tts(response)
        else:
            st.session_state.recording_status = voice_text or "فشل التسجيل، جرب تاني."
            st.error(st.session_state.recording_status)
        st.session_state.voice_text = None

def run_app():
    """تشغيل تطبيق Streamlit"""
    st.set_page_config(page_title="EmpathyBot", page_icon="🤖", layout="wide")
    st.title("🤖 EmpathyBot ")

    conversations = load_conversations()
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = str(uuid.uuid4())
        conversations[st.session_state.chat_id] = {
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "title": "New Chat"
        }
        save_conversations(conversations)

    if "last_image_hash" not in st.session_state:
        st.session_state.last_image_hash = None
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "is_recording" not in st.session_state:
        st.session_state.is_recording = False
    if "recording_status" not in st.session_state:
        st.session_state.recording_status = "غير مسجل"
    if "voice_text" not in st.session_state:
        st.session_state.voice_text = None

    messages = conversations[st.session_state.chat_id]["messages"]

    response_container = st.empty()

    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg.get("input", "غير متوفر"))
        elif msg.get("role") == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg.get("output", "غير متوفر"))
                if i == len(messages) - 1:
                    play_tts(msg.get("output"))

    st.write(f"حالة التسجيل: {st.session_state.recording_status}")

    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        user_msg = st.chat_input("اكتب رسالتك هنا...")
    with col2:
        uploaded = st.file_uploader("📎", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="file_uploader")
        st.session_state.uploaded_file = uploaded
    with col3:
        if st.session_state.is_recording:
            if st.button("🛑 إيقاف التسجيل"):
                stop_recording(response_container, st.session_state.chat_id, conversations)
                st.rerun()
        else:
            if st.button("🎤 بدء التسجيل"):
                start_recording()
                st.rerun()

    if user_msg:
        with response_container.container():
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_msg)
        response = generate_response(user_msg, st.session_state.chat_id, conversations)
        if response:
            with response_container.container():
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(response)
                    play_tts(response)
        st.rerun()

    if st.session_state.uploaded_file:
        image = Image.open(st.session_state.uploaded_file)
        image_hash = get_image_hash(image)
        if image_hash != st.session_state.last_image_hash:
            response = generate_response("", st.session_state.chat_id, conversations, image=image, image_hash=image_hash)
            if response:
                with response_container.container():
                    with st.chat_message("user", avatar="👤"):
                        st.markdown("📷 صورة مرفوعة")
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(response)
                        play_tts(response)
                st.session_state.last_image_hash = image_hash
                st.session_state.uploaded_file = None
                st.success("تم تحليل الصورة وإزالتها من الواجهة!")
                st.rerun()

if __name__ == "__main__":
    run_app()
