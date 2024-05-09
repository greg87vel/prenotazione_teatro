import firebase_admin
from firebase_admin import credentials, db
import pandas as pd

# Configura Firebase Admin SDK
cred = credentials.Certificate('cred-greg.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://prenotazione-teatro-default-rtdb.europe-west1.firebasedatabase.app/'
})


# Funzione per ottenere i dati dalla reference e creare un DataFrame
def reference_to_dataframe(reference, dataframe_name):
    # Recupera i dati dalla reference
    data = reference.get()

    # Se non ci sono dati, restituisci un DataFrame vuoto
    if not data:
        print(f"La reference {reference.path} non contiene dati.")
        return pd.DataFrame()

    # Converti i dati in un DataFrame
    df = pd.DataFrame.from_dict(data, orient='index')

    # Stampa un messaggio di successo
    print(f"DataFrame '{dataframe_name}' creato con successo dalla reference {reference.path}.")

    # Restituisci il DataFrame
    return df


# Riferimento alla tabella platea
ref = db.reference('/teatro_aurora_velletri')

# Recupera i dati dalla reference e crea un DataFrame
df_platea = reference_to_dataframe(ref, 'df_teatro_aurora_velletri')

# Mostra i primi 5 record del DataFrame
print(df_platea.head())
