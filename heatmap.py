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

# --- NEW: Keyword List and Scoring Function ---
spice_keywords = [
    "gasp", "moan", "groan", "shiver", "pulse", "ache", "breath", "panting", 
    "skin", "taste", "lips", "tongue", "bare", "naked", "hips", "thighs", 
    "breast", "chest", "neck", "tangled", "core", "center", "slick", "wet", 
    "hard", "thrust", "peak", "climax", "release", "shatter"
]

def score_chapter(chapter_text):
    text_lower = chapter_text.lower()
    score = 0
    for word in spice_keywords:
        # regex \b ensures we only match whole words (e.g., "hard", not "hardly")
        matches = len(re.findall(r'\b' + word + r'\b', text_lower))
        score += matches
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
        
        # --- NEW: We specifically label the chunks so the AI can count them ---
        top_chunks = []
        for i, (score, chap) in enumerate(scored_chapters[:3]):
            chunk_text = f"--- CHAPTER EXCERPT {i+1} ---\n{chap[:25000]}"
            top_chunks.append(chunk_text)
        
        # 4. Stitch them together
        text_sample = "\n\n".join(top_chunks)
        
    st.success("Heat map complete! Hottest chapters identified. Analyzing content...")
    
    with st.spinner("AI is evaluating the peak spice level..."):
        # --- MODIFIED: Forced Chain-of-Thought Prompt ---
        prompt = f"""
        You are a strict, literal literary analyst. Rate the sexual content ("spice level") of the text sample using this 0-5 scale.

        0 Peppers: No Romance. The text contains zero romantic plotlines, zero romantic tension, and zero physical intimacy. This is for non-romance genres (sci-fi, thriller, nonfiction, etc.).
        1 Pepper: Sweet/Clean Romance. Kissing, holding hands, romantic tension, or sweet closed-door moments. ZERO sexual acts.
        2 Peppers: Closed Door. Heavy kissing, making out, or suggestive dialogue. The scene cuts away before sex occurs. 
        3 Peppers: Gentle Open Door. A physical sexual act occurs on-page, but descriptions are vague OR highly explicit acts occur in 2 or fewer excerpts.
        4 Peppers: Explicit Open Door. Detailed, explicit descriptions of physical sexual acts on-page.
        5 Peppers: Smut. Highly graphic, prolonged explicit sex.

        ABSOLUTE RULES FOR RATINGS 4 AND 5 (Read Carefully):
        - STEP 1: Evaluate each Excerpt individually. Does it contain a physical, on-page sexual act?
        - STEP 2: Count them. If the total number of 'YES' answers is 1 or 2, your FINAL RATING CANNOT exceed 3 Peppers, no matter how graphic or smutty the text is. 
        - STEP 3: You can ONLY award 4 or 5 Peppers if EXCERPT 1, EXCERPT 2, AND EXCERPT 3 ALL evaluate to YES.

        Provide your response in this EXACT format:
        EXCERPT 1 EXPLICIT: [YES or NO]
        EXCERPT 2 EXPLICIT: [YES or NO]
        EXCERPT 3 EXPLICIT: [YES or NO]
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
        
        # --- MODIFIED: The Output Filter to show the Excerpt breakdown ---
        lines = raw_result.split('\n')
        # We now keep lines starting with EXCERPT, RATING, or REASON
        clean_lines = [line.strip() for line in lines if line.startswith(("EXCERPT", "RATING", "REASON"))]
        final_result = "<br><br>".join(clean_lines)
        
        # Custom Highlighted Results Box
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='background-color: rgba(255, 75, 75, 0.05); border-left: 5px solid #ff4b4b; padding: 20px; border-radius: 5px;'>
                <span style='font-size: 1.1rem; line-height: 1.6;'>{final_result}</span>
            </div>
        """, unsafe_allow_html=True)