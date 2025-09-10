EmpathyBot - Professional Summary
Project Overview
EmpathyBot is a sophisticated AI-driven conversational tool designed to deliver empathetic and context-aware responses. Built using Streamlit and integrated with Google Generative AI, it analyzes user inputs—including text, emojis, and facial expressions from uploaded images (JPG, JPEG, PNG)—to detect emotions such as joy, sadness, distress, or fatigue. The application supports multilingual responses in Arabic and English, tailored to the user's input language, and maintains conversation continuity through a JSON-based memory system.
Key Features

Emotion Analysis: Leverages advanced AI to interpret text, emojis, and image-based facial expressions.
Multilingual Capability: Seamlessly responds in Arabic or English based on detected language.
Image Integration: Supports image uploads for enhanced emotional context.
Persistent Memory: Stores chat history in conversations.json for ongoing context.
Intuitive Design: Features a clean, ChatGPT-inspired interface with a streamlined attach button.

Technical Requirements

Python 3.7+
Active internet connection for API usage

Installation & Setup

Clone the repository:git clone <repository-url>
cd empathybot


Install dependencies:pip install streamlit google-generativeai langdetect emoji pillow


Configure API key:
Obtain a key from Google AI Studio.
Replace YOUR_API_KEY_HERE in app2.py or set as an environment variable:export GOOGLE_API_KEY=your_api_key

Update app2.py with:import os
API_KEY = os.getenv("GOOGLE_API_KEY")





Usage

Launch the app:streamlit run app2.py


Interact by typing messages or uploading images via the attach button, then press Enter.
Manage chats via the sidebar to start new conversations or delete existing ones.

File Structure

app2.py: Core application logic.
conversations.json: Auto-generated chat history file.

Customization & Contribution

Adjust the CSS in app2.py for design tweaks.
Extend language support or enhance security (e.g., with cryptography for encryption).
Contribute via pull requests or issue submissions on the repository.

License
Distributed under the MIT License - see LICENSE for details.
Contact
For inquiries, please use the repository's issue tracker.

Last updated: 09:06 PM EEST, Wednesday, September 10, 2025
