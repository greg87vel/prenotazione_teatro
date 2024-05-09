import firebase_admin
from firebase_admin import credentials, db

# Configura Firebase Admin SDK
cred = credentials.Certificate('cred-greg.json')
firebase_admin.initialize_app(credential=cred, options={
    'databaseURL': 'https://prenotazione-teatro-default-rtdb.europe-west1.firebasedatabase.app/'
})

data = '29 GENNAIO 2025'
evento = 'IL MEDICO DEI PAZZI'
teatro = 'TEATRO AURORA'
ultima_lettera = 'F'
ultimo_numero = 16
prima_lettera_galleria = 'G'


def trova_posti_duplicati(reference):
    data = reference.get()
    if not data:
        print("La reference fornita non contiene dati.")
        return

    posti_visti = set()
    duplicati = set()

    for key, value in data.items():
        posto = value['posto']
        if posto in posti_visti:
            duplicati.add(posto)
        else:
            posti_visti.add(posto)

    if duplicati:
        print("Posti duplicati trovati:", duplicati)
    else:
        print("Nessun posto duplicato trovato.")


# Funzione per determinare la posizione (platea o galleria)
def determina_posizione(lettera):
    if 'A' <= lettera <= 'L':
        return 'PLATEA'
    elif prima_lettera_galleria <= lettera:
        return 'GALLERIA'


# Funzione per determinare il prezzo in base alla lettera (esempio)
def determina_prezzo(lettera):
    # Fai una logica personalizzata per determinare il prezzo
    if 'A' <= lettera <= 'C':
        return 10
    else:
        return 8


def posto_esiste(reference, posto):
    return reference.child(posto).get() is not None


# Funzione per generare posti e scriverli su Firebase
def genera_posti(reference):
    for lettera in range(ord('A'), ord(ultima_lettera) + 1):
        for numero in range(1, ultimo_numero+1):
            codice_numero = str(numero).zfill(2)
            codice_posto = chr(lettera) + codice_numero
            if not posto_esiste(reference, codice_posto):
                posto = {
                    'posto': codice_posto,
                    'prenotato': 'NO',
                    'nominativo': '',
                    'prezzo': determina_prezzo(chr(lettera)),
                    'posizione': determina_posizione(chr(lettera)),
                    'note': ''
                }
                reference.child(codice_posto).set(posto)
                print(f"Posto {codice_posto} aggiunto.")
            else:
                print(f"Posto {codice_posto} già presente e non è stato aggiunto.")


# Riferimento al teatro specifico
ref = db.reference(f'/{data}_{evento}_{teatro}')

# Genera e aggiungi posti alla tabella Firebase
genera_posti(ref)

print("Aggiornamento della tabella dei posti completato.")
