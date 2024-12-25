from firebase_admin import credentials, initialize_app, db

RTDB = None


def initialize_firebase(cred_path: str) -> None:
    global RTDB
    cred = credentials.Certificate(cred_path)
    initialize_app(
        cred,
        {
            "databaseURL": "https://aigrid-23256-default-rtdb.asia-southeast1.firebasedatabase.app",
            "storageBucket": "aigrid-23256.appspot.com",
        },
    )

    RTDB = db.reference("/")

    if RTDB is None:
        raise RuntimeError("Realtime database client is nil after initialization")


initialize_firebase("credentials/aigrid/sa.json")


def get_whiteboard_data() -> str:
    whiteboard_data = RTDB.child("whiteboard").child("content").get()
    return whiteboard_data
