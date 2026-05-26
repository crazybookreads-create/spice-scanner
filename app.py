import streamlit as st
from openai import OpenAI
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# 1. Set up the look and layout of your website
st.set_page_config(page_title="Spice Level Scanner", page_icon="🌶️", layout="wide")

# ----------------- SIDEBAR LEGEND -----------------
with st.sidebar:
    st.markdown("## 🌶️ Spice Level Guide")
    st.markdown("---")
    st.markdown("""
**🌶️ Sweet / Fade to Black:** 
Zero to minimal sexual content. Focuses heavily on relationships, holding hands, or sweet, 'closed-door' moments where the action cuts away.

**🌶️🌶️ Closed Door:** 
The story hints at physical attraction, but explicit acts remain off-page. The door closes before anything graphic occurs.

**🌶️🌶️🌶️ Gentle Open Door:** 
The 'Novice' level. The reader is present for intimate scenes, and specific body parts or actions are described, but the focus remains on the romantic connection.

**🌶️🌶️🌶️🌶️ Explicit Open Door:** 
Multiple explicit intimate scenes. Authors use detailed language and describe a variety of acts.

**🌶️🌶️🌶️🌶️🌶️ Smut / Explicit:** 
Highly graphic, detailed sexual content throughout the novel. The narrative often centers heavily on the physical intimacy.
""")

# ----------------- MAIN INTERFACE -----------------
st.markdown("""
    <div style='text-align: center; padding: 1rem 0 2rem 0;'>
        <h1 style='color: #ff4b4b; font-size: 3rem;'>🌶️ Spice Level Scanner</h1>
        <p style='font-size: 1.2rem; color: #555;'>Upload an EPUB file to instantly scan its content and determine its exact spice rating.</p>
    </div>
""", unsafe_allow_html=True)

# NEW: We automatically grab the key from your secret vault behind the scenes!
api_key = st.secrets["OPENAI_API_KEY"]

# 3. Create a clear drag-and-drop file upload box
uploaded_file = st.file_uploader(
    "Drag and drop your EPUB book here, or click to browse", 
    type="epub",
    accept_multiple_files=False
)

def extract_text_from_epub(file_bytes):
    with open("temp.epub", "wb") as f:
        f.write(file_bytes.getbuffer())
    
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    book = epub.read_epub("temp.epub")
    full_text = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            full_text.append(soup.get_text())
            
    return "\n".join(full_text)

# 4. What happens when a file is uploaded
if uploaded_file and api_key:
    client = OpenAI(api_key=api_key)
    
    with st.spinner("Reading the book... This might take a moment."):
        raw_text = extract_text_from_epub(uploaded_file)
        
        # --- NEW: Multi-Chunk Sampling Strategy ---
        length = len(raw_text)
        chunk_size = 25000  # We will take 25k characters from 3 different spots
        
        # Grab text from the 50%, 75%, and 85% marks of the book
        chunk1 = raw_text[length//2 : (length//2) + chunk_size]
        chunk2 = raw_text[int(length * 0.75) : int(length * 0.75) + chunk_size]
        chunk3 = raw_text[int(length * 0.85) : int(length * 0.85) + chunk_size]
        
        # Stitch them together into one giant text sample for the AI
        text_sample = chunk1 + "\n\n...[TEXT SKIPPED]...\n\n" + chunk2 + "\n\n...[TEXT SKIPPED]...\n\n" + chunk3
        
    st.success("Book successfully read! Analyzing content...")
    
    with st.spinner("AI is evaluating the peak spice level..."):
        prompt = f"""
        You are a strict, literal literary analyst. Rate the sexual content ("spice level") of the text sample using this 1-5 scale.

        1 Pepper: Sweet/Clean. Kissing, holding hands, romantic tension. ZERO sexual acts.
        2 Peppers: Closed Door. Heavy kissing, making out, or suggestive dialogue. The scene cuts away before sex occurs. 
        3 Peppers: Gentle Open Door. A physical sexual act occurs on-page, but descriptions are vague and focus on emotion.
        4 Peppers: Explicit Open Door. Detailed, explicit descriptions of physical sexual acts on-page.
        5 Peppers: Smut. Highly graphic, prolonged explicit sex.

        STEP 1: You must first determine if a physical sexual act actually occurs on the page. 
        STEP 2: If NO physical sexual act occurs, the rating MUST be a 1 or 2. It is mathematically impossible to score a 3, 4, or 5 without an on-page sexual act.

        Provide your response in this EXACT format:
        ON-PAGE SEX ACT: [Answer YES or NO]
        RATING: [Number of peppers, e.g., 1 Pepper]
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
        
        # --- NEW: The Output Filter ---
        # Split the AI's response into separate lines
        lines = raw_result.split('\n')
        
        # Create a clean list that ONLY keeps lines starting with RATING or REASON
        clean_lines = [line.strip() for line in lines if line.startswith("RATING:") or line.startswith("REASON:")]
        
        # Stitch those clean lines back together with a nice double line-break
        final_result = "<br><br>".join(clean_lines)
        
        # Custom Highlighted Results Box
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='background-color: rgba(255, 75, 75, 0.05); border-left: 5px solid #ff4b4b; padding: 20px; border-radius: 5px;'>
                <span style='font-size: 1.1rem; line-height: 1.6;'>{final_result}</span>
            </div>
        """, unsafe_allow_html=True)