import json
import gradio as gr
from module.generate_figure import Figure
from module.cause_perf import CausePerf
from module.rag import RAG
from module import utils
import pandas as pd
import json
import matplotlib.pyplot as plt
import yaml
import configparser
from dotenv import load_dotenv
import os
from call_api import APIClient
from database.sql_handler import SQLHandler

#Charger les variables a partir du fichier .env
load_dotenv() 

#Charger le fichier config pour recuperer les chemins des fichiers

config = configparser.ConfigParser()
config.read("config/settings.config")  



# Chemin vers les fichiers
non_ponctu_path = config["PATH"]["non_ponctu"]
line_perf_path = config["PATH"]["line_perf"]
mapp_cause_path = config["PATH"]["map_cause"]
idf_path = config["PATH"]["idf"]
prompt_path = config["PATH"]["prompt"] 



# Ouvrir et charger le fichier YAML
with open(prompt_path, "r", encoding="utf-8") as file:
    prompt = yaml.safe_load(file)


# Charger les données
non_ponctu_df = pd.read_excel(non_ponctu_path)

line_perf_df = pd.read_csv(line_perf_path, sep=";")

with open(idf_path, "r", encoding="utf-8") as f:
    idf_dict = json.load(f)


# Carger la clés de l'api 
API_KEY = os.environ.get("OPENAI_API_KEY_SNCF")
ENDPOINT_COMPLETION = os.environ.get("ENDPOINT_COMPLETION")
ENDPOINT_EMBEDDINGS = os.environ.get("ENDPOINT_EMBEDDINGS")
COLLECTION = "incident_db"


#Instancier la classe qui traite les demande 
api = APIClient(ENDPOINT_COMPLETION, ENDPOINT_EMBEDDINGS, API_KEY)


# Initialiser la classe Figure avec les données
sqlhandler = SQLHandler()
fig = Figure(idf_dict, line_perf_df,sqlhandler)
cause_perf = CausePerf(non_ponctu_df)
rag = RAG(api, COLLECTION)





# Configuration d'OpenAI
system_message = prompt['orchestrator_prompt']
system_analye_perf_prompt = prompt["system_analye_perf_prompt"]
system_rag_prompt = prompt['system_rag_response_prompt']
system_top_n_prompt = prompt['system_top_n_prompt']



# Fonction qui génère les données de ponctualité
def get_punctuality_data(line_name, date_range):
    print(line_name)
    print(date_range)

#recuperer les promptes qui va diriger le comportement du moddele 

punctuality_function = prompt["prompts_cause_perf"]
top_causes_function = prompt["Prompt_ponctu"]
rag_tool = prompt['prompt_rag']
top_incident_tool = prompt['top_incidents_tool_prompt']


#Ajouter la date d'aujourd'hui 
punctuality_function['description'] += utils.date_instruction()
top_causes_function['description'] += utils.date_instruction()


tools = [
    {"type": "function", "function": punctuality_function},
    {"type": "function", "function": top_causes_function},
    {"type": "function", "function": rag_tool},
    {"type": "function", "function": top_incident_tool}

]


# Fonction pour gérer l'appel des outils de OpenAI
def handle_tool_call_o(message, question):
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    if function_name == "get_punctuality_data":

        # Appeler la fonction qui génère le graphique (c'est-à-dire ta méthode `show_figure`)
        plt_figure = fig.show_figure(arguments)
        return plt_figure, "image"

    elif function_name == "get_cause_perf":

        perf = cause_perf.get_perf(arguments)
        return perf, "text"
    

    elif function_name == "rag_tool":
         
        user_prompt = rag.rag_question(arguments, question)
        return  user_prompt, "rag"
    
    elif function_name == "get_top_incidents":
        
        top_n = sqlhandler.get_top_incidents(arguments)
        return top_n, 'top_incident'
        # Retourner le graphique à Gradio


def stream_response(model_response):
    response = ""
    for chunk in model_response:
        delta = chunk.choices[0].delta.content
        if delta:
            response += delta
            yield response, None


# Fonction de chat
def chat_o(question):
    # Appel à l'API pour obtenir la réponse
    response = api.call_api3(system_message, question, tools)
    
    # Si la réponse contient un appel à un outil, on génère le graphique
    if response.choices[0].finish_reason == "tool_calls":
        
        message = response.choices[0].message
        tools_response, type_response = handle_tool_call_o(message, question)
    
        if type_response == "image":
            # Si la réponse est une image, afficher l'image et masquer la zone de texte
            yield None, tools_response
            return  # stoppe la fonction ici
        elif type_response == "text":
            
            model_response = api.stream_model_response(system_analye_perf_prompt, str(tools_response))

            yield from stream_response(model_response)

        elif type_response == "rag" : 
            
            model_response = api.stream_model_response(system_rag_prompt, tools_response)
            
            yield from stream_response(model_response)
        
        elif type_response == "top_incident":
            model_response = api.stream_model_response(system_top_n_prompt, tools_response)
            
            yield from stream_response(model_response)
    else :
        return response.choices[0].message.content, None
    

def chat(question):
    response = api.call_api(system_message, question, tools)

    # Si l'IA appelle un outil (tool call)
    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tools_response, type_response = handle_tool_call_o(message, question)

        if type_response == "image":
            yield None, tools_response  # Affiche l'image, masque le texte
            return

        elif type_response in ["text", "rag", "top_incident"]:
            # Choisir le prompt selon le type
            prompt_map = {
                "text": system_analye_perf_prompt,
                "rag": system_rag_prompt,
                "top_incident": system_top_n_prompt,
            }
            selected_prompt = prompt_map[type_response]

            # Appel en streaming au modèle
            yield from api.stream_model_intern_response(selected_prompt, str(tools_response),"gpt-4o")


    else:
        # Cas normal : réponse directe sans appel d'outil
        answer = response.choices[0].message.content
        yield answer, None


with gr.Blocks(theme="soft", title = "Assistant Performance Ferroviaire") as interface:
    with gr.Row():
        with gr.Column():
            image_output = gr.Image(label="Ligne Perf", visible=True)
            input_box = gr.Textbox(label="Message", lines=5)
            submit_button = gr.Button("Envoyer")
        response_box = gr.Markdown(label="Réponse")  # <-- Utilisation de Markdown

    

    # Déclenchement par bouton
    submit_button.click(fn=chat, inputs=[input_box], outputs=[response_box, image_output])

    # Déclenchement par Entrée
    input_box.submit(fn=chat, inputs=[input_box], outputs=[response_box, image_output])

interface.launch()