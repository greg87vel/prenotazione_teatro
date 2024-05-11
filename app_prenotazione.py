import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
from fpdf import FPDF
import os
import qrcode
from PIL import Image
import base64
import io

# ----------------------------
# IMPOSTAZIONI

# Configurazione Streamlit
st.set_page_config(page_title="Prenotazione Posti Teatro", page_icon="🎭", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "evento" not in st.session_state:
    st.session_state['evento'] = ''
if "selected_seat" not in st.session_state:
    st.session_state['selected_seat'] = None

hide_streamlit_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Titolo

logo_path = 'immagini/logoROTcol.png'
img = Image.open(logo_path)

# Converti l'immagine in base64
buffered = io.BytesIO()
img.save(buffered, format="PNG")
encoded_img = base64.b64encode(buffered.getvalue()).decode()

# Crea l'HTML per centrare l'immagine
html_code = f"""
<div style="text-align: center;">
    <img src="data:image/png;base64,{encoded_img}" width="200">
    <h1 style="font-family: Arial, sans-serif; margin-top: 20px;">Servizio di prenotazione posti</h1>
</div>
"""

# Usa st.markdown per visualizzare l'HTML
st.markdown(html_code, unsafe_allow_html=True)

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


# Genera la griglia HTML
def select_seat_callback(seat):
    st.session_state['selected_seat'] = seat
    st.rerun()


# Funzione per creare un codice QR
def generate_qr_code(data, file_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img.save(file_path, "JPEG")


class PDF(FPDF):

    def header(self):
        logo_path = 'immagini/logoROTcol.jpg'
        # Aggiungi il logo centrato in alto
        if os.path.exists(logo_path):
            logo_width = 30
            page_width = self.w
            x_position = (page_width - logo_width) / 2
            self.image(logo_path, x=x_position, y=10, w=logo_width)
            self.ln(40)  # Spazio extra sotto il logo
        self.set_font("Arial", "B", 20)
        self.cell(0, 10, "A.P.S. 'I DILETTANTI ALL'OPERA'", 0, 1, "C")
        self.ln(10)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, f"{title}", 0, 1, "C")
        self.ln(10)

    def chapter_body_key(self, body):
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, body)

    def chapter_body_value(self, body):
        self.set_font("Arial", "B", 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_qr_code(self, path, x=None, y=None, w=40):
        if os.path.exists(path):
            if x is None:
                x = (self.w - w) / 2
            if y is None:
                y = self.get_y()
            self.image(path, x=x, y=y, w=w)
            self.ln(10)


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state['evento'] = ''
    st.session_state['selected_seat'] = None

def esci_evento():
    st.session_state['evento'] = ''


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

    st.image('immagini/palco.png')

    for row, seats in rows.items():
        num_columns = len(seats)
        cols = st.columns(num_columns)
        for idx, seat in enumerate(seats):
            seat_info = seats_data[seat]
            if seat_info['prenotato'].lower() == 'no':
                if st.session_state['selected_seat'] == seat:
                    cols[idx].button("🟩",
                                     help=f'Posto: {seat_info["posto"]} - LIBERO',
                                     key=seat,
                                     on_click=select_seat_callback,
                                     args=(seat,),
                                     disabled=False,
                                     type='primary')
                else:
                    cols[idx].button("🟩",
                                     help=f'Posto: {seat_info["posto"]} - LIBERO',
                                     key=seat,
                                     on_click=select_seat_callback, args=(seat,), disabled=False)
            else:
                if st.session_state.username.lower() == seat_info['nominativo'].lower():
                    if st.session_state['selected_seat'] == seat:
                        if seat_info["note"].strip() == '':
                            cols[idx].button('🟦',
                                             help=f'Posto: {seat_info["posto"]} - '
                                             'Prenotato da: {seat_info["nominativo"].upper()}',
                                             key=seat, on_click=select_seat_callback, args=(seat,), disabled=False,
                                             type='primary')
                        else:
                            cols[idx].button('🟦',
                                             help=f'Posto: {seat_info["posto"]} - '
                                                  f'Prenotato da: {seat_info["nominativo"].upper()} - '
                                                  f'Note: {seat_info["note"].upper()}',
                                             key=seat, on_click=select_seat_callback, args=(seat,), disabled=False,
                                             type='primary')

                    elif seat_info["note"].strip() == '':
                        cols[idx].button('🟦',
                                         help=f'''Posto: {seat_info["posto"]}\n
                                         Prenotato da: {seat_info["nominativo"].upper()}''',
                                         key=seat, on_click=select_seat_callback, args=(seat,), disabled=False)
                    else:
                        cols[idx].button('🟦',
                                         help=f'Posto: {seat_info["posto"]} - '
                                              f'Prenotato da: {seat_info["nominativo"].upper()} - '
                                              f'Note: {seat_info["note"].upper()}',
                                         key=seat, on_click=select_seat_callback, args=(seat,), disabled=False)
                else:
                    if seat_info["note"].strip() == '':
                        cols[idx].button('🟥',
                                         help=f'''Posto: {seat_info["posto"]}\n
                                                  Prenotato da: {seat_info["nominativo"].upper()}''',
                                         key=seat, on_click=select_seat_callback, args=(seat,), disabled=True)
                    else:
                        cols[idx].button('🟥',
                                         help=f'Posto: {seat_info["posto"]} \n  '
                                              f'Prenotato da: {seat_info["nominativo"].upper()}\n'
                                              f'Note: {seat_info["note"].upper()}',
                                         key=seat, on_click=select_seat_callback, args=(seat,), disabled=True)

    selected_seat = st.session_state.get('selected_seat', None)

    # Mostra i dettagli del posto selezionato e il form di prenotazione
    if selected_seat:
        seat_info = seats_data[selected_seat]
        st.write(f"### Dettagli del Posto Selezionato ({selected_seat})")
        st.write(f"**Posto:** {seat_info['posto']}")
        st.write(f"**Posizione:** {seat_info['posizione'].upper()}")
        if seat_info['prenotato'].lower() == 'sì':
            st.write(f"**Prenotato da:** {seat_info['nominativo'].upper()}")
            st.write(f"**Note:** {seat_info['note']}")
            if seat_info['nominativo'].lower() == st.session_state.username.lower():
                project_folder = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(project_folder,
                                         f"pdf/Ricevuta Prenotazione - POSTO: {seat_info['posto']} - {st.session_state['evento']}.pdf")
                qr_code_path = os.path.join(project_folder,
                                            f"qr/qrcode - POSTO: {seat_info['posto']} - {st.session_state['evento']}.jpg")
                # Crea file PDF se non esiste
                if not os.path.exists(file_path):

                    pdf = PDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)

                    pdf.chapter_title("RICEVUTA DI PRENOTAZIONE")
                    if seat_info['note'].strip() == '':
                        pdf.chapter_body_key("Evento")
                        pdf.chapter_body_value(st.session_state['evento'])
                        pdf.chapter_body_key("Posto")
                        pdf.chapter_body_value(seat_info['posto'])
                        pdf.chapter_body_key("Prenotato da")
                        pdf.chapter_body_value(seat_info['nominativo'])

                        qr_text = (f'RICEVUTA DI PRENOTAZIONE\n'
                                   f'Evento: {st.session_state["evento"]}\n'
                                   f'Posto: {seat_info["posto"]}')

                        generate_qr_code(qr_text, qr_code_path)
                    else:
                        pdf.chapter_body_key("Evento")
                        pdf.chapter_body_value(st.session_state['evento'])
                        pdf.chapter_body_key("Posto")
                        pdf.chapter_body_value(seat_info['posto'])
                        pdf.chapter_body_key("Prenotato da")
                        pdf.chapter_body_value(seat_info['nominativo'])
                        pdf.chapter_body_key("Note")
                        pdf.chapter_body_value(seat_info['note'])

                        qr_text = (f'RICEVUTA DI PRENOTAZIONE\n'
                                   f'Evento: {st.session_state["evento"]}\n'
                                   f'Posto: {seat_info["posto"]}\n'
                                   f"Note: {seat_info['note']}")

                        generate_qr_code(qr_text, qr_code_path)

                    pdf.add_qr_code(qr_code_path)

                    pdf.output(file_path)

                # Leggi il contenuto del file PDF
                with open(file_path, "rb") as file:
                    file_data = file.read()

                st.download_button(
                    label="Scarica Ricevuta",
                    help=f"Scarica la Ricevuta di Prenotazione per il Posto: {seat_info['posto']}",
                    data=file_data,
                    file_name=f"Ricevuta Prenotazione - POSTO: {seat_info['posto']} - {st.session_state['evento']}.pdf",
                    mime="application/pdf")

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
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning(f"Prenotazione NON effettuata. Il posto è stato appena prenotato da qualcun altro.")
                    time.sleep(2)
                    st.rerun()

    st.button('Cambia Evento', on_click=esci_evento)
    st.button("Esci", on_click=logout)


# ----------------------------
# GESTIONE DELLE PAGINE

if st.session_state['evento']:
    show_billing_page()
elif st.session_state.logged_in:
    pagina_scelta_evento()
else:
    show_login_page()
