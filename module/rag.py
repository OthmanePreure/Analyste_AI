from call_api import APIClient
from module.utils import to_unix_epoch
from database.chromadb_handler import DatabaseHandler

class RAG:
    def __init__(self, client, name_collection):
        self.client = client
        self.db_handler = DatabaseHandler(client, name_collection)
    def rag_question(self, arguments, question):

        try :
            retrival_response = self.db_handler.augmented_search_per_date(question, arguments,20)
            if not isinstance(retrival_response,str):    
                documents = retrival_response['documents'][0]
                documents_text = "\n\n".join([f"## Incident : {i+1}\n{doc}" for i, doc in enumerate(documents)])   # si documents est une liste de strings

            else :
                documents_text = retrival_response or "aucune reponse trouvé"

            user_prompt = f"""Voici la question :  
            {question}

        Voici les documents pertinents à consulter :
        {documents_text}

        """

            return user_prompt
    
        except Exception as e: 
            print(f'erreur dans rag_question : {e}')
            return 'probleme dans la recherche augmenté'    
if __name__=="__main__":
    from dotenv import load_dotenv
    import os
    import yaml
    from database.chromadb_handler import DatabaseHandler
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY_OTHMANE")
    client = APIClient("", "", api_key)

    # Charger un fichier YAML
    with open(r"C:\Users\9510156B\agent_ai\config\agent_config.yaml", "r") as file:
        prompt = yaml.safe_load(file)

    db_handler = DatabaseHandler(client, "my_collection")

    system_orchestrator_prompt = prompt['orchestrator_prompt']

    prompts_cause_perf = prompt['prompts_cause_perf']
    Prompt_ponctu = prompt['Prompt_ponctu']
    prompt_rag = prompt['prompt_rag']

    tools = [
    {"type": "function", "function": prompts_cause_perf},
    {"type": "function", "function": Prompt_ponctu},
    {"type": "function", "function": prompt_rag}

]   
    
    rag = RAG(client)
    question = "listes moit tout les incidents concernant des derangement d'installations le 06 mai 2025"
    response = client.call_api(system_orchestrator_prompt, question, tools)
    rag.rag_question(response, question)
    import json
    arguments = json.loads(response.choices[0].message.tool_calls[0].function.arguments)

    #mettre les dates au format time_stamp 
    
    
    print()