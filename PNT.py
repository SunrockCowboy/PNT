import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Paginastijling
st.set_page_config(page_title="Vergunning Verplichtingen Monitor", layout="wide")

st.title("📄 Flexibele Vergunning Verplichtingen Monitor")
st.markdown("""
Upload je omgevingsvergunning (PDF), geef op op welke pagina's de voorschriften staan en stel de datum van inwerkingtreding in. 
Je kunt de lijst met verplichtingen hieronder direct aanpassen of aanvullen voor de specifieke vergunning die je hebt geüpload.
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
st.sidebar.info("Tip: Controleer eerst in de PDF op welke pagina's de voorschriften staan en lees de tekst mee in het uitklapmenu hiernaast.")

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
        with st.expander(f"📖 Lees de tekst van de voorschriften (Pagina {paginas_input}) om je verplichtingen te bepalen"):
            st.text_area("Inhoud voorschriften", voorschriften_text, height=250)

        st.markdown("---")
        st.subheader("📝 Overzicht verplichtingen en deadlines voor deze vergunning")
        st.markdown("Voeg hieronder verplichtingen toe of pas ze aan op basis van de tekst uit de geüploade vergunning. De deadlines worden automatisch berekend op basis van de inwerkingtreding (**sinds " + inwerking_date.strftime('%d-%m-%Y') + "**).")

        # Standaard lege of flexibele starttabel (geen hardgecodeerde L7-F rommel meer, maar een handige template)
        # Gebruiker kan dit direct aanpassen in de tabel!
        initial_data = [
            {
                "Voorschrift Nr.": "Voorschrift X.X",
                "Verplichting / Actie": "Voorbeeld: Indienen rapportage / uitvoeren meting",
                "Termijn omschrijving": "Bijv. Binnen 6 maanden na inwerkingtreding",
                "Type termijn": "Maanden na inwerkingtreding",
                "Aantal": 6,
                "Ontvanger / Instantie": "Bevoegd Gezag"
            },
            {
                "Voorschrift Nr.": "Voorschrift Y.Y",
                "Verplichting / Actie": "Voorbeeld: Jaarlijkse emissierapportage",
                "Termijn omschrijving": "Jaarlijks binnen 3 maanden na kalenderjaar",
                "Type termijn": "Jaarlijks",
                "Aantal": 0,
                "Ontvanger / Instantie": "Toezichthouder"
            }
        ]
        
        df_template = pd.DataFrame(initial_data)

        # Bewerkbare tabel in Streamlit
        edited_df = st.data_editor(
            df_template, 
            num_rows="dynamic", 
            use_container_width=True,
            help="Dubbelklik in cellen om de tekst aan te passen, of voeg onderaan een rij toe."
        )

        # Bereken automatisch deadlines op basis van wat de gebruiker invoert
        berekende_rows = []
        for index, row in edited_df.iterrows():
            termijn_type = row["Type termijn"]
            aantal = row["Aantal"]
            
            # Berekening op basis van type
            deadline_str = "N.v.t. / Handmatig"
            try:
                if termijn_type == "Maanden na inwerkingtreding":
                    dl = inwerking_date + relativedelta(months=int(aantal))
                    deadline_str = dl.strftime('%d-%m-%Y')
                elif termijn_type == "Jaren na inwerkingtreding":
                    dl = inwerking_date + relativedelta(years=int(aantal))
                    deadline_str = dl.strftime('%d-%m-%Y')
                elif termijn_type == "Jaarlijks":
                    end_of_year = datetime(inwerking_date.year, 12, 31).date()
                    dl = end_of_year + relativedelta(months=3)
                    deadline_str = dl.strftime('%d-%m-%Y') (Jaarlijks)
            except:
                deadline_str = "Controleer invoer"

            berekende_rows.append({
                "Voorschrift": row["Voorschrift Nr."],
                "Verplichting": row["Verplichting / Actie"],
                "Termijn": row["Termijn omschrijving"],
                "Berekende Deadline": deadline_str,
                "Ontvanger": row["Ontvanger / Instantie"]
            })

        st.markdown("### 📅 Berekend overzicht met actuele datums")
        final_df = pd.DataFrame(berekende_rows)
        st.dataframe(final_df, use_container_width=True)

        # Downloadknop
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download dit overzicht als CSV",
            data=csv,
            file_name=f"vergunning_deadlines_{inwerking_date}.csv",
            mime='text/csv',
        )

else:
    st.info("👈 Upload ten minste een PDF-bestand via de zijbalk om de applicatie te starten.")
