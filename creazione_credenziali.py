import firebase_admin
from firebase_admin import credentials, db
import random

# Configura Firebase Admin SDK
cred = credentials.Certificate('cred-greg.json')
firebase_admin.initialize_app(cred, options={
    'databaseURL': 'https://prenotazione-teatro-default-rtdb.europe-west1.firebasedatabase.app/'
})

ref = db.reference(f'/credenziali')


# Funzione per generare username e password facili da ricordare
def generate_easy_username_password_pairs(names):
    def generate_username(name):
        # Genera un username usando il nome dato
        return name

    def generate_password():
        # Genera una password usando aggettivi e nomi comuni in italiano
        aggettivi = [
            'veloce', 'lento', 'pigro', 'felice', 'scaltro',
            'simpatico', 'divertente', 'forte', 'intelligente',
            'coraggioso'
        ]
        sostantivi = [
            'volpe', 'cane', 'gatto', 'orso', 'uccello',
            'albero', 'sole', 'luna', 'stella', 'nuvola'
        ]
        numero = str(random.randint(10, 99))
        return random.choice(sostantivi) + random.choice(aggettivi) + numero

    pairs = [{'user': generate_username(name), 'password': generate_password()} for name in names]
    return pairs


# Lista dei nomi forniti
names = [
    'Eugenio', 'Giuseppe', 'Matilde', 'Pietro',
    'Giacomo', 'Francesca', 'Antonietta',
    'Bartolomeo', 'Cristian', 'Graziano', 'Gregory', 'Settimio'
]

# Genera e salva le combinazioni di username e password
username_password_pairs = generate_easy_username_password_pairs(names)
for i, pair in enumerate(username_password_pairs):
    ref.child(str(i + 1)).set(pair)

print(f"{len(names)} combinazioni di username e password sono state salvate con successo.")
