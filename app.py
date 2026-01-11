import streamlit as st
import os
import time
import urllib.parse
import re
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
from groq import Groq
from dotenv import load_dotenv

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Kind Regards AI",
    page_icon="🤝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; color: #2C3E50; }
    /* Styling for the steps */
    .step-label {
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "history" not in st.session_state:
    st.session_state.history = []
if "total_decoded" not in st.session_state:
    st.session_state.total_decoded = 0
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# --- 4. API SETUP ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⚠️ API Key missing. Please set GROQ_API_KEY.")
    st.stop()

@st.cache_resource
def get_groq_client():
    return Groq(api_key=api_key)

client = get_groq_client()

# --- 5. LOGIC & HELPERS ---
def extract_score(text):
    match = re.search(r"Toxicity:\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return 5

def generate_stream(prompt, temp):
    try:
        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=400,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"

# --- 6. ROBUST IMAGE GENERATOR (Drawing Shapes) ---
def create_social_card(said, meant, scenario, score):
    # 16:9 Landscape
    W, H = 1600, 900 
    img = Image.new('RGB', (W, H), color=(255, 255, 255)) 
    draw = ImageDraw.Draw(img)
    
    # Font Loading (Fallbacks)
    try:
        font_brand = ImageFont.truetype("DejaVuSans-Bold.ttf", 40) 
        font_score = ImageFont.truetype("DejaVuSans-Bold.ttf", 30) 
        font_header = ImageFont.truetype("DejaVuSans-Bold.ttf", 35) 
        font_text = ImageFont.truetype("DejaVuSans.ttf", 32) 
        font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except:
        try:
            font_brand = ImageFont.truetype("arialbd.ttf", 40)
            font_score = ImageFont.truetype("arialbd.ttf", 30)
            font_header = ImageFont.truetype("arialbd.ttf", 35) 
            font_text = ImageFont.truetype("arial.ttf", 32)
            font_bold = ImageFont.truetype("arialbd.ttf", 32)
        except:
            font_brand = font_score = font_header = font_text = font_bold = ImageFont.load_default()
        
    # --- DRAWING ---
    margin_x = 80 
    icon_size = 35
    text_offset = 60
    line_height = 42
    section_gap = 30

    # 1. Header
    # Icon: Dark Blue Rounded Rectangle
    draw.rounded_rectangle([(margin_x, 55), (margin_x + 40, 95)], radius=10, fill="#2C3E50")
    draw.text((margin_x + 55, 50), "Kind Regards AI", font=font_brand, fill="#2C3E50")
    
    # Score: Yellow Dot + Text
    draw.ellipse([(1310, 58), (1340, 88)], fill="#F1C40F") 
    draw.text((1350, 60), f"Toxicity: {score}/10", font=font_score, fill="#F1C40F") 

    draw.line([(margin_x, 110), (W - margin_x, 110)], fill="#E74C3C", width=4)
    
    # 2. THEY SAID
    y = 150
    # Icon: Grey Circle
    draw.ellipse([(margin_x, y+5), (margin_x + icon_size, y+5 + icon_size)], fill="#95A5A6")
    draw.text((margin_x + text_offset, y), "THEY SAID", font=font_header, fill="#7F8C8D")
    y += 50
    
    wrapper = textwrap.TextWrapper(width=75)
    for line in wrapper.wrap(f'"{said}"')[:3]: 
        draw.text((margin_x + text_offset, y), line, font=font_text, fill="#2C3E50")
        y += line_height
        
    # Separator
    y += section_gap
    draw.line([(margin_x, y), (W - margin_x, y)], fill="#BDC3C7", width=2) 
    y += section_gap + 10
        
    # 3. THEY MEANT
    # Icon: Red Circle
    draw.ellipse([(margin_x, y+5), (margin_x + icon_size, y+5 + icon_size)], fill="#E74C3C")
    draw.text((margin_x + text_offset, y), "THEY MEANT", font=font_header, fill="#E74C3C")
    y += 50
    
    for line in wrapper.wrap(meant)[:5]: 
        draw.text((margin_x + text_offset, y), line, font=font_text, fill="#2C3E50")
        y += line_height
        
    y += section_gap

    # 4. SCENARIO
    # Icon: Black Square
    draw.rectangle([(margin_x, y+5), (margin_x + icon_size, y+5 + 25)], fill="#2C3E50")
    draw.text((margin_x + text_offset, y), "SCENARIO", font=font_bold, fill="#2C3E50")
    y += 50
    for line in wrapper.wrap(scenario)[:5]: 
        draw.text((margin_x + text_offset, y), line, font=font_text, fill="#566573") 
        y += line_height
    
    return img

# --- 7. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Settings")
    tone = st.selectbox("Tone", ["Brutally Honest 💀", "Sarcastic 🤡", "Professional 👔", "Humorous 😂"])
    temp = st.slider("Creativity", 0.0, 1.0, 0.7)
    st.divider()
    st.metric("Total Decoded", st.session_state.total_decoded)

# --- 8. MAIN UI ---
st.title("🤝 Kind Regards AI")
st.markdown("##### The corporate jargon decoder powered by Groq speed ⚡")

tab_main, tab_history, tab_about = st.tabs(["🔍 Live Decoder", "📜 History", "ℹ️ About"])

# ==========================================
# TAB 1: LIVE DECODER
# ==========================================
with tab_main:
    st.subheader("📩 Incoming Message")
    
    user_input = st.text_area("Paste the email or slack message here:", height=120, key="main_input", placeholder="E.g., 'Per my last email'")
    
    c1, c2 = st.columns([1, 4])
    with c1:
        submit = st.button("🔥 Decode", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑️ Clear", use_container_width=False):
            st.session_state.current_result = None
            st.rerun()

    # --- PROCESSING ---
    if submit and user_input:
        
        prompt = f"""
        ROLE: You are a {tone} corporate translator.
        TASK: Translate input to raw truth, write scenario, rate toxicity.
        FORMAT (Strictly follow this layout with new lines):
        **MEANING:** [Translation]
        
        **SCENARIO:** [Scenario]
        
        **Toxicity:** [Score and brief explanation]
        
        INPUT: "{user_input}"
        """
        
        full_response = ""
        result_container = st.container(border=True)
        with result_container:
            st.subheader("💀 The Truth")
            stream_box = st.empty()
            for chunk in generate_stream(prompt, temp):
                full_response += chunk
                stream_box.markdown(full_response)
        
        # Parsing
        score = extract_score(full_response)
        try:
            meaning_part = full_response.split("**MEANING:**")[1].split("**SCENARIO:**")[0].strip()
            temp_scenario = full_response.split("**SCENARIO:**")[1]
            if "**Toxicity:**" in temp_scenario:
                scenario_part = temp_scenario.split("**Toxicity:**")[0].strip()
            else:
                scenario_part = temp_scenario.strip()
        except:
            meaning_part = full_response
            scenario_part = ""

        # Save State
        st.session_state.current_result = {
            "input": user_input,
            "response": full_response,
            "meaning": meaning_part,
            "scenario": scenario_part,
            "score": score
        }
        st.session_state.history.insert(0, {"input": user_input, "output": meaning_part, "score": score, "time": time.strftime("%H:%M")})
        st.session_state.total_decoded += 1
        st.rerun()

    # --- PERSISTENT RESULT & SHARING ---
    if st.session_state.current_result:
        res = st.session_state.current_result
        
        with st.container(border=True):
            st.subheader("💀 The Truth")
            st.markdown(res["response"])
            
        st.divider()
        st.markdown("### 📸 Share Result")
        st.info("Tip: Download the image first, then attach it to your post!")

        # 1. GENERATE BUTTON
        if st.button("🖼️ Generate Image Card", use_container_width=True):
            with st.spinner("Designing card..."):
                img = create_social_card(res["input"], res["meaning"], res["scenario"], res["score"])
                st.image(img, caption="Preview (16:9)", use_container_width=True)
                
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()

                # 2. TWO-STEP SHARE UI
                st.write("")
                col_step1, col_step2 = st.columns(2)
                
                with col_step1:
                    st.markdown("<p class='step-label'>1️⃣ Step 1: Save Image</p>", unsafe_allow_html=True)
                    st.download_button(
                        label="⬇️ Download Image",
                        data=byte_im,
                        file_name="kind_regards_card.png",
                        mime="image/png",
                        type="primary",
                        use_container_width=True
                    )
                
                with col_step2:
                    st.markdown("<p class='step-label'>2️⃣ Step 2: Open App</p>", unsafe_allow_html=True)
                    share_text = urllib.parse.quote(f"I decoded this with Kind Regards AI:\n\n{res['input']} -> {res['meaning']}\n\nTry it: https://huggingface.co/spaces/LakhanPawar1/Kind_Regards_AI")
                    
                    st.link_button("🐦 Post Text on X (Attach Img)", f"https://twitter.com/intent/tweet?text={share_text}", use_container_width=True)
                    st.link_button("💬 Send Text on WhatsApp", f"https://wa.me/?text={share_text}", use_container_width=True)

# ==========================================
# HISTORY & ABOUT TABS
# ==========================================
with tab_history:
    st.subheader("📜 Recent Decodings")
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
    for item in st.session_state.history:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 1])
            c1.caption(f"🕒 {item['time']}")
            c2.markdown(f"**Said:** {item['input']}")
            c3.markdown(f"**Toxicity:** {item['score']}/10")
            st.info(f"**Meant:** {item['output']}")

with tab_about:
    st.markdown("### 🤝 About Kind Regards AI\nPowered by **Llama 3.1** & **Groq**.")
