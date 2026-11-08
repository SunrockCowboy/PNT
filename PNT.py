import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Paginastijling
st.set_page_config(page_title="Vergunning Verplichtingen Monitor", layout="wide")

st.title("📄 Permit Notification Tool©")
st.markdown("""
Upload hieronder de omgevingsvergunning (PDF) en voer de **datum van inwerkingtreding** in. 
Het programma berekent automatisch op basis van de voorschriften wanneer specifieke acties en rapportages moeten zijn ingediend.
""")

# --- ZIJBALK VOOR INVOER ---
st.sidebar.header("1. Vergunning Configuratie")
uploaded_file = st.sidebar.file_uploader("Upload Omgevingsvergunning (PDF)", type=["pdf"])

# Standaarddatum op 12 juni 2026 (zoals in de vergunning)
default_date = datetime.strptime("2026-06-12", "%Y-%m-%d").date()
inwerking_date = st.sidebar.date_input("Datum van inwerkingtreding", value=default_date)

st.sidebar.markdown("---")
st.sidebar.info("Tip: Dit hulpmiddel leest de vaste wettelijke en vergunninggebonden termijnen uit Bijlage 1 en rekent deze direct voor je uit.")

# --- HOOFDSCHERM ---
if uploaded_file is not None:
    # PDF inlezen en tekst extraheren
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    st.success(f"PDF succesvol geladen ({total_pages} pagina's gedetecteerd). Inwerkingtreding vastgesteld op: **{inwerking_date.strftime('%d-%m-%Y')}**")

    # Bepaal deadlines op basis van inwerkingtreding
    deadline_zzs = inwerking_date + relativedelta(months=6)
    deadline_lucht_overzicht = inwerking_date + relativedelta(years=1)
    
    # Einde van het eerste kalenderjaar voor de jaarlijkse rapportage
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

    # Uitgebreide tekstweergave optie
    with st.expander("🔍 Bekijk volledige tekst van Bijlage 1 (Voorschriften) uit de PDF"):
        st.text_area("Geëxtraheerde PDF-inhoud", full_text, height=300)

else:
    st.info("👈 Upload ten minste een PDF-bestand via de zijbalk om de applicatie te starten.")