import streamlit_authenticator as stauth

# Remplace 'MADLAL19791979' par le mot de passe que tu as choisi
hashed_password = stauth.Hasher(['MADLAL19791979']).generate()
print(hashed_password[0])
