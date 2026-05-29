import streamlit as st
from openai import OpenAI
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re  # --- NEW: Required for finding whole words in the text ---

# 1. Set up the look and layout of your website
st.set_page_config(page_title="Spice Level Scanner", page_icon="🌶️", layout="wide")

# ----------------- SIDEBAR LEGEND -----------------
with st.sidebar:
    st.markdown("## 🌶️ Spice Level Guide")
    st.markdown("---")
    st.markdown("""
**🌶️ Sweet / Fade to Black:** Zero to minimal sexual content. Focuses heavily on relationships, holding hands, or sweet, 'closed-door' moments where the action cuts away.

**🌶️🌶️ Closed Door:** The story hints at physical attraction, but explicit acts remain off-page. The door closes before anything graphic occurs.

**🌶️🌶️🌶️ Gentle Open Door:** The 'Novice' level. The reader is present for intimate scenes, and specific body parts or actions are described, but the focus remains on the romantic connection.

**🌶️🌶️🌶️🌶️ Explicit Open Door:** Multiple explicit intimate scenes. Authors use detailed language and describe a variety of acts.

**🌶️🌶️🌶️🌶️🌶️ Smut / Explicit:** Highly graphic, detailed sexual content throughout the novel. The narrative often centers heavily on the physical intimacy.
""")

# ----------------- MAIN INTERFACE -----------------
st.markdown("""
    <div style='text-align: center; padding: 1rem 0 2rem 0;'>
        <h1 style='color: #ff4b4b; font-size: 3rem;'>🌶️ Spice Level Scanner</h1>
        <p style='font-size: 1.2rem; color: #555;'>Upload an EPUB file to instantly scan its content and determine its exact spice rating.</p>
    </div>
""", unsafe_allow_html=True)

# We automatically grab the key from your secret vault behind the scenes!
api_key = st.secrets["OPENAI_API_KEY"]

# 3. Create a clear drag-and-drop file upload box
uploaded_file = st.file_uploader(
    "Drag and drop your EPUB book here, or click to browse", 
    type="epub",
    accept_multiple_files=False
)

# --- OPTIMIZED WEIGHTED DICTIONARY (Based on Library Audit) ---
spice_keywords = {
    # Level 1: Tension & Multi-use words (1 point)
    "gasp": 1, "moan": 1, "groan": 1, "shiver": 1, "pulse": 1, "ache": 1, 
    "breath": 1, "panting": 1, "taste": 1, 
    "hard": 1, "wet": 1, "center": 1, "release": 1, "length": 1, # Demoted to prevent false positives
    
    # Level 2: Physical (3 points)
    "lips": 3, "tongue": 3, "bare": 3, "naked": 3, "hips": 3, "thighs": 3, 
    "breast": 3, "chest": 3, "neck": 3, "tangled": 3, 
    
    # Level 3: Explicit / High-Signal (10 points)
    "core": 10, "slick": 10, "thrust": 10, "climax": 10, "shatter": 10,
    "clit": 10, "cock": 10, "dick": 10, "erection": 10,
    "thrusting": 10, "stroking": 10, "grinding": 10, "penetrating": 10,
    "folds": 10, "throbbing": 10, "swollen": 10, "apex": 10, "sheath": 10,
    "nub": 10, "bud": 10, "member": 10, "shaft": 10, "girth": 10
}

def score_chapter(chapter_text):
    text_lower = chapter_text.lower()
    score = 0
    # We now loop through both the word AND its weight
    for word, weight in spice_keywords.items():
        # regex \b ensures we only match whole words
        matches = len(re.findall(r'\b' + word + r'\b', text_lower))
        # Multiply the number of times it was found by its weight
        score += (matches * weight) 
    return score

# --- MODIFIED: Extracts a LIST of chapters instead of one giant string ---
def extract_chapters_from_epub(file_bytes):
    with open("temp.epub", "wb") as f:
        f.write(file_bytes.getbuffer())
    
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    book = epub.read_epub("temp.epub")
    chapters = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text().strip()
            # Ignore blank pages or tiny title pages (less than 500 chars)
            if len(text) > 500:
                chapters.append(text)
            
    return chapters

# 4. What happens when a file is uploaded
if uploaded_file and api_key:
    client = OpenAI(api_key=api_key)
    
    with st.spinner("Reading the book and generating a heat map... This might take a moment."):
        chapters = extract_chapters_from_epub(uploaded_file)
        
        # 1. Score every chapter in the book
        scored_chapters = [(score_chapter(chap), chap) for chap in chapters]
        
        # 2. Sort the chapters from highest score to lowest score
        scored_chapters.sort(key=lambda x: x[0], reverse=True)
        
        # --- UPGRADED: Grabbing the top 4 hottest chapters ---
        top_chunks = []
        for i, (score, chap) in enumerate(scored_chapters[:4]):
            chunk_text = f"--- CHAPTER EXCERPT {i+1} ---\n{chap[:25000]}"
            top_chunks.append(chunk_text)
        
        # 4. Stitch them together
        text_sample = "\n\n".join(top_chunks)
        
    st.success("Heat map complete! Hottest chapters identified. Analyzing content...")
    
    with st.spinner("AI is evaluating the peak spice level..."):
        # --- UPGRADED: Adjusted Prompt Rules for 4 Excerpts ---
        prompt = f"""
        You are a strict, literal literary analyst. Rate the sexual content ("spice level") of the text sample using this 0-5 scale.

        0 Peppers: No Romance. The text contains zero romantic plotlines, zero romantic tension, and zero physical intimacy. This is for non-romance genres (sci-fi, thriller, nonfiction, etc.).
        1 Pepper: Sweet/Clean Romance. Kissing, holding hands, romantic tension, or sweet closed-door moments. ZERO sexual acts.
        2 Peppers: Closed Door. Heavy kissing, making out, or suggestive dialogue. The scene cuts away before sex occurs. 
        3 Peppers: Gentle Open Door. The 'Novice' level. The reader is present for intimate scenes, and specific body parts or actions are described, but the focus remains on the romantic connection. RATE AS 3 IF EXPLICIT ACTS APPEAR IN ONLY 1 OR 2 EXCERPTS.
        4 Peppers: Explicit Open Door. Multiple explicit intimate scenes. Authors use detailed language and describe a variety of acts. EXPLICIT ACTS MUST APPEAR IN AT LEAST 3 EXCERPTS to qualify for this rating.
        5 Peppers: Smut / Explicit. Highly graphic, detailed sexual content throughout the novel. The narrative often centers heavily on the physical intimacy. EXPLICIT ACTS MUST APPEAR IN AT LEAST 3 EXCERPTS to qualify for this rating.

        ABSOLUTE RULES (Read Carefully):
        - STEP 1 (Frequency Check): Evaluate each Excerpt individually. Does it contain a physical, on-page sexual act?
        - STEP 2 (The Cap): Count your 'YES' answers. If you have 0, 1, or 2 'YES' answers, you are strictly forbidden from giving a 4 or 5 rating. Your FINAL RATING MUST BE 3 OR LOWER. 
        - STEP 3 (The Focus Check): You can ONLY award a 4 or 5 if AT LEAST 3 excerpts evaluate to YES (i.e., 3 or 4 YES answers). 
           * If you have 3 or 4 YES answers, and the overarching plot still carries significant weight alongside the detail, rate it a 4.
           * If you have 3 or 4 YES answers, and the narrative overwhelmingly centers on physical intimacy rather than plot, rate it a 5.

        Provide your response in this EXACT format:
        EXCERPT 1 EXPLICIT: [YES or NO]
        EXCERPT 2 EXPLICIT: [YES or NO]
        EXCERPT 3 EXPLICIT: [YES or NO]
        EXCERPT 4 EXPLICIT: [YES or NO]
        RATING: [Number of peppers, e.g., 0 Peppers]
        REASON: [1-2 sentences justifying your rating based strictly on the text.]

        Here is the text to analyze:
        {text_sample}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Grab the raw response from the AI
        raw_result = response.choices[0].message.content
        
        # The Output Filter (Hiding the AI's "Dialog")
        lines = raw_result.split('\n')
        
        # We only keep lines starting with RATING or REASON for the UI
        clean_lines = [line.strip() for line in lines if line.startswith(("RATING", "REASON"))]
        
        # Stitch those clean lines back together
        final_result = "<br><br>".join(clean_lines)
        
        # Custom Highlighted Results Box
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='background-color: rgba(255, 75, 75, 0.05); border-left: 5px solid #ff4b4b; padding: 20px; border-radius: 5px;'>
                <span style='font-size: 1.1rem; line-height: 1.6;'>{final_result}</span>
            </div>
        """, unsafe_allow_html=True)