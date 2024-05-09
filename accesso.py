# Funzione per verificare se una combinazione user-password esiste nella reference credenziali
def check_credentials(user, password, ref):
    credentials = ref.get()
    if not credentials:
        print("Nessuna credenziale trovata.")
        return False

    for credential in credentials:
        if credential and credential.get('user').lower() == user and credential.get('password').lower() == password:
            return True
    return False