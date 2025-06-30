
import sqlite3

class SQLHandler:
    def __init__(self, db_path=r'data\ma_base.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_incident INTEGER,
                commentaire_incident TEXT,
                date_incident TEXT
            )
        ''')
        self.conn.commit()


    def add_new_value(self, colonnes_valeurs: dict, date, nombre):
        # Vérifie que tous les noms de colonnes sont valides
        for col in colonnes_valeurs:
            if not col.isidentifier():
                raise ValueError(f"Nom de colonne invalide : {col}")

        # Construction dynamique de la requête
        set_clause = ", ".join(f"{col} = ?" for col in colonnes_valeurs)
        valeurs = list(colonnes_valeurs.values()) + [date, nombre]

        query = f"""
            UPDATE incidents
            SET {set_clause}
            WHERE date_incident = ? AND nombre_incident = ?;
        """
        self.cursor.execute(query, valeurs)
        self.conn.commit()

        
    def insert_row_line_perf(self,id, date, line_perf):
        self.cursor.execute('''
            INSERT INTO line_perf (id, date_val, valeur) VALUES (?, ?, ?);
''', (id, date, line_perf))
        self.conn.commit()


    def insert_row(self, nombre_incident, date_incident, commentaire_incident):
        self.cursor.execute('''
            INSERT INTO incidents (nombre_incident, date_incident, commentaire_incident) VALUES (?, ?, ?)
        ''', (nombre_incident, date_incident, commentaire_incident))
        self.conn.commit()


    def close(self):
        self.conn.close()

    def format_documents(self, documents):
        nbr_incident = len(documents)
        formatted_str = f"Ci dessous tu a les {nbr_incident} incidents les plus impactant : \n\n"
        for ind,doc in enumerate(documents):
            formatted_str += "date incident : \"{}\" \n\n, nombre de personne impacté : \"{}\" \n\n, commentaire_incident : \"{}\" \n\n".format(*doc)
            formatted_str += "\n\n"
        return formatted_str

    def format_documents_for_report(self, documents):
        nbr_incident = len(documents)
        formatted_str = f"Ci dessous tu a les {nbr_incident} incidents les plus impactant : \n\n"
        for ind,doc in enumerate(documents):
            formatted_str += "date incident : \"{}\" \n\n, nombre de personne impacté : \"{}\" \n\n, commentaire_incident : \"{}\" \n\n, cause incident : \"{}\" \n\n, class de cause : \"{}\" \n\n, lieu de l'incident : \"{}\" \n\n, part de non ponctualité de l'incident : \"{}\" \n\n".format(*doc)
            formatted_str += "\n\n"
        return formatted_str
    def get_data(self, args):
        try : 
            query = '''
                SELECT date_incident, nombre_incident, commentaire_incident, cause, class_cause, lieu, part_non_ponctu_float      
                FROM incidents
            '''
            params = []
            top_n = 5

            start_date = args.get('start_date')
            end_date = args.get('end_date')
            class_cause = args.get('class_cause')

            if start_date and end_date:
                query += ' WHERE date_incident BETWEEN ? AND ? '
                params.extend([start_date, end_date])
            elif start_date:
                query += ' WHERE date_incident = ? '
                params.append(start_date)
                # si pas de start_date on ne filtre pas

            if class_cause:
                if "WHERE" in query:
                    query += " AND class_cause = ?"
                else:
                    query += " WHERE class_cause = ?"
                params.append(class_cause)
                
            query += ' ORDER BY nombre_incident DESC LIMIT ?'
            params.append(top_n)

            self.cursor.execute(query, params)
            documents = self.cursor.fetchall()
            formated_response = self.format_documents_for_report(documents)
            return formated_response

        except Exception as e:
            print(f'probleme dans la fonction get_data in sql_handler file :\n {e}')
            return "probleme dans l'affichage de la figure"
        
    def get_line_perf(self,date,line):
        try :

            params = [line]
            query = '''
                SELECT date_val, valeur
                FROM line_perf
            '''
            if len(date)==2:
                start_date = date[0]
                end_date = date[1]
            else : 
                start_date = date[0]

            if start_date and end_date:
                query += ' WHERE id = ? AND date_val BETWEEN ? AND ? '
                params.extend([start_date, end_date])
            elif start_date:
                query += ' WHERE id = ? AND date_val = ? '
                params.append(start_date)
            self.cursor.execute(query, params)
            values = self.cursor.fetchall()
            new_dict = dict(values)

            return new_dict
        
        except Exception as e:
            print(f'probleme dans la fonction get_line_perf {e}')
            return "probleme dans l'affichage de la figure"
        
    def get_top_incidents(self, args):
        try : 
            query = '''
                SELECT date_incident, nombre_incident, commentaire_incident
                FROM incidents
            '''
            params = []
            top_n = 3

            start_date = args.get('start_date')
            end_date = args.get('end_date')
            top_n = args.get('top_n', 3)
            if start_date and end_date:
                query += ' WHERE date_incident BETWEEN ? AND ? '
                params.extend([start_date, end_date])
            elif start_date:
                query += ' WHERE date_incident = ? '
                params.append(start_date)
                # si pas de start_date on ne filtre pas
            
            
                

            query += ' ORDER BY nombre_incident DESC LIMIT ?'
            params.append(top_n)

            self.cursor.execute(query, params)
            documents = self.cursor.fetchall()
            formated_response = self.format_documents(documents)

            return formated_response

        except Exception as e : 
            print(f'erreur dans get_top_incidents : {e}')
            return 'probleme dans recherche des top incident'
        

    
    def add_column(self, name_column):
        # Vérifie que le nom de colonne est valide (optionnel mais recommandé)
        if not name_column.isidentifier():
            raise ValueError(f"Nom de colonne invalide : {name_column}")

        # Ajouter la colonne si elle n'existe pas (sinon erreur)
        self.cursor.execute(f"ALTER TABLE incidents ADD COLUMN {name_column} REAL;")
        self.conn.commit()


if __name__=="__main__":
    import pandas as pd
    import os

    #self.add_columns(["cause", "class_cause", "part_non_ponctu", "lieu"])



    sql_handler = SQLHandler()
        
    s = sql_handler.get_data({"start_date": "2025-03-02", "end_date": "2025-03-08", "class_cause":"reseau"})
    print()