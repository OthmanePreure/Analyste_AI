import pandas as pd
from datetime import datetime
from collections import defaultdict
from module.utils import normalize
class CausePerf:

    def __init__(self, non_ponctu_df):
        self.non_ponctu_df = non_ponctu_df
        self.non_ponctu_df['nb_voyageurs_retardés'] = self.non_ponctu_df['nb_voyageurs_retardés'].fillna(0)


    

    def get_week_label(self, date_range):
        formated_date = []
        
        for date in date_range:
            # Convertir la chaîne de caractères en objet datetime
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            # Extraire le numéro de semaine et l'année ISO
            iso_year, iso_week, _ = date_obj.isocalendar()
            # Formater le numéro de semaine avec un zéro devant si nécessaire
            formated_date.append(f"S{iso_week:02d} {iso_year}")
        
        return formated_date


    def get_perf(self, arguments):
        try : 
            famille_cause = normalize(arguments.get('cause'))
            date_range = arguments['date_range']


            date_min, date_max = self.get_week_label(date_range)

            mask = (
                (self.non_ponctu_df["libelle_famille_cause"] == famille_cause) &
                (self.non_ponctu_df["libelle_semaine_annee"] >= date_min) &
                (self.non_ponctu_df["libelle_semaine_annee"] <= date_max)
            )

            df_filtred = self.non_ponctu_df[mask]

            if df_filtred.empty:
                return "cause non existante"

            sum_cause = df_filtred.groupby("code_cause")["nb_voyageurs_retardés"].sum().reset_index()
            vec = sum_cause[["code_cause", "nb_voyageurs_retardés"]].values.tolist()

            result = defaultdict(dict)
            for cause, retard in vec:
                result[cause] = int(retard)
            
            perf_cause = f"voici les sous cause de {famille_cause} avec leur impacte en terme de nombre de passager du {arguments["date_range"][0]} au {arguments["date_range"][1]} est : \n\n "
            perf_cause += str(dict(result))
            perf_cause += "\n\nIndiques la sous cause la plus impactante"

            return perf_cause
        
        except Exception as e:
            print(f"Erreur dans get_perf : {e}")

            return "cause non existante"




if __name__=="__main__":
    df = pd.read_excel(r'C:\Users\9510156B\agent_ai\data\non_ponctu17.xlsx')
    perf = CausePerf(df)
    date_min, date_max, famille_cause = "2025-01-05", "2025-01-19", "Matériel"
    perf.get_perf(famille_cause, [date_min, date_max])
    print()
