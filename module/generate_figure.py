import matplotlib.pyplot as plt
import io
from PIL import Image


class Figure:
    def __init__(self, idf_dict, ponctualite_df,sqlrequest):
        self.sqlrequest = sqlrequest

        self.idf_dict = idf_dict
        self.ponctualite_df = ponctualite_df

    def get_line_ponctu(self, date_range, line_name):
        date_min, date_max = date_range
        # Filtrer le DataFrame en fonction des dates
        mask = (self.ponctualite_df["date"] >= date_min) & (self.ponctualite_df["date"] <= date_max)
        filtered_df = self.ponctualite_df.loc[mask]

        line_name = line_name.upper()

        # Créer le dictionnaire avec la colonne "date" comme clé et les valeurs de la colonne souhaitée comme valeur
        # Par exemple, si tu veux que la clé soit la date et la valeur soit l'élément de la colonne "line_name"
        result_dict = dict(zip(filtered_df["date"], filtered_df[line_name]))

        # Afficher le dictionnaire
        print(result_dict)

        return result_dict

    def show_figure(self, arguments):
        
        try:
            line_name = arguments["line_name"].upper()
            date_range = arguments["date_range"]
            test = line_name.lower()
            if "ligne" in test or "rer" in test :
                line_name = test[-1].upper()

            data_dict = self.sqlrequest.get_line_perf(date_range, line_name)
            # Extraire les dates et valeurs
            dates = list(data_dict.keys())
            values = list(data_dict.values())
        
            # Créer un graphique en barres plus esthétique
            plt.figure(figsize=(12, 6))  # Taille plus grande pour plus de clarté
            bars = plt.bar(dates, values, color='#487bda', linewidth=1.2)  # Couleur et bordure des barres
            # Préparer les positions de ticks x tous les 3 jours + dernier jour si non inclus
            tick_indices = list(range(0, len(dates), 3))
            if (len(dates) - 1) not in tick_indices:
                tick_indices.append(len(dates) - 1)
            tick_labels = [dates[i] for i in tick_indices]

            plt.xticks(ticks=tick_indices, labels=tick_labels, rotation=0, fontname='Arial', color='#4B0082', fontweight='bold')
            # Supprimer les valeurs de l'axe Y
            plt.yticks([])

            # Ajouter des annotations sur les barres
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, yval + 1, str(yval) +"%", ha='center',fontname='Arial', color='#4B0082', fontweight='bold')

            # Masquer les spines (le cadre)
            for spine in plt.gca().spines.values():
                spine.set_visible(False)

            # Ajuster l'espacement des éléments
            plt.tight_layout()
            
            # Sauvegarder dans un buffer BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format='png')  # Sauvegarder l'image au format PNG
            buf.seek(0)  # Revenir au début du buffer
            
            # Convertir BytesIO en image PIL
            img = Image.open(buf)

            # Fermer la figure pour libérer la mémoire
            plt.close()

            # Retourner l'image PIL
            return img
        except Exception as e:
            print(f'erreur dans show_figure {e}')
            return 'erreur dans generation image'
if __name__=="__main__":
    import pandas as pd
    import json

    ponct_path = r"C:\Users\9510156B\agent_ai\data\poctualite_df.csv"
    idf_path = r"C:\Users\9510156B\agent_ai\data\idf_dict.json"
    ponctualite_df = pd.read_csv(ponct_path, sep=";")
    with open(idf_path, "r", encoding="utf-8") as f:
        idf_dict = json.load(f)

    line_name = "U"
    date_range = ["2025-01-17","2025-01-22"]

    fig = Figure(line_name,date_range, idf_dict, ponctualite_df)
    fig.show_figure()
    print()