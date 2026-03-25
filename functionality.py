# importing required libraries
import re
from datetime import datetime, timezone

powiazane_nipy = ["7492107657", "7492095718", "7491130950"]

forma_platnosci_do_numberow_ksef = {
    "gotówka": 1,
    "karta": 2,
    "bon": 3,
    "czek": 4,
    "kredyt": 5,
    "przelew": 6,
    "mobilna": 7}


def napraw_polskie_znaki(tekst):
    mapa_znakow = {
        "l/": "ł", "L/": "Ł",
        "/l": "ł", "/L": "Ł",
        "'z": "ź", "'Z": "Ź",
        "'c": "ć", "'C": "Ć",
        "'s": "ś", "'S": "Ś",
        "'n": "ń", "'N": "Ń",
        "'o": "ó", "'O": "Ó", 
        ".z": "ż", ".Z": "Ż",
        ",a": "ą", ",A": "Ą",
        ",e": "ę", ",E": "Ę"
    }

    nowy_tekst = tekst
    for kod, polski_znak in mapa_znakow.items():
        nowy_tekst = nowy_tekst.replace(kod, polski_znak)
        
    return nowy_tekst

def napraw_niedozwolone_znaki(tekst):
    tekst = tekst.replace("&", "&amp;")
    tekst = tekst.replace("<", "&lt;")
    tekst = tekst.replace(">", "&gt;")
    return tekst

def dane_firmy(txt):
    try:
        x = re.findall("Nabywca[\s\S]*?Forma", txt)[0].split("\n")
        x = x[:-1]
        nip = x[0].split()[-1].replace("-", "")
    except:
        nip = -1
    try:
        nazwa = napraw_polskie_znaki(x[1])
        adres = napraw_polskie_znaki(x[2])
        miasto = " ".join(re.findall("..-...*", adres)[0].split()[1:]).strip()
        kod_pocztowy = re.findall("..-...", adres)[0]
        ul = " ".join(re.findall("ul.*..-...", adres)[0].split()[:-1]).replace(".", ". ")
        pelny_adres = ul + " " + miasto + " " + kod_pocztowy + " " + miasto
    except:
        pelny_adres = ""
        nazwa = ""
    return {"nip": nip, "nazwa": nazwa, "adres": pelny_adres}


def informacje_faktury(txt):
    try:
        numer_fv = re.findall("Faktura VAT numer:.*", txt)[0].split()[-1]
    except:
        numer_fv = -1
    try:
        data_wystawienia = re.findall("Data wystawienia:.*", txt)[0].split()[-1].replace("/", "-")
    except:
        data_wystawienia = -1
    try:
        ceny = re.findall("\|Razem\|.*", txt)[0].strip().split("|")
    except:
        ceny = -1
    try:
        cena_brut = ceny[-2].strip().replace(",", "")
        vat = ceny[-3].strip().replace(",", "")
        cena_net = ceny[-4].strip().replace(",", "")
    except:
        cena_brut = -1
        vat = -1
        cena_net = -1
    try:
        forma_platnosci = re.findall("Forma\s*płatności:.*? ", txt)[0].split()[-1].split(":")[-1]
    except:
        forma_platnosci = -1
    try:
        termin_platnosci = re.findall("Termin\s*płatności:.*? ", txt)[0].split()[-1].split(":")[-1].replace("/", "-")
    except:
        termin_platnosci = -1
    try:
        uwagi = "".join(re.findall("Uwagi:.*", txt)[0].split(":")[1::])
    except:
        uwagi = -1
    try:
        zaplacone = 1 if "z a p ł a c o n o" in txt else 0
    except:
        zaplacone = -1
    return {"data_wystawienia": data_wystawienia, "numer_fv": numer_fv, "cena_net": cena_net, "vat": vat, "cena_brut": cena_brut, "forma_platnosci": forma_platnosci, "termin_platnosci": termin_platnosci, "zaplacone": zaplacone, "uwagi": uwagi}


def wczytywanie_listy_towarów_plubmer(txt):
    xy = re.findall("\|.\d+\|.*", txt)
    spis_towarow = []
    konflikty = []
    opisy = ["lp", "nazwa", "kod", "ilosc", "jednostka", "cena_jed_netto", "wartosc_netto", "vat", "pkwiu", "rabat"]
    index_do_zmian = [3, 5, 6, 7]
    for x in xy:
        if len(x.split("|")) == 11:
            splited = x.split("|")
            lp = splited[1].strip()
            nazwa = splited[2].strip()
            kod = splited[3].strip()
            ilosc = splited[4].strip().split()[0].strip().replace(",", "")
            jm = splited[4].strip().split()[1].strip()
            cena_net = splited[5].strip().replace(",", "")
            wart_net = splited[6].strip().replace(",", "")
            vat = splited[7].strip().replace(",", "")
            pkwiu = splited[8].strip()
            rabat = splited[9].strip()
            spis_towarow.append({"lp": lp, "nazwa": nazwa, "kod": kod, "ilosc": ilosc, "jednostka": jm, "cena_jed_netto": cena_net, "wartosc_netto": wart_net, "vat": vat, "pkwiu": pkwiu, "rabat": rabat})

        elif len(x.split("|")) != 11:
            i = 0
            towar = {}
            konflikty.append(x.split("|")[1])
            try:
                for s in x.split("|"):
                    if s.strip() != "":
                        s = s.strip()
                        splitted = s.split("  ")
                        if len(splitted) == 1:
                            if i in index_do_zmian:
                                towar[opisy[i]] = splitted[0].strip().replace(",", "")
                            else:
                                towar[opisy[i]] = splitted[0].strip()    
                            i += 1
                        elif len(splitted) != 1:
                            for s in splitted:
                                if s.strip() != "":
                                    if i in index_do_zmian:
                                        towar[opisy[i]] = s.strip().replace(",", "")
                                    else:
                                        towar[opisy[i]] = s.strip()
                                    i += 1
                spis_towarow.append(towar)
            except:
                spis_towarow.append({"lp": -1, "nazwa": -1, "kod": -1, "ilosc": -1, "jednostka": -1, "cena_jed_netto": -1, "wartosc_netto": -1, "vat": -1, "pkwiu": -1, "rabat": -1})

    return spis_towarow,konflikty


def dane_do_xml(dane_firmy, spis_towarow, informacje_faktury):
    now = datetime.now(timezone.utc)
    result = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    data_wystawienia = now.strftime("%Y-%m-%d")
    xml = f"""<Faktura xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
        <Naglowek>
        <KodFormularza kodSystemowy="FA (3)" wersjaSchemy="1-0E">FA</KodFormularza>
        <WariantFormularza>3</WariantFormularza>
        <DataWytworzeniaFa>{result}</DataWytworzeniaFa>
        <SystemInfo>Spersonalizowana aplikacja pod Hurtownia Elektryczna PEKRA BL</SystemInfo>
        </Naglowek>
        <Podmiot1>
            <DaneIdentyfikacyjne>
                <NIP>7491248893</NIP>
                <Nazwa>Adrian Jakubczyk Hurtownia Elektryczna PEKRA BL</Nazwa>
            </DaneIdentyfikacyjne>
            <Adres>
                <KodKraju>PL</KodKraju>
                <AdresL1>
                ul. Przyjaźni 54 Kędzierzyn-Koźle 47-225 Kędzierzyn-Koźle
                </AdresL1>
            </Adres>
        </Podmiot1>
        <Podmiot2>
            <DaneIdentyfikacyjne>
                <NIP>{dane_firmy['nip']}</NIP>
                <Nazwa>
                {napraw_niedozwolone_znaki(dane_firmy['nazwa'])}
                </Nazwa>
            </DaneIdentyfikacyjne>
            <Adres>
                <KodKraju>PL</KodKraju>
                <AdresL1>{napraw_niedozwolone_znaki(dane_firmy['adres'])}</AdresL1>
            </Adres>
        <JST>2</JST>
        <GV>2</GV>
        </Podmiot2>
        <Fa>
        <KodWaluty>PLN</KodWaluty>
        <P_1>{data_wystawienia}</P_1>
        <P_2>{informacje_faktury['numer_fv']}</P_2>
        <P_13_1>{informacje_faktury['cena_net']}</P_13_1>
        <P_14_1>{informacje_faktury['vat']}</P_14_1>
        <P_15>{informacje_faktury['cena_brut']}</P_15>
            <Adnotacje>
            <P_16>2</P_16>
            <P_17>2</P_17>
            <P_18>2</P_18>
            <P_18A>2</P_18A>
                <Zwolnienie>
                    <P_19N>1</P_19N>
                </Zwolnienie>
                <NoweSrodkiTransportu>
                    <P_22N>1</P_22N>
                </NoweSrodkiTransportu>
            <P_23>2</P_23>
                <PMarzy>
                <P_PMarzyN>1</P_PMarzyN>
                </PMarzy>
            </Adnotacje>
        <RodzajFaktury>VAT</RodzajFaktury>
        """
    if dane_firmy['nip'] in powiazane_nipy:
        xml += f"""
        <TP>1</TP>
     """
    for towar in spis_towarow:
        xml += f"""
            <FaWiersz>
                <NrWierszaFa>{towar['lp']}</NrWierszaFa>
                <P_7>{napraw_niedozwolone_znaki(towar['nazwa'])}</P_7>
                <P_8A>{towar['jednostka']}</P_8A>
                <P_8B>{towar['ilosc'].replace(",", "")}</P_8B>
                <P_9A>{towar['cena_jed_netto'].replace(",", "")}</P_9A>
                <P_11>{towar['wartosc_netto'].replace(",", "")}</P_11>
                <P_12>23</P_12>
            </FaWiersz>
        """
    if informacje_faktury["zaplacone"] == 1 or forma_platnosci_do_numberow_ksef[informacje_faktury['forma_platnosci']] == 1:
        a = f"""<Zaplacono>1</Zaplacono>
                <DataZaplaty>{informacje_faktury['termin_platnosci']}</DataZaplaty>
        
        """
    else:
        a = f"""<TerminPlatnosci>
                <Termin>{informacje_faktury['termin_platnosci']}</Termin>
                </TerminPlatnosci>"""
    xml += f"""
            <Platnosc>
                {a}
            <FormaPlatnosci>{forma_platnosci_do_numberow_ksef[informacje_faktury['forma_platnosci']]}</FormaPlatnosci>
                <RachunekBankowy>
                <NrRB>14102037140000490202780427</NrRB>
                <NazwaBanku>PKO Bank Polski SA</NazwaBanku>
                </RachunekBankowy>
            </Platnosc>
        </Fa>

        """
    if informacje_faktury["uwagi"] != "":
        xml += f"""
        <Stopka>
            <Informacje>
                <StopkaFaktury>
                Uwagi: {napraw_niedozwolone_znaki(informacje_faktury['uwagi'])}
                </StopkaFaktury>
            </Informacje>
        </Stopka>
        """
    xml += f"""
    </Faktura>
    """
    return xml


def sprawdz_poprawnosc(x: dict):
    a = []
    for key, value in x.items():
        if value == -1:
            a.append(key)
    return a