import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Paginastijling
st.set_page_config(page_title="Vergunning Verplichtingen Monitor", layout="wide")

st.title("📄 Universele Vergunning Verplichtingen & Deadlines Monitor")
st.markdown("""
Upload je omgevingsvergunning (PDF), geef op op welke pagina's de voorschriften staan en stel de datum van inwerkingtreding in. 
Het programma scant de geselecteerde pagina's automatisch op verplichtingen en termijnen.
""")

# --- ZIJBALK VOOR INVOER ---
st.sidebar.header("1. Configuratie & Pagina's")
uploaded_file = st.sidebar.file_uploader("Upload Omgevingsvergunning (PDF)", type=["pdf"])

paginas_input = st.sidebar.text_input(
    "Pagina's met voorschriften", 
    value="", 
    placeholder="Bijv. 48-57 of 30,35",
    help="Vul hier het paginabereik in waar de voorschriften in deze specifieke vergunning staan."
)

default_date = datetime.strptime("2026-06-12", "%Y-%m-%d").date()
inwerking_date = st.sidebar.date_input("Datum van inwerkingtreding", value=default_date)

st.sidebar.markdown("---")
st.sidebar.info("Tip: Geef de exacte pagina's op waar de voorschriften beginnen en eindigen.")

# Functie om paginabereik om te zetten
def parse_page_ranges(range_str, total_pages):
    if not range_str.strip():
        return []
    page_nums = set()
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for p in range(max(1, start), min(total_pages, end) + 1):
                    page_nums.add(p - 1)
            except ValueError:
                pass
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    page_nums.add(p - 1)
            except ValueError:
                pass
    return sorted(list(page_nums))

# Functie om automatisch zinnen met verplichtingen/termijnen te filteren
def extract_potential_obligations(text):
    # Splits de tekst op in zinnen of alinea's
    lines = text.split('\n')
    filtered_results = []
    
    # Trefwoorden die vaak wijzen op een verplichting, rapportage of termijn
    trigger_words = [
        'binnen', 'maand', 'maanden', 'jaar', 'jaarlijks', 'dagen', 'uur', 
        'indienen', 'melden', 'overleggen', 'verstrekken', 'rapporteren', 
        'voordat', 'voorafgaand', 'ten minste', 'termijn'
    ]
    
    for line in lines:
        line_lower = line.lower()
        # Controleer of de regel een voorschrift-aanduiding bevat (bijv. "15.1" of "Voorschrift") of een triggerwoord
        has_trigger = any(word in line_lower for word in trigger_words)
        is_article = 'voorschrift' in line_lower or re.search(r'\b\d+\.\d+\b', line)
        
        if has_trigger or is_article:
            cleaned_line = line.strip()
            if len(cleaned_line) > 15: # Skip lege of heel korte regels
                filtered_results.append(cleaned_line)
                
    return list(set(filtered_results)) # Unieke resultaten

# --- HOOFDSCHERM ---
if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
    
    target_pages = parse_page_ranges(paginas_input, total_pages)

    if not paginas_input.strip():
        st.warning("⚠️ Vul aan de linkerkant in de zijbalk in op welke pagina's de voorschriften staan.")
    elif not target_pages:
        st.error("❌ Ongeldig paginabereik opgegeven. Controleer de invoer (bijv. 48-57).")
    else:
        # Lees alleen de geselecteerde voorschriften-pagina's uit
        voorschriften_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for p_idx in target_pages:
                page = pdf.pages[p_idx]
                text = page.extract_text()
                if text:
                    voorschriften_text += f"\n{text}\n"

        st.success(f"PDF succesvol geladen. Pagina's **{paginas_input}** automatisch gefilterd en geanalyseerd!")

        # Automatisch filteren van verplichtingen
        raw_obligations = extract_potential_obligations(voorschriften_text)

        st.subheader("🔍 Automatisch gedetecteerde verplichtingen & voorschriften")
        st.markdown(f"Hieronder staan de zinnen uit de geselecteerde pagina's waarin termen staan die duiden op een verplichting of termijn (gebaseerd op inwerkingtreding per **{inwerking_date.strftime('%d-%m-%Y')}**):")

        if raw_obligations:
            # Zet de gefilterde zinnen in een nette tabel
            df_data = []
            for idx, item in enumerate(raw_obligations, start=1):
                df_data.append({
                    "Nr": idx,
                    "Gedetecteerde Voorschrift / Verplichting": item,
                    "Inwerkingtreding": inwerking_date.strftime('%d-%m-%Y')
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

            # Downloadknop
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download gedetecteerd overzicht als CSV",
                data=csv,
                file_name=f"gefilterde_vergunning_verplichtingen_{inwerking_date}.csv",
                mime='text/csv',
            )
        else:
            st.warning("Geen specifieke verplichtingen automatisch gedetecteerd in dit paginabereik. Probeer een ander bereik of controleer de tekst hieronder.")

        # Volledige tekst inzage als back-up
        with st.expander(f"📖 Bekijk de volledige ruwe tekst van pagina {paginas_input}"):
            st.text_area("Ruwe tekst", voorschriften_text, height=300)

else:
    st.info("👈 Upload ten minste een PDF-bestand via de zijbalk om de applicatie te starten.")
