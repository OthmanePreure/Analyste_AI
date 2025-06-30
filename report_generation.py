from database.sql_handler import SQLHandler
from datetime import datetime, timedelta
from call_api import APIClient
from dotenv import load_dotenv
import os
import yaml 
import configparser
from markdown_interpreter import markdown_to_docx
from test import declanche

config = configparser.ConfigParser()
config.read("config/settings.config")  

prompt_path = config['PATH']['prompt']
# Ouvrir et charger le fichier YAML
with open(prompt_path, "r", encoding="utf-8") as file:
    prompt = yaml.safe_load(file)

load_dotenv()

API_KEY = os.getenv('OPENAI_API_KEY_SNCF')
COMPLETION_ENDPOINT = os.getenv('ENDPOINT_COMPLETION')


class ReportGeneration: 
    def __init__(self):
        self.sql_client = SQLHandler()
        self.client = APIClient(COMPLETION_ENDPOINT, "", API_KEY)
        self.system_report_prompt = prompt['system_report_prompt']
        self.system_synthese_prompt1 = prompt['system_synthese1_prompt']
        self.system_synthese_prompt2 = prompt['system_synthese2_prompt']
        self.system_synthese_prompt_np = prompt['system_synthese_np_prompt']

    def report_gen(self, args):
        weeks = self.split_weeks(args["start_date"], args["end_date"])
        all_markdown = ""
        synhtese_first_step = ""
        for i, week in enumerate(weeks, 1):
            start_date, end_date = week
            arguments = {
                "start_date": start_date,
                "end_date": end_date,
                "class_cause": args.get('class_cause')
            }
            documents = self.sql_client.get_data(arguments)
            user_prompt = self.struct_prompt(documents, start_date, end_date)
            #model_response = self.client.call_api(self.system_report_prompt, user_prompt)
            model_response2 = self.client.call_api(self.system_synthese_prompt1, user_prompt)

            #all_markdown += model_response.choices[0].message.content
            #all_markdown += "\n\n"

            synhtese_first_step += model_response2.choices[0].message.content
            synhtese_first_step += "\n\n"

        response2 = self.client.call_api(self.system_synthese_prompt2, synhtese_first_step)
        synthese_final = response2.choices[0].message.content

        evolution_np = declanche()
        response_evolution = self.client.call_api(self.system_synthese_prompt_np, evolution_np)
        evolution = response_evolution.choices[0].message.content
        
        synhtese_first_step += "\n\n" + evolution
        
        response2 = self.client.call_api(self.system_synthese_prompt2, synhtese_first_step)
        synthese_final = response2.choices[0].message.content

        #markdown_to_docx(all_markdown,report)
        markdown_to_docx(synthese_final, "synthese.docx")


    # Une fois toutes les réponses récupérées, on crée le docx

    def struct_prompt(self, documents, start_date, end_date):
        user_prompt = f"Voici la liste d'incident allant du {start_date} au {end_date} : \n\n {documents}"
        return user_prompt



    def split_weeks(self,start_date_str, end_date_str):
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        semaines = []
        current_start = start_date

        while current_start <= end_date:
            current_end = current_start + timedelta(days=6)
            if current_end > end_date:
                current_end = end_date  # Ne dépasse pas la fin réelle

            semaines.append((
                current_start.strftime("%Y-%m-%d"),
                current_end.strftime("%Y-%m-%d")
            ))

            current_start = current_end + timedelta(days=1)

        return semaines

    
    

if __name__=="__main__":
    gen = ReportGeneration()
    args = {"start_date": "2025-01-01", "end_date": "2025-05-18", "class_cause": "reseau"}
    gen.report_gen(args)