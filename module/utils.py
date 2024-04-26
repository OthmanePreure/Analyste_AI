import json
import os
from datetime import date, datetime
import re
import unicodedata
import pandas as pd

def normalize(text):
    if pd.isna(text):
        return text
    text = str(text).lower().replace(' ', '_')
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )



def get_today_date():
    return date.today()



def date_instruction():
    d = date.today()
    
    date_instruction = f"Keep in mind that today's date is {d}. Use this date if needed in your responses. \n"
    
    return date_instruction




def to_unix_epoch(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())




def clean_text(texte):

    # Supprimer <DEC> + ID
    texte = re.sub(r'<DEC>[\w\d]+', '', texte)

    # Supprimer les URLs
    texte = re.sub(r'https?://\S+', '', texte)

    # Supprimer les balises comme --NOPANIC--
    texte = re.sub(r'--\w+--', '', texte)

    # Met en minuscules
    texte = texte.lower()

    # Normalisation des noms de lignes RER et Transilien
    normalisation_lignes = {
        r"\brer\s*[-]?\s*a\b": "rer_a",
        r"\brer\s*[-]?\s*b\b": "rer_b",
        r"\brer\s*[-]?\s*c\b": "rer_c",
        r"\brer\s*[-]?\s*d\b": "rer_d",
        r"\brer\s*[-]?\s*e\b": "rer_e",
        r"\bligne\s*[-]?\s*h\b": "ligne_h",
        r"\bligne\s*[-]?\s*j\b": "ligne_j",
        r"\bligne\s*[-]?\s*k\b": "ligne_k",
        r"\bligne\s*[-]?\s*l\b": "ligne_l",
        r"\bligne\s*[-]?\s*n\b": "ligne_n",
        r"\bligne\s*[-]?\s*p\b": "ligne_p",
        r"\bligne\s*[-]?\s*r\b": "ligne_r",
        r"\bligne\s*[-]?\s*u\b": "ligne_u",
    }

    for pattern, canonique in normalisation_lignes.items():
        texte = re.sub(pattern, canonique, texte)
    # Supprimer les caractères indésirables mais garder accents, chiffres, lettres, ponctuations utiles
    texte = re.sub(r"[^a-zA-ZÀ-ÿ0-9\s,.\-:/_'’]", '', texte)

    # Nettoyage des espaces multiples
    texte = re.sub(r"\s+", " ", texte)

    return texte.strip()