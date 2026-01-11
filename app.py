import streamlit as st
import os
from groq import Groq
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import urllib.parse

# --- 1. CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Kind Regards",
    page_icon="🤝",
    layout="centered"
)

# 1. Load the secret API key from the .env file
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

# Initialize Groq (Ensure GROQ_API_KEY is in your .streamlit/secrets.toml)
try:
    client = Groq(api_key)
except:
    st.info("⚠️ Dev Mode: Set `GROQ_API_KEY` in secrets to run.")
    st.stop()

# --- 2. THE TRANSLATOR ENGINE (GROQ) ---
def get_translation(text):
    """
    Uses the LLM to extract the subtext.
    """
    system_prompt = """
    ROLE: You are 'Kind Regards', a diplomatic interpreter of corporate subtext.
    
    TASK:
    1. Analyze the input for passive-aggression, urgency, or fake politeness.
    2. Translate it into blunt, raw truth.
    3. Assign a 'Tension Level' (1-10).
    
    OUTPUT FORMAT (Pipe Separated):
    Original Quote (Shortened if needed) | The Brutal Truth | Tension Level
    
    Example:
    "Per my last email" | "I already told you this, can you read?" | 7
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "Error|Corporate jargon overload. Try again.|0"

# --- 3. THE VIRAL CARD GENERATOR (PILLOW) ---
def create_shareable_card(quote, translation, score):
    """
    Generates a high-quality social media card (1080x1080).
    """
    # Canvas Settings (Dark "Diplomatic" Theme)
    W, H = 1080, 1080
    bg_color = (20, 30, 46)  # Deep Navy
    accent_color = (255, 165, 0) # Orange/Gold for the "Truth"
    text_white = (240, 240, 240)
    
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)

    # --- Fonts (With Fallback) ---
    try:
        # Tries to load standard fonts. If you upload a .ttf file, change these names!
        font_brand = ImageFont.truetype("arial.ttf", 40)
        font_header = ImageFont.truetype("arial.ttf", 60)
        font_quote = ImageFont.truetype("arial.ttf", 70)
        font_trans = ImageFont.truetype("arial.ttf", 85) # Bigger impact
    except:
        font_brand = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_quote = ImageFont.load_default()
        font_trans = ImageFont.load_default()

    # --- HEADER ---
    draw.text((50, 50), "Kind Regards.", font=font_brand, fill=accent_color)
    draw.line([(50, 110), (1030, 110)], fill="#334155", width=3)

    # --- SECTION 1: WHAT THEY SAID ---
    draw.text((80, 200), "WHAT THEY SAID:", font=font_header, fill="#94a3b8") # Muted Blue-Grey
    
    # Wrap text for Quote
    lines = textwrap.wrap(f"\"{quote}\"", width=22)
    y = 280
    for line in lines:
        draw.text((80, y), line, font=font_quote, fill=text_white)
        y += 85

    # --- DIVIDER ARROW ---
    draw.text((500, 580), "⬇", font=font_header, fill=accent_color)

    # --- SECTION 2: WHAT THEY MEANT ---
    # Draw a highlight box behind the truth
    draw.rectangle([(50, 680), (1030, 950)], fill="#1e293b", outline=accent_color, width=4)
    draw.text((80, 630), "WHAT THEY MEANT:", font=font_header, fill=accent_color)
    
    # Wrap text for Translation
    lines = textwrap.wrap(translation, width=20)
    y = 730
    for line in lines:
        draw.text((100, y), line, font=font_trans, fill="white")
        y += 100

    # --- FOOTER ---
    draw.text((80, 1000), f"Tension Level: {score}/10", font=font_brand, fill="white")
    draw.text((750, 1000), "via KindRegards.ai", font=font_brand, fill="#94a3b8")

    return img

# --- 4. THE UI ---

# Header Section
st.markdown("<h1 style='text-align: center; color: #FFA500;'>Kind Regards.</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>What they said vs. What they meant.</h3>", unsafe_allow_html=True)
st.write("---")

# Input
user_input = st.text_area("Paste the email, Slack message, or comment here:", height=150, placeholder="E.g., 'Let's take this offline' or 'Just a gentle reminder'")

if st.button("Translate Subtext 🔍", type="primary"):
    if not user_input:
        st.warning("Please paste some text first.")
    else:
        with st.spinner("Reading between the lines..."):
            # 1. Get Translation
            raw_data = get_translation(user_input)
            parts = raw_data.split('|')
            
            if len(parts) >= 3:
                quote = parts[0].strip()
                translation = parts[1].strip()
                score = parts[2].strip()

                # 2. Display Text Results
                st.subheader("The Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Said:**\n\"{quote}\"")
                with col2:
                    st.error(f"**Meant:**\n\"{translation}\"")

                # 3. Generate Image
                img = create_shareable_card(quote, translation, score)
                
                # 4. Show Image
                st.write("---")
                st.subheader("Your Shareable Card")
                st.image(img, caption="Right-click to copy or use Download button below", use_container_width=True)
                
                # 5. Download Button
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="⬇️ Download Image",
                    data=byte_im,
                    file_name="kind_regards_translation.png",
                    mime="image/png"
                )

                # 6. Social Share Links
                st.write("### Spread the truth:")
                
                share_text = f"Official Translation:\n\n\"{quote}\"\n⬇\n\"{translation}\"\n\nAnalyzed by Kind Regards."
                encoded_text = urllib.parse.quote(share_text)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("🐦 Post on X", f"https://twitter.com/intent/tweet?text={encoded_text}")
                with c2:
                    st.link_button("💬 Send on WhatsApp", f"https://wa.me/?text={encoded_text}")
                
            else:
                st.error("Could not translate. Try a shorter sentence.")

# Footer
st.markdown("---")
st.caption("🔒 Privacy Note: No data is stored. Your boss will never know.")