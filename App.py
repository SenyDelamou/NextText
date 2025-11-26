# Application Streamlit : téléversement PDF -> extraction texte -> téléchargeable en .txt et .json
# Design Ultra-Premium & Extraction Intelligente

import io
import json
import re
import time
import unicodedata
import streamlit as st
import pdfplumber

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="TextFlow | Extracteur PDF Premium",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS AVANCÉ & ANIMATIONS (GLASSMORPHISM) ---
st.markdown("""
<style>
    /* Importation Polices Premium */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap');

    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --bg-color: #0f172a;
        --card-bg: rgba(30, 41, 59, 0.7);
        --text-color: #f8fafc;
        --accent-color: #38bdf8;
    }

    /* Reset & Base */
    .stApp {
        background-color: var(--bg-color);
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.15) 0px, transparent 50%);
        color: var(--text-color);
        font-family: 'Outfit', sans-serif;
    }

    /* Typography */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    
    .hero-title {
        font-size: 4rem;
        background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255,255,255,0.1);
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        color: #94a3b8;
        font-weight: 300;
        margin-bottom: 3rem;
    }

    /* Cards (Glassmorphism) */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.3);
    }

    /* Metrics */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--accent-color);
    }
    .metric-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94a3b8;
    }

    /* Custom Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* Text Area & Code */
    .stTextArea textarea {
        background-color: rgba(0,0,0,0.3) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 8px;
        color: #94a3b8;
        padding: 8px 16px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fadeIn 0.6s ease-out forwards;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def clean_text(s: str) -> str:
    """Nettoie et normalise le texte extrait avec précision."""
    if s is None: return ""
    s = unicodedata.normalize("NFC", s)
    replacements = {
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', 
        "\u00ab": '"', "\u00bb": '"', "\u2013": "-", "\u2014": "-", 
        "\u2026": "...", "\u00A0": " ", "\u2002": " ", "\u2003": " ", "\u2009": " "
    }
    for old, new in replacements.items(): s = s.replace(old, new)
    s = re.sub(r'[\u200B-\u200D\uFEFF]', '', s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r'(\w+)-\n(\w+)', r'\1\2', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r' *\n *', '\n', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    uploaded_file = st.file_uploader("Importer PDF", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file:
        st.success("Fichier chargé !")
        
    st.markdown("---")
    st.markdown("### 🎨 Affichage")
    preview_chars = st.slider("Densité de l'aperçu", 100, 5000, 1500, 100)
    
    st.markdown("---")
    st.markdown("""
    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; font-size: 0.8rem; color: #94a3b8;'>
        <strong>TextFlow v3.0</strong><br>
        L'excellence en extraction documentaire.
    </div>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">TextFlow</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">L\'élégance de l\'extraction documentaire.</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIQUE PRINCIPALE ---
if not uploaded_file:
    # État vide (Landing Page)
    st.markdown("""
    <div class="animate-fade-in" style="animation-delay: 0.2s;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-top: 2rem;">
            <div class="glass-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">⚡</div>
                <h3>Ultra Rapide</h3>
                <p style="color: #94a3b8;">Traitement instantané de vos documents, quelle que soit leur taille.</p>
            </div>
            <div class="glass-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">💎</div>
                <h3>Qualité Premium</h3>
                <p style="color: #94a3b8;">Nettoyage intelligent des artefacts et normalisation typographique.</p>
            </div>
            <div class="glass-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">🛡️</div>
                <h3>Sécurisé</h3>
                <p style="color: #94a3b8;">Traitement 100% local. Vos données ne quittent jamais votre session.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- TRAITEMENT ---
with st.status("Traitement du document en cours...", expanded=True) as status:
    st.write("📥 Lecture du fichier binaire...")
    pdf_bytes = uploaded_file.read()
    time.sleep(0.3) # Petit délai pour l'effet UX
    
    st.write("🧠 Initialisation du moteur d'extraction...")
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            progress_bar = st.progress(0)
            
            for i, page in enumerate(pdf.pages):
                # Extraction
                try:
                    raw_text = page.extract_text()
                except:
                    raw_text = ""
                
                # Nettoyage
                cleaned = clean_text(raw_text)
                pages.append({"page_number": i + 1, "text": cleaned})
                
                # Mise à jour progression
                progress = (i + 1) / len(pdf.pages)
                progress_bar.progress(progress)
                
            status.update(label="Extraction terminée avec succès !", state="complete", expanded=False)
            
    except Exception as e:
        status.update(label="Erreur critique", state="error")
        st.error(f"Erreur : {e}")
        st.stop()

# --- DASHBOARD DE RÉSULTATS ---
total_chars = sum(len(p["text"]) for p in pages)
n_pages = len(pages)

st.markdown("---")
st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)

# Métriques
cols = st.columns(4)
metrics_data = [
    ("Fichier", uploaded_file.name[:15] + "..." if len(uploaded_file.name)>15 else uploaded_file.name),
    ("Pages", str(n_pages)),
    ("Caractères", f"{total_chars:,}".replace(",", " ")),
    ("Densité", f"{int(total_chars/n_pages)} car/page")
]

for col, (label, value) in zip(cols, metrics_data):
    with col:
        st.markdown(f"""
        <div class="glass-card" style="padding: 1.5rem; text-align: center;">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- VISUALISATION ---
st.markdown("### 👁️ Explorateur de Contenu")
st.markdown("Naviguez à travers les pages extraites.")

if len(pages) > 0:
    # On utilise des tabs pour les premières pages
    max_tabs = 10
    tabs = st.tabs([f"Page {p['page_number']}" for p in pages[:max_tabs]])
    
    for i, tab in enumerate(tabs):
        with tab:
            p = pages[i]
            if p["text"]:
                st.code(p["text"], language="text")
            else:
                st.info("Cette page semble vide ou ne contient que des images.")
                
    if len(pages) > max_tabs:
        st.warning(f"⚠️ Affichage limité aux {max_tabs} premières pages pour optimiser les performances.")

# --- EXPORT ---
st.markdown("---")
st.markdown("### 📦 Exportation des Données")

txt_content = "\n\n".join([f"=== Page {p['page_number']} ===\n{p['text']}" for p in pages])
json_content = json.dumps({
    "meta": {"filename": uploaded_file.name, "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    "data": pages
}, ensure_ascii=False, indent=2)

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        label="📥 Télécharger le Rapport (.txt)",
        data=txt_content.encode("utf-8"),
        file_name=f"TextFlow_{uploaded_file.name}.txt",
        mime="text/plain",
    )
with col2:
    st.download_button(
        label="🔮 Télécharger la Structure (.json)",
        data=json_content.encode("utf-8"),
        file_name=f"TextFlow_{uploaded_file.name}.json",
        mime="application/json",
    )
