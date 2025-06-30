from call_api import APIClient
import json
import hashlib
from uuid import uuid4
from module.utils import to_unix_epoch
from tqdm import tqdm
from module.utils import clean_text
from database.chromadb_handler import SetDatabase
from database.sql_handler import SQLHandler



class DataIngestion:
    def __init__(self, client: APIClient, prompt: str):
        self.prompt = prompt
        self.openai_client = client
        self.sql_client = SQLHandler()
        self.sql_client.create_table()
        self.cause_reseau = [
    'GR-GI', 'SGTC', 'SIL', 'AG-MAINT', 'CATEN', 'EALE', 'EM-MAINT', 'INFOR',
    'LTV-I', 'PN', 'SIGNAL', 'TELECOM', 'VOI', 'TVX-AG', 'TVX-P', 'TVX-RT',
    'LTV', 'EX', 'EX-EF', 'ENQUETE', 'IND-VOI', 'MANIF', 'OBST', 'ACC',
    'COLI-GI', 'MALV-GI', 'METEO'
]    
    
    def modele_clean_text(self, text):
        text = clean_text(text)
        system_prompt = self.prompt['system_clean_text_prompt']
        user_prompt = 'Voici le texte a netoyer : \n\n ' + text
        response = self.openai_client.call_api3(system_prompt, user_prompt)
        cleaned_text = response.choices[0].message.content
        return cleaned_text
    

    
    def entites_extraction(self, texte):
        system_prompt = self.prompt["extraction_entites"]["system_prompt"]
        
        user_prompt = f"""Voici un commentaire d'incident :
                        \"\"\"{texte}\"\"\"
                        """

        try:
            response = self.openai_client.call_api2(system_prompt, user_prompt, None, {"type": "json_object"})
            json_response = json.loads(response)
            if "date" in json_response:
                json_response['date'] = to_unix_epoch(json_response['date'])
            return json_response
        except Exception as e:
            print(f"Erreur extraction : {e}")
            return {}
        
    def add_colonne(self, df):
        for _, row in tqdm(df.iterrows()):
            heure_deb_inc = row.get('heure deb inc', None)
            if pd.isna(heure_deb_inc):
                # La date n'est pas valide, on passe à la ligne suivante
                continue

            date = heure_deb_inc.date().strftime("%Y-%m-%d")
            cause = row.get('cause', None)

            # Déterminer class_cause
            class_cause = "reseau" if cause in self.cause_reseau else "transilien"

            lieu_incident = row.get('Lieu', "Lieu non précisé")
            nombre_incident = int(row.get('nb voy retardés', 0))

            # Nettoyer part_non_ponctu
            part_non_ponctu = row.get('Part de la non ponctu ', 0)
            if isinstance(part_non_ponctu, str):
                part_non_ponctu = float(part_non_ponctu.replace('%', '').replace(',', '.'))

            # Construire les valeurs à mettre à jour
            valeurs = {
                "cause": cause,
                "class_cause": class_cause,
                "lieu": lieu_incident,
                "part_non_ponctu_float": part_non_ponctu
            }

            self.sql_client.add_new_value(valeurs, date, nombre_incident)

        
    def ingestion_vectordb(self, df):
        
        data_setter = SetDatabase(client, 'incident_db')
        
        hash_list = []

        for index, row in tqdm(df.iterrows()):

            texte_brut = str(row.get('commentaire', '')).strip()
                
            if not texte_brut or texte_brut == "Incident fictif":
                continue

            text_cleaned = self.modele_clean_text(texte_brut)

            heure_deb_inc = row.get('heure deb inc', None)
            if pd.isna(heure_deb_inc):
                # La date n'est pas valide, on passe à la ligne suivante
                continue
            
            nombre_incident = int(row.get('nb voy retardés', '0'))

            part_non_ponctu = row.get('Part de la non ponctu ', 0)
            part_non_ponctu = float(part_non_ponctu.replace('%', '').replace(',', '.'))

            # Si on arrive ici, la date est valide
            date = heure_deb_inc.date().strftime("%Y-%m-%d")

           
            #mettre les données dans sql database


            text_cleaned +=  f" \n\n- Date de l'incident : {date} "
            text_cleaned +=  f" \n\n- Nombre de passagers impacté : {nombre_incident} personnes "
            text_cleaned += f"\n\n- Part de la non ponctualité de l'incident : {part_non_ponctu}" 



            id = hashlib.sha256(text_cleaned.encode("utf-8")).hexdigest()
            data['ids'] = id
            
            
            if id in hash_list:
                continue


            print("index numero : ", index)
            


            data['documents'].append(text_cleaned)
            
            metadata = data_ingestion.entites_extraction(text_cleaned)



            print("metadata ############################ \n", metadata )

            print('\n #######################################################')
            data['metadatas'].append(metadata)    

            embeddings = data_ingestion.generer_embeddings([text_cleaned])[0]
            
            data['embeddings'].append(embeddings)

            hash_list.append(id)
            
            results = data_setter.index_data(text_cleaned, embeddings, metadata)



    def generer_embeddings(self,textes):

        return self.openai_client.vectorizer2(textes)




if __name__ == "__main__":


    from datetime import datetime

    from dotenv import load_dotenv
    import os
    import pandas as pd
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY_OTHMANE")
    client = APIClient("", "", api_key)

    import yaml


    data = {"documents": [], "embeddings": [], "metadatas": []}
    # Charger le fichier YAML
    with open("c:\\Users\\9510156B\\agent_ai\\config\\agent_config.yaml", "r", encoding="utf-8") as file:
        prompts = yaml.safe_load(file)

    data_ingestion = DataIngestion(client, prompts)




    path = r'C:\Users\9510156B\agent_ai\topn'
    list_top_n = os.listdir(path)

    for top_n_path in tqdm(list_top_n) : 


        print("Fichier en cours de traitement : ", top_n_path)
        print()
        complete_path = os.path.join(path, top_n_path)
        

        df = pd.read_excel(complete_path)
        df = df.iloc[:-3, :]
        df.dropna(subset=['commentaire'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        data_ingestion.add_colonne(df)

        with open("mon_fichier.txt", "a", encoding="utf-8") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{now}] Fichier traité : {top_n_path}\n")

