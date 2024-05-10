import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time

# ----------------------------
# IMPOSTAZIONI

# Configurazione Streamlit
st.set_page_config(page_title="Prenotazione Posti Teatro", page_icon="🎭")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "evento" not in st.session_state:
    st.session_state['evento'] = ''
if "selected_seat" not in st.session_state:
    st.session_state['selected_seat'] = None

# Titolo
st.image('logoROTcol.png', width=200)
st.title("Servizio di prenotazione posti")

# Configura Firebase Admin SDK

firebase_credentials = {
    "type": st.secrets.FIREBASE_TYPE,
    "project_id": st.secrets.FIREBASE_PROJECT_ID,
    "private_key_id": st.secrets.FIREBASE_PRIVATE_KEY_ID,
    "private_key": st.secrets.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
    "client_email": st.secrets.FIREBASE_CLIENT_EMAIL,
    "client_id": st.secrets.FIREBASE_CLIENT_ID,
    "auth_uri": st.secrets.FIREBASE_AUTH_URI,
    "token_uri": st.secrets.FIREBASE_TOKEN_URI,
    "auth_provider_x509_cert_url": st.secrets.FIREBASE_AUTH_PROVIDER_CERT_URL,
    "client_x509_cert_url": st.secrets.FIREBASE_CLIENT_CERT_URL
}


if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, options={
        'databaseURL': 'https://prenotazione-teatro-default-rtdb.europe-west1.firebasedatabase.app/'
    })



# ----------------------------
# UTILS

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""


def login(user, password):
    ref_credenziali = db.reference('/credenziali')
    credentials = ref_credenziali.get()
    if not credentials:
        st.session_state.logged_in = False
        print("Nessuna credenziale trovata.")
        return False

    for credential in credentials:
        if credential and credential.get('user').lower() == user.lower() and credential.get(
                'password').lower() == password.lower():
            st.session_state.logged_in = True
            return True
    return False


def load_seats():
    # Load the seats data from Firebase
    ref = db.reference(f'/{st.session_state["evento"]}')
    return ref.get()


def update_seat(seat_id, data):
    # Update a specific seat data in Firebase
    ref = db.reference(f'/{st.session_state["evento"]}/{seat_id}')
    current_data = ref.get()
    if current_data['prenotato'].lower() == 'no':
        ref.update(data)
        return True
    else:
        return False


# ----------------------------
# PAGINA DI LOGIN

def show_login_page():
    st.title("Accesso")
    username = st.text_input("Utente")
    password = st.text_input("Password", type="password")
    login_button = st.button("Accedi")

    if login_button:
        if login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("❌ Nome utente o password errati. Riprova!")


# ----------------------------
# PAGINA DI SCELTA EVENTO

def pagina_scelta_evento():
    st.success(f"Benvenuto, {st.session_state.username.capitalize()}! 😊")
    st.subheader("Seleziona l'evento che ti interessa:")
    reference_path = "/"  # Sostituisci con il percorso corretto

    # Recupera tutti i nodi figlio sotto il percorso specificato
    ref = db.reference(reference_path)
    references_data = ref.get()

    # Verifica che i dati esistano
    if references_data:
        # Filtra le referenze secondo il pattern
        references = [key for key in references_data.keys()]

        # Crea un pulsante Streamlit per ogni referenza
        for ref in references:
            if ref.lower() == 'credenziali':
                pass
            elif st.button(ref):
                st.session_state['evento'] = ref
                st.rerun()
    else:
        st.write("Non ci sono eventi con questo nome.")


# ----------------------------
# PAGINA DI PRENOTAZIONE

def show_billing_page():
    st.success(f"Benvenuto, {st.session_state.username.capitalize()}! 😊")
    st.success(f"Hai selezionato l'evento: {st.session_state['evento'].upper()}")
    # Carica i dati dei posti
    seats_data = load_seats()
    if not seats_data:
        st.error("Errore nel caricare i dati dei posti.")
        return

    # Definisci la disposizione del teatro
    rows = {}

    for key in sorted(seats_data.keys()):
        letter = key[0]
        if letter not in rows:
            rows[letter] = []
        rows[letter].append(key)

    st.write("## Pianta dei Posti (Clicca per selezionare)")

    st.image('palco.png')

    selected_seat = st.session_state.get('selected_seat', None)

    # Funzione per creare un bottone in base allo stato del posto
    def create_button(seat_info, seat_key):
        color = '🟩' if seat_info['prenotato'].lower() == 'no' else '🟥'
        return st.button(f"{color}", key=seat_key)

    # Disegna la disposizione del teatro usando righe e colonne
    for row, seats in rows.items():
        cols = st.columns(len(seats))
        for idx, seat in enumerate(seats):
            seat_info = seats_data[seat]
            with cols[idx]:
                if create_button(seat_info, seat):
                    selected_seat = seat
                    st.session_state['selected_seat'] = seat

    # Mostra i dettagli del posto selezionato e il form di prenotazione
    if selected_seat:
        seat_info = seats_data[selected_seat]
        st.write(f"### Dettagli del Posto Selezionato ({selected_seat})")
        st.write(f"**Posto:** {seat_info['posto']}")
        st.write(f"**Posizione:** {seat_info['posizione'].upper()}")
        st.write(f"**Prezzo:** {seat_info['prezzo']} Euro")
        if seat_info['prenotato'].lower() == 'sì':
            st.write(f"**Prenotato da:** {seat_info['nominativo'].upper()}")
            st.write(f"**Note:** {seat_info['note']}")

        # Form per aggiornare le informazioni di prenotazione
        if seat_info['prenotato'].lower() == 'no':
            with st.form(key='booking_form'):
                note = st.text_area('Note', value=seat_info['note'])
                submit_button = st.form_submit_button(label='Prenota!')
            if submit_button:
                new_data = {
                    'prenotato': 'sì',
                    'nominativo': st.session_state.username.capitalize(),
                    'note': note
                }
                success = update_seat(selected_seat, new_data)
                if success:
                    st.success("Prenotazione effettuata con successo!")
                    time.sleep(1.5)
                    st.session_state['selected_seat'] = None
                    st.rerun()
                else:
                    st.warning(f"Prenotazione NON effettuata. Il posto è stato appena prenotato da qualcun altro.")
                    st.session_state['selected_seat'] = None
                    st.rerun()

    st.button("Esci", on_click=logout)


# ----------------------------
# GESTIONE DELLE PAGINE

if st.session_state['evento']:
    show_billing_page()
elif st.session_state.logged_in:
    pagina_scelta_evento()
else:
    show_login_page()
