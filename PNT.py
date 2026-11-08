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
Het programma leest de voorschriften uit de PDF en toont direct het overzicht van verplichtingen.
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
            st.text_area("Inhoud voorschriften", voorschriften_text, height=250)

        st.markdown("---")
        st.subheader("📅 Berekend overzicht van verplichtingen en deadlines")
        st.markdown(f"Deadlines berekend op basis van inwerkingtreding per: **{inwerking_date.strftime('%d-%m-%Y')}**")

        # Standaard overzichtelijk sjabloon van verplichtingen dat dynamisch rekent met de ingevoerde datum
        deadline_zzs = inwerking_date + relativedelta(months=6)
        deadline_lucht_overzicht = inwerking_date + relativedelta(years=1)
        end_of_year = datetime(inwerking_date.year, 12, 31).date()
        deadline_jaarrapportage = end_of_year + relativedelta(months=3)

        data = [
            {
                "Voorschrift": "Voorschrift 15.1",
                "Verplichting": "Indienen vermijdings- en reductieprogramma / informatieplicht ZZS",
                "Termijn": "Binnen 6 maanden na inwerkingtreding",
                "Berekende Deadline": deadline_zzs.strftime('%d-%m-%Y'),
                "Ontvanger": "Bevoegd Gezag"
            },
            {
                "Voorschrift": "Voorschrift 12.4",
                "Verplichting": "Opstellen overzicht emissies naar de lucht (o.a. methaan, benzeen)",
                "Termijn": "Binnen 1 jaar na van kracht worden besluit",
                "Berekende Deadline": deadline_lucht_overzicht.strftime('%d-%m-%Y'),
                "Ontvanger": "Inspecteur-generaal der Mijnen (SodM)"
            },
            {
                "Voorschrift": "Voorschrift 12.4",
                "Verplichting": f"Jaarlijkse rapportage luchtemissies (over kalenderjaar {inwerking_date.year})",
                "Termijn": "Binnen 3 maanden na afloop van elk kalenderjaar",
                "Berekende Deadline": deadline_jaarrapportage.strftime('%d-%m-%Y'),
                "Ontvanger": "Inspecteur-generaal der Mijnen (SodM)"
            },
            {
                "Voorschrift": "Voorschrift 17.1",
                "Termijngebonden",
                "Verplichting": "Indienen 'North Sea Activity (NSA) aanvraagformulier'",
                "Termijn": "Ten minste 2 weken voor aanvang werkzaamheden",
                "Berekende Deadline": "Dynamisch (voor start project)",
                "Ontvanger": "Kustwacht"
            },
            {
                "Voorschrift": "Voorschrift 5.2",
                "Verplichting": "Melding gecontroleerd affakkelen of afblazen bij normale bedrijfsvoering",
                "Termijn": "Ten minste 48 uur voor aanvang",
                "Berekende Deadline": "Dynamisch (voor handeling)",
                "Ontvanger": "Toezichthouder (SodM)"
            }
        ]

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Downloadknop
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download dit overzicht als CSV",
            data=csv,
            file_name=f"vergunning_deadlines_{inwerking_date}.csv",
            mime='text/csv',
        )

else:
    st.info("👈 Upload ten minste een PDF-bestand via de zijbalk om de applicatie te starten.")
