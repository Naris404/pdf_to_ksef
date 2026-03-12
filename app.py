import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from requests import get
import os
from pypdf import PdfReader
from time import sleep

from fucntionality import (
    napraw_polskie_znaki,
    dane_firmy,
    informacje_faktury,
    wczytywanie_listy_towarów_plubmer,
    sprawdz_poprawnosc,
    dane_do_xml
)


load_dotenv()
api_key = os.getenv("API_KEY")


st.title("Przetwarzanie PDF do KSeF 📑")

# --- SEKCJA 1: UPLOAD PLIKU ---
st.header("Prześlij swoje pliki PDF")
uploaded_files = st.file_uploader("Wybierz plik PDF z dysku", type=["pdf"], accept_multiple_files=True)

if uploaded_files is not None:
    for uploaded_file in uploaded_files:
        sleep(1)
        # Tutaj możesz dodać logikę przetwarzania pliku
        st.success(f"Pomyślnie przesłano plik: {uploaded_file.name}")
        reader = PdfReader(uploaded_file)
        txt = ""
        # creating a page object
        for page in reader.pages:
            txt += page.extract_text()
        txt = napraw_polskie_znaki(txt)

        inf_faktury = informacje_faktury(txt)
        inf_faktury["nip"] = -1
        brakujace_pola = sprawdz_poprawnosc(inf_faktury)
        if brakujace_pola:
            for pole in brakujace_pola:
                inf_faktury[pole] = st.text_input(f"Brakuje mi pola {pole}. Proszę uzupełnij:", key=f"input-{pole}")
        print(inf_faktury["nip"])
        dane_firmowe = dane_firmy(txt)
        brakujace_pola = sprawdz_poprawnosc(dane_firmowe)
        if brakujace_pola:
            for pole in brakujace_pola:
                dane_firmowe[pole] = st.text_input(f"Brakuje mi pola {pole}. Proszę uzupełnij:", key=f"input-{pole}")
        spis_towarow,konflikty = wczytywanie_listy_towarów_plubmer(txt)
        brakujace_pola = sprawdz_poprawnosc(spis_towarow)
        if brakujace_pola:
            i = 0
            for pole in brakujace_pola:
                st.header(f"Pozycja numer {int(konflikty[i]) + 1}")
                spis_towarow[int(konflikty[i]) + 1][pole] = st.text_input(f"Brakuje mi pola {pole}. Proszę uzupełnij:", key=f"input-{pole}")
                i += 1
        nip = dane_firmowe["nip"]

        response = get(
            f'https://dataport.pl/api/v1/company/{nip}',
            params={'format': 'simple'},
            headers={
                'X-API-Key': api_key,
                'Accept': 'application/json'
            }
        )

        data = response.json()

        plik_wyjsciowy = dane_do_xml(data, spis_towarow[0], inf_faktury)

        numer_fv = inf_faktury["numer_fv"].replace("/", "_")
        
        # Symulacja danych wynikowych (np. tekst XML)
        result_data = plik_wyjsciowy.encode('utf-8')  # Konwersja tekstu na bytes
        st.download_button(
            key=f"download-{numer_fv}",
            label=f"Pobierz plik do KSeF ({numer_fv})",
            data=result_data,
            file_name=f"{numer_fv}.xml",
            mime="application/xml"
        )
else:
    st.info("Czekam na plik...")