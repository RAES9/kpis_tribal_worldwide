import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase/ios-assistant-5f37f-firebase-adminsdk-hd4vl-1497ed076f.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://ios-assistant-5f37f-default-rtdb.firebaseio.com'
    })


def verify_user(user_id):
    """
    Verifica si el usuario con el user_id tiene acceso en Firebase Realtime Database.
    """
    ref = db.reference('users')
    users_list = ref.get()

    if users_list and user_id in users_list:
        return True
    return False