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
        sample_size = 50000  
        text_sample = raw_text[len(raw_text)//3 : (len(raw_text)//3) + sample_size]
        
    st.success("Book successfully read! Analyzing content...")
    
    with st.spinner("AI is evaluating the spice level..."):
        prompt = f"""
        You are an expert literary analyst specializing in content ratings. 
        Analyze the following text sample from a novel and rate its sexual content ("spice level") strictly based on this 1-5 scale:

        1 Pepper (Sweet / Fade to Black): Zero to minimal sexual content. Focuses heavily on relationships, holding hands, or sweet, "closed-door" moments where the action cuts away.
        2 Peppers (Closed Door): The story hints at physical attraction, but explicit acts remain off-page. The door closes before anything graphic occurs.
        3 Peppers (Gentle Open Door): The "Novice" level. The reader is present for intimate scenes, and specific body parts or actions are described, but the focus remains on the romantic connection rather than heavy explicit detail.
        4 Peppers (Explicit Open Door): Multiple explicit intimate scenes. Authors use detailed language and describe a variety of acts.
        5 Peppers (Smut/Explicit): Highly graphic, detailed sexual content throughout the novel. The narrative often centers heavily on the physical intimacy.

        Provide your response in this exact format:
        RATING: [Number of peppers, e.g., 3 Peppers]
        REASON: [A 2-3 sentence explanation of why you gave this rating based on the text provided, without quoting explicit words directly]

        Here is the text to analyze:
        {text_sample}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.choices[0].message.content
        
        # --- NEW: Custom Highlighted Results Box without icons/titles ---
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='background-color: rgba(255, 75, 75, 0.05); border-left: 5px solid #ff4b4b; padding: 20px; border-radius: 5px;'>
                <span style='font-size: 1.1rem; line-height: 1.6;'>{result}</span>
            </div>
        """, unsafe_allow_html=True)