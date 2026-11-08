import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Paginastijling
st.set_page_config(page_title="Vergunning Verplichtingen Monitor", layout="wide")

st.title("📄 Vergunning Verplichtingen & Deadlines Monitor")
st.markdown("""
Upload hieronder je omgevingsvergunning (PDF), geef op op welke pagina's de voorschriften staan en stel de datum van inwerkingtreding in. 
Het programma leest de geselecteerde pagina's uit zodat je de verplichtingen kunt bekijken en verwerken.
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
st.sidebar.info("Tip: Controleer eerst in de PDF op welke pagina's de voorschriften staan.")

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
                    voorschriften_text += f"\n--- PAGINA {p_idx + 1} ---\n" + text

        st.success(f"PDF succesvol geladen. Pagina's **{paginas_input}** succesvol ingelezen!")

        # Toon de tekst zodat de gebruiker kan nazoeken wat er in DEZE specifieke vergunning staat
        with st.expander(f"📖 Lees de tekst van de voorschriften (Pagina {paginas_input})"):
            st.text_area("Inhoud voorschriften", voorschriften_text, height=300)

        st.markdown("---")
        st.subheader("📝 Overzicht verplichtingen voor deze vergunning")
        st.markdown(f"Inwerkingtreding ingesteld op: **{inwerking_date.strftime('%d-%m-%Y')}**. Hieronder kun je optioneel eigen notities of verplichtingen op basis van de gelezen tekst toevoegen.")

        # Een volledig lege starttabel (geen vooringevulde L7-F data meer!)
        empty_data = [
            {
                "Voorschrift Nr.": "",
                "Verplichting / Actie": "",
                "Termijn": "",
                "Ontvanger / Instantie": ""
            }
        ]
        
        df_empty = pd.DataFrame(empty_data)

        # We tonen een schone tabel
        st.info("Tip: Gebruik de tekst hierboven om de verplichtingen uit je nieuwe vergunning te lezen.")
        st.dataframe(df_empty, use_container_width=True)

else:
    st.info("👈 Upload ten minste een PDF-bestand via de zijbalk om de applicatie te starten.")
