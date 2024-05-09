import streamlit as st

# CSS personalizzato per modificare il colore dei pulsanti
st.markdown("""
    <style>
    .stButton>button {
        background-color: #FF5733;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 10em;
        border: 2px solid #FFC300;
    }
    </style>
    """, unsafe_allow_html=True)

# Pulsante in Streamlit
if st.button('Pulsante Personalizzato'):
    st.write('Hai cliccato il pulsante!')
