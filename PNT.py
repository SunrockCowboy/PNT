import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Paginastijling
st.set_page_config(page_title="Vergunning Verplichtingen Monitor", layout="wide")

st.title("📄 Vergunning Verplichtingen & Deadlines Monitor")
st.markdown("""
Upload hieronder de omgevingsvergunning (PDF), geef op op welke pagina's de voorschriften staan, 
en voer de **datum van inwerkingtreding** in. Het programma berekent automatisch de deadlines.
""")

# --- ZIJBALK VOOR INVOER ---
st.sidebar.header("1. Configuratie & Pagina's")
uploaded_file = st.sidebar.file_uploader("Upload Omgevingsvergunning (PDF)", type=["pdf"])

# Veld om paginabereik van de voorschriften op te geven (nu leeg als standaard)
paginas_input = st.sidebar.text_input(
    "Pagina's met voorschriften", 
    value="", 
    placeholder="Bijv. 48-57 of 30,35,40-45",
    help="Vul hier het paginabereik in waar de voorschriften in deze specifieke vergunning staan."
)

# Datum van inwerkingtreding
default_date = datetime.strptime("2026-06-12", "%Y-%m-%d").date()
inwerking_date = st.sidebar.date_input("Datum van inwerkingtreding", value=default_date)

st.sidebar.markdown("---")
st.sidebar.info("Tip: Controleer eerst in de PDF op welke pagina's de voorschriften beginnen en eindigen en vul dat hierboven in.")

# Functie om paginabereik string om te zetten naar een lijst van Paginanummers (0-based index)
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
    # PDF inlezen
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        
        # Bepaal welke pagina's geselecteerd zijn
        target_pages = parse_page_ranges(paginas_input, total_pages)
        
        full_text = ""
        voorschriften_text = ""
        
        for idx, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n--- PAGINA {idx + 1} ---\n" + text
                if idx in target_pages:
                    voorschriften_text += f"\n--- PAGINA {idx + 1} ---\n" + text

    # Waarschuwing als er nog geen pagina's zijn ingevuld
    if not paginas_input.strip():
        st.warning("⚠️ Vul aan de linkerkant in de zijbalk in op welke pagina's de voorschriften staan om de gerichte tekst te bekijken.")
    else:
        st.success(f"PDF succesvol geladen ({total_pages} pagina's). Analyse gericht op geselecteerde pagina's: **{paginas_input}**.")

    # Bepaal deadlines op basis van inwerkingtreding
    deadline_zzs = inwerking_date + relativedelta(months=6)
    deadline_lucht_overzicht = inwerking_date + relativedelta(years=1)
    
    end_of_year = datetime(inwerking_date.year, 12, 31).date()
    deadline_jaarrapportage = end_of_year + relativedelta(months=3)

    # Tabel met periodieke/termijngebonden verplichtingen
    data = [
        {
            "Voorschrift": "Voorschrift 15.1",
            "Verplichting": "Indienen vermijdings- en reductieprogramma ZZS (art. 5.24 Bal)",
            "Termijn": "Binnen 6 maanden na inwerkingtreding",
            "Berekende Deadline": deadline_zzs.strftime('%d-%m-%Y'),
            "Ontvanger": "Bevoegd Gezag"
        },
        {
            "Voorschrift": "Voorschrift 15.1",
            "Verplichting": "Eerste informatieverstrekking ZZS (art. 5.23 Bal - afwijkende termijn)",
            "Termijn": "Binnen 6 maanden na inwerkingtreding",
            "Berekende Deadline": deadline_zzs.strftime('%d-%m-%Y'),
            "Ontvanger": "Bevoegd Gezag"
        },
        {
            "Voorschrift": "Voorschrift 12.4",
            "Verplichting": "Opstellen overzicht emissies naar de lucht (methaan, benzeen, etc.)",
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

    st.subheader("📅 Overzicht berekende deadlines")
    st.dataframe(df, use_container_width=True)

    # Optie om data te exporteren naar CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download berekend overzicht als CSV",
        data=csv,
        file_name=f"vergunning_deadlines_{inwerking_date}.csv",
        mime='text/csv',
    )

    # Weergave van de geselecteerde voorschriften-tekst (indien ingevuld)
    if paginas_input.strip():
        with st.expander(f"🔍 Bekijk geëxtraheerde tekst van de opgegeven voorschriften-pagina's ({paginas_input})"):
            st.text_area("Voorschriften tekst", voorschriften_text, height=300)

else:
    st.info("👈 Upload ten minste een PDF-bestand via de zijbalk om de applicatie te starten.")
