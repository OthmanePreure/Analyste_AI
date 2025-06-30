import requests
import os
from openai import OpenAI
import openai
from openai._exceptions import AuthenticationError
import numpy as np
from types import SimpleNamespace
import json

def api__key_valid(api_key: str) -> bool:
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()  
        return True
    except AuthenticationError:
        return False
    except Exception as e:
        print(f"Erreur OpenAI : {e}")
        return False



class APIClient:
    def __init__(self, endpoint_completion, endpoint_embeddings, api_key):



        self.endpoint_completion = endpoint_completion
        self.endpoint_embeddings = endpoint_embeddings
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        
    def call_api2(self, system_prompt, user_prompt,tools=None, response_format=None):

        try :
            completion = self.client.chat.completions.create(model="gpt-4o-mini"
                                                    , messages=[{'role': 'system', 'content': system_prompt},
                                                                {'role': 'user', 'content': user_prompt}],
                                                                response_format=response_format
                  
                                          )
        except Exception as e:
            raise ValueError(f"La clés API est invalide")

        generated_text = completion.choices[0].message.content
        return generated_text
    
    def call_api3(self, system_prompt, user_prompt,tools=None, response_format=None):

        try :
            response = self.client.chat.completions.create(model="gpt-4o-mini"
                                                    , messages=[{'role': 'system', 'content': system_prompt},
                                                                {'role': 'user', 'content': user_prompt}],
                                                                response_format=response_format,
                                                                tools=tools, 
                  
                                          )
        except Exception as e:
            print(e)
            raise ValueError(f"La clés API est invalide")

        
        return response
    



    def stream_model_response(self, system_prompt, user_prompt,tools=None, response_format=None):

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                response_format=response_format,
                tools=tools,
                stream=True
            )
        except Exception as e:
            raise ValueError("La clé API est invalide")

        return response
            

    def call_api(self,system_prompt, user_prompt,tools=None, response_format=None):
        print("Calling IA for :", user_prompt)
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Préparer les données pour l'appel API
        data = {
            "model": "gpt-4o",  # Assure-toi que ce modèle est valide
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt  # Utiliser le système prompt passé lors de l'initialisation
                },
                {
                    "role": "user",
                    "content": user_prompt  # Utiliser le contenu passé lors de l'appel
                }
            ],
            "tools":tools
                            }

        response = requests.post(self.endpoint_completion, json=data, headers=headers,  verify=True)
        result = ""
        if response.status_code == 200:
            result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        else:
            raise ValueError(f"La clés API est invalide")
        return result
    

    def stream_model_intern_response(self, system_prompt, user_prompt, model="gpt-4o-mini"):

        try:
            

            print("Calling IA for :", user_prompt)
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # Préparer les données pour l'appel API
            data = {
                "model": model,  # Assure-toi que ce modèle est valide
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt  # Utiliser le système prompt passé lors de l'initialisation
                    },
                    {
                        "role": "user",
                        "content": user_prompt  # Utiliser le contenu passé lors de l'appel
                    }
                ],
                "stream":True
                                }

            response = requests.post(self.endpoint_completion, json=data, headers=headers,  verify=True)            
            if response.status_code != 200:
                raise ValueError(f"Erreur API : {response.status_code} - {response.text}")

            full_response = ""

            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        data_str = decoded.removeprefix("data: ").strip()
                        if data_str == "[DONE]":
                            break
                        chunk = json.loads(data_str)
                        content = chunk["choices"][0].get("delta", {}).get("content")
                        if content:
                            full_response += content
                            yield full_response, None

        except Exception as e:
            print(f"erreur dans : {e}")
            raise ValueError("La clé API est invalide")
        


    def vectorizer(self, text):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
                "input": text,
                "model": "text-embedding-ada-002",
                "encoding_format": "float"
            }
        response = requests.post(self.endpoint_embeddings, json=data, headers=headers,  verify=True)
        if response.status_code == 200:
            result = response.json()['data'][0]['embedding']
        else:
            raise ValueError(f"La clés API embeddings est invalide")
        print("Resultat du call :", result)
        # Extraire les embeddings et les convertir en np.array
        embeddings =  np.array(result, dtype=np.float32)

        return embeddings
    

    def vectorizer2(self,textes):
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=textes
        )

        # Extraire les embeddings et les convertir en np.array
        embeddings = [np.array(e.embedding, dtype=np.float32) for e in response.data]
        return np.array(embeddings)
    

if __name__=="__main__":


        # Définir les paramètres
    #endpoint_completion = "https://motrice.int.gpt.sncf.fr/api/gateway/chat/completions"  # Remplace par ton endpoint_completion
    #api_key = "sgpt-TiWwGeG5TmmJGBJEosb5a47kf9AaqvJ9"  # Remplace par ta clé API
    import yaml
    from configparser import ConfigParser
    import os
    from dotenv import load_dotenv




    api_key = os.getenv("OPENAI_API_KEY_SNCF")
    endpoint_completion = os.getenv("ENDPOINT_COMPLETION")
    endpoint_embeddings = os.getenv("ENDPOINT_EMBEDDINGS")




    system_prompt = "Tu es un assistant intelligent, clair et concis. Tu aides l'utilisateur à comprendre des concepts simplement."  


    # Créer une instance de APIClient
    api_client = APIClient(endpoint_completion, endpoint_embeddings, api_key)
    api_client.call_api("reponds a mes questions", "salut tout le monde")