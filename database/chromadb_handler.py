import chromadb
import hashlib
from scipy.spatial.distance import cosine
from typing import List
from collections import OrderedDict
from module.utils import to_unix_epoch
class SetDatabase:
    def __init__(self, client, name_collection):


        # s'assurer de changer de path  si tu changes de collection
        self.chroma_client = chromadb.PersistentClient(path=r"C:\Users\9510156B\agent_ai\storage_np")
        self.openai_client = client
        self.collection = self.chroma_client.get_or_create_collection(name_collection)

    def index_documents(self: str, data):
        # Ingest data into ChromaDB
        docs = data['documents']

        data["ids"] = [self.generate_id(doc) for doc in docs]
        
        self.check_data(docs)

        for i, meta in enumerate(data['metadatas']):
            if not meta:    
                data['metadatas'][i] = {"placeholder": "no_metadata"}

        self.collection.add(
            documents=data['documents'],
            metadatas=data['metadatas'],
            ids=data['ids'],
            embeddings=data['embeddings']
        )

        print("Data indexed successfully.")
        return self.collection
    

    def index_data(self, document: str, embedding: list[float], metadata: dict = None):
        # Générer un ID unique pour le document
        doc_id = self.generate_id(document)

        # Vérifier la validité du document (si tu as une méthode check_data)
        self.check_data([document])  # On passe une liste ici si check_data attend une liste

        # Nettoyer ou compléter les métadonnées
        if not metadata:
            metadata = {"placeholder": "no_metadata"}
        else:
            metadata = {k: v for k, v in metadata.items() if v is not None}

        # Ajouter dans la base
        try:
            self.collection.add(
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"Erreur lors de l'ajout du document {doc_id} : {e}")

    
    def check_data(self, docs: List[str]):
        """
        Vérifie si les documents existent déjà dans la collection en comparant leurs hashes.
        Supprime les documents existants avant de les réindexer.
        """
        for doc in docs:
            # Générer l'ID (hash) du document
            doc_id = self.generate_id(doc)

            try:
                # Vérifier si le document existe dans la collection
                existing = self.collection.get(ids=[doc_id])
            except Exception:
                # Si une exception est levée, considérer que le document n'existe pas
                existing = {"ids": []}

            if existing["ids"]:
                # Si le document existe, le supprimer
                print(f"♻️  Doc ID {doc_id} existe déjà. Suppression...")
                return
            else:
                print(f"❌  Doc ID {doc_id} n'existe pas. Prêt pour indexation.")
    
    def generate_id(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

class DatabaseHandler:


    def __init__(self, client, name_collection):
        # s'assurer de changer de path  si tu changes de collection
        self.chroma_client = chromadb.PersistentClient(path=r"C:\Users\9510156B\agent_ai\storage_np")
        self.openai_client = client
        self.collection = self.chroma_client.get_or_create_collection(name_collection)


    def generate_id(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def should_update(self, old_emb: List[float], new_emb: List[float], threshold: float = 0.01) -> bool:
        return cosine(old_emb, new_emb) > threshold



    def semantic_search_per_date(self, query: str, date_filter, n_results: int = 5):
        # Perform a search in the ChromaDB collection


        filter_date = self.filter_per_date(date_filter)
        results = self.collection.query(
            query_embeddings=[self.openai_client.vectorizer(query)],
            n_results=n_results,
            where=filter_date
        )
        return results

    
    def semantic_search(self, query: str, n_results: int = 5):
        # Perform a search in the ChromaDB collection


        results = self.collection.query(
            query_embeddings=[self.openai_client.vectorizer(query)],
            n_results=n_results,
        )
        return results
    


    def exacte_search_per_date(self, line_filter, date_filter, n_results: int = 5):
        dummy_embedding = [0.0] * 1536  # vecteur nul dimension 1536

        filter_date = self.filter_per_date(date_filter)



        results = self.collection.query(
            query_embeddings=[dummy_embedding],
            n_results=n_results,
            where={"$and":[line_filter, filter_date]}
        )
        return results
    def exacte_search_without_ligne(self, date_filter, n_results: int = 5):
        dummy_embedding = [0.0] * 1536  # vecteur nul dimension 1536

        filter_date = self.filter_per_date(date_filter)



        results = self.collection.query(
            query_embeddings=[dummy_embedding],
            n_results=n_results,
            where= filter_date
        )
        return results


    def filter_per_date(self, date_filter: dict) -> dict:
        """
        Construit le filtre 'where' pour ChromaDB basé sur un dictionnaire de dates.

        Args:
            date_filter (dict): Peut contenir 'start_date' et/ou 'end_date'.

        Returns:
            dict: Filtre ChromaDB pour le champ 'date'.
        """
        conditions = []
        date = {}
        if "start_date" in date_filter and "end_date" in date_filter:
            conditions.append({"date": {"$gte": date_filter["start_date"]}})
            conditions.append({"date": {"$lte": date_filter["end_date"]}})

            date = {"$and": conditions}
        elif "start_date" in date_filter:
            date["date"] = {"$eq": date_filter["start_date"]}
        return date
    


    def deduplicate_by_id(self, res1, res2):
        merged = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": []
        }

        # On extrait les listes imbriquées
        all_ids = res1["ids"][0] + res2["ids"][0]
        all_docs = res1["documents"][0] + res2["documents"][0]
        all_metas = res1["metadatas"][0] + res2["metadatas"][0]
        all_dists = res1["distances"][0] + res2["distances"][0]

        seen = OrderedDict()
        for i, doc_id in enumerate(all_ids):
            if doc_id not in seen:
                seen[doc_id] = i

        for doc_id, i in seen.items():
            merged["ids"].append(doc_id)
            merged["documents"].append(all_docs[i])
            merged["metadatas"].append(all_metas[i])
            merged["distances"].append(all_dists[i])

        # 🔁 Standardisation : encapsule dans une liste comme ChromaDB
        for key in merged:
            merged[key] = [merged[key]]

        return merged



    def augmented_search_per_date(self, query, arguments, n_results=5):
        
        
        final_response = ""

        question = arguments['question']
        if "date" in arguments :
            if arguments["date"] : 
                arguments["date"] = {k: to_unix_epoch(v) for k, v in arguments["date"].items()}
                date_filter = {arg: arguments['date'][arg] for arg in arguments['date']} 

            else : 
                final_response = self.semantic_search(question, 50)
                return final_response
            
            
            if "ligne" not in  arguments:
                exact_response = self.exacte_search_without_ligne(date_filter, n_results)
            
            else: 
                line_filter = {"ligne" : arguments["ligne"]}
                exact_response = self.exacte_search_per_date(line_filter, date_filter, n_results)
            
            semantic_response = self.semantic_search_per_date(question, date_filter, n_results)
            
            final_response = self.deduplicate_by_id(semantic_response, exact_response)
        elif "date" not in arguments and "ligne" not in arguments : 
            final_response = self.semantic_search(question, 50)

        elif "date" not in arguments and "ligne" in arguments:
            final_response = self.semantic_search(question, 50)
            
        return final_response
        

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()

    api = os.getenv('OPENAI_API_KEY_OTHMANE')

    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("my_collection")
    s = DatabaseHandler(api)
    print()
