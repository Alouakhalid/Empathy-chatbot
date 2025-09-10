import streamlit as st
from langdetect import detect
import google.generativeai as genai
import json
import uuid
from datetime import datetime
import emoji
import base64
from io import BytesIO
from PIL import Image

API_KEY = "AIzaSyB_ei3R2CM7DRwYyZw3YkcPtTXhDe6vH14" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

CONVERSATIONS_FILE = "conversations.json"

def load_conversations():
    """تحميل المحادثات من ملف JSON"""
    try:
        with open(CONVERSATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_conversations(conversations):
    """حفظ المحادثات في ملف JSON"""
    with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=4)

def detect_language(text):
    """اكتشاف لغة النص (عربي أو إنجليزي فقط)"""
    try:
        lang = detect(text)
        return "ar" if lang.startswith("ar") else "en"
    except:
        return "ar"  
def analyze_emoji(text):
    """تحليل الإيموجي في النص وإرجاع وصف نصي"""
    emoji_dict = emoji.demojize(text, language='en')
    if emoji_dict != text:
        return emoji_dict
    return "No emojis detected"

def detect_emotion(text, emoji_analysis, image_analysis=None):
    """اكتشاف المشاعر من النص، الإيموجي، والصورة (إن وجدت)"""
    prompt = (
        f"Detect the emotion in this text: '{text}'.\n"
        f"Emoji analysis: '{emoji_analysis}'.\n"
        f"Image facial expression analysis: '{image_analysis if image_analysis else 'No image provided'}'.\n"
        f"Return only the emotion (joy, sadness, anger, fear, neutral, distress, fatigue, suffocation)."
    )
    response = model.generate_content(prompt)
    return response.text.lower().strip()

def analyze_image(image):
    """تحليل تعبيرات الوجه في الصورة"""
    try:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        prompt = (
            "Analyze the facial expression in this image and describe the emotional state "
            "(e.g., tired, distressed, suffocated, happy, neutral). Return a short description."
        )
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_str}])
        return response.text.strip()
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def generate_response(user_message, chat_id, conversations, image=None):
    """توليد رد تعاطفي طويل وطبيعي بناءً على النص، الإيموجي، والصورة"""
    lang = detect_language(user_message) if user_message else "ar"
    emoji_analysis = analyze_emoji(user_message) if user_message else "No text provided"
    image_analysis = analyze_image(image) if image else None
    emotion = detect_emotion(user_message, emoji_analysis, image_analysis)
    
    chat_history = conversations.get(chat_id, {"messages": []})["messages"]
    history_context = "\n".join([f"User: {msg['input']}\nBot: {msg['output']}" for msg in chat_history[-3:]])  # آخر 3 رسائل
    
    rag_prompt = (
        f"Based on the emotion '{emotion}', provide a detailed, natural, and empathetic response in {lang}. "
        f"Use a conversational tone with multiple sentences, as if you're a close friend chatting casually. "
        f"Make the response engaging, varied, and reflective of the user's emotion, considering the text, "
        f"emojis ('{emoji_analysis}'), and facial expression ('{image_analysis if image_analysis else 'No image'}'). "
        f"Include follow-up questions or suggestions to keep the conversation flowing. "
        f"Here is the recent chat history for context:\n{history_context}"
    )
    response_text = model.generate_content(rag_prompt).text
    
    chat_history.append({
        "input": user_message if user_message else "Image only",
        "output": response_text,
        "image_analysis": image_analysis if image_analysis else None
    })
    conversations[chat_id]["messages"] = chat_history
    conversations[chat_id]["last_updated"] = datetime.now().isoformat()
    save_conversations(conversations)
    
    return response_text

def run_streamlit():
    st.set_page_config(page_title="EmpathyBot", page_icon="🤖", layout="wide")

    st.markdown("""
        <style>
        .chat-container {
            max-height: 70vh;
            overflow-y: auto;
            padding: 10px;
        }
        .stChatMessage {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            max-width: 70%;
        }
        .user {
            background: #d1e7dd;
            color: #0f5132;
            margin-left: auto;
            text-align: right;
        }
        .bot {
            background: #e2e3e5;
            color: #333;
        }
        .stChatInput {
            position: fixed;
            bottom: 10px;
            width: 70%;
            padding: 5px;
            display: flex;
            align-items: center;
        }
        .stButton>button {
            background: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
        }
        .sidebar .stButton>button {
            width: 100%;
            margin-top: 10px;
        }
        .upload-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 3px;
            background: #e9ecef;
            color: #333;
            cursor: pointer;
            margin-right: 5px;
            font-size: 13px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            transition: background 0.2s;
        }
        .upload-btn:hover {
            background: #dfe3e8;
        }
        .stFileUploader {
            width: 22px !important;
            display: inline-block !important;
        }
        .stFileUploader > div > div > div {
            padding: 0 !important;
            background: none !important;
            border: none !important;
        }
        .stFileUploader label {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("EmpathyBot - رفيقك العاطفي 🤗")
    st.markdown("كلمني عن إحساسك أو ارفع صورة، هرد عليك بطريقة تناسبك!")

    conversations = load_conversations()
    
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = str(uuid.uuid4())
        conversations[st.session_state.chat_id] = {
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "title": "محادثة جديدة"
        }
        save_conversations(conversations)

    with st.sidebar:
        st.header("المحادثات")
        chat_options = {chat_id: conv["title"] for chat_id, conv in conversations.items()}
        selected_chat = st.selectbox("اختر محادثة", options=list(chat_options.keys()), format_func=lambda x: chat_options[x])
        if st.button("محادثة جديدة"):
            new_chat_id = str(uuid.uuid4())
            conversations[new_chat_id] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "title": f"محادثة {len(conversations) + 1}"
            }
            st.session_state.chat_id = new_chat_id
            save_conversations(conversations)
            st.session_state.messages = []
        
        if st.button("حذف المحادثة الحالية"):
            if st.session_state.chat_id in conversations:
                del conversations[st.session_state.chat_id]
                save_conversations(conversations)
                st.session_state.chat_id = str(uuid.uuid4())
                conversations[st.session_state.chat_id] = {
                    "messages": [],
                    "created_at": datetime.now().isoformat(),
                    "title": "محادثة جديدة"
                }
                save_conversations(conversations)
                st.session_state.messages = []

    if selected_chat != st.session_state.chat_id:
        st.session_state.chat_id = selected_chat
        st.session_state.messages = [
            {"role": "user" if msg["input"] else "assistant", "content": msg.get("input", msg.get("output"))}
            for msg in conversations[selected_chat]["messages"]
        ]

    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "user" if msg["input"] else "assistant", "content": msg.get("input", msg.get("output"))}
                for msg in conversations[st.session_state.chat_id]["messages"]
            ]
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
                st.markdown(message["content"], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="stChatInput">', unsafe_allow_html=True)
        cols = st.columns([0.5, 10])  
        with cols[0]:
            uploaded_image = st.file_uploader("📎", type=["jpg", "jpeg", "png"], key="image_uploader", label_visibility="collapsed")
        with cols[1]:
            prompt = st.chat_input("اكتبي رسالتك...")
        
        if prompt or uploaded_image:
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(prompt, unsafe_allow_html=True)
            
            image = None
            if uploaded_image:
                image = Image.open(uploaded_image)
                st.image(image, width=200, caption="الصورة المرفوعة")
            
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("بفكر..."):
                    response = generate_response(prompt if prompt else "", st.session_state.chat_id, conversations, image)
                st.markdown(response, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    run_streamlit()