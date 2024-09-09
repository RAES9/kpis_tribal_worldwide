import requests

client_id = '1233485159571918898'
client_secret = '-_swjz6-M6gOVJUq1upRJBpEiS-TnUNk'
redirect_uri = "https://kpistribalworldwide.streamlit.app"


def get_access_token(code):
    """
    Obtiene el token de acceso de Discord utilizando el código de autorización.
    """
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    return response.json()


def get_user_info(access_token):
    """
    Obtiene la información del usuario autenticado utilizando el token de acceso.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://discord.com/api/users/@me', headers=headers)
    return response.json()
