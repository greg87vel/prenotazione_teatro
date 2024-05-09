import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# ----------------------------
# IMPOSTAZIONI

# Configura Firebase Admin SDK
if firebase_admin._apps:
    pass
else:
    cred = credentials.Certificate('cred-greg.json')
    firebase_admin.initialize_app(cred, options={
        'databaseURL': 'https://prenotazione-teatro-default-rtdb.europe-west1.firebasedatabase.app/'
    })

# Configurazione Streamlit
st.set_page_config(page_title="Prenotazione Posti Teatro", page_icon="🎭")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "evento" not in st.session_state:
    st.session_state['evento'] = ''

# Titolo
st.image('logoROTcol.png', width=200)
st.title("Servizio interno di prenotazione posti")


# ----------------------------
# UTILS

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""


def login(user, password):
    ref_credenziali = db.reference(f'/credenziali')
    credentials = ref_credenziali.get()
    if not credentials:
        st.session_state.logged_in = False
        print("Nessuna credenziale trovata.")
        return False

    for credential in credentials:
        if credential and credential.get('user').lower() == user.lower() and credential.get('password').lower() == password.lower():
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
    ref.update(data)


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
            if ref in ['CREDENZIALI', 'credenziali']:
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
        color = '🟩' if seat_info['prenotato'] in ['no', 'NO'] else '🟥'
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
        if not (seat_info['prenotato'].upper() == 'NO'):
            st.write(f"**Prenotato da:** {seat_info['nominativo'].upper()}")
            st.write(f"**Note:** {seat_info['note']}")

        # Form per aggiornare le informazioni di prenotazione
        if seat_info['prenotato'].upper() == 'NO':
            with st.form(key='booking_form'):
                note = st.text_area('Note', value=seat_info['note'])
                submit_button = st.form_submit_button(label='Prenota!')
            if submit_button:
                ref_posto_da_prenotare = db.reference(f'/{st.session_state["evento"]}/{selected_seat}')
                info_posto = ref_posto_da_prenotare.get()
                st.write(info_posto)
                import time
                time.sleep(3)
                if info_posto['prenotato'].lower() == 'no':
                    new_data = {
                        'prenotato': 'sì',
                        'nominativo': st.session_state.username.capitalize(),
                        'note': note
                    }
                    update_seat(selected_seat, new_data)
                    st.success(f"Prenotazione effettuata con successo!")
                    st.rerun()
                else:
                    st.warning(f'Prenotazione non riuscita. Il posto è stato appena prenotato da {info_posto["nominativo"].upper()}')
    st.button("Esci", on_click=logout)


# ----------------------------
# GESTIONE DELLE PAGINE

if st.session_state['evento']:
    show_billing_page()

elif st.session_state.logged_in:
    pagina_scelta_evento()

else:
    show_login_page()
