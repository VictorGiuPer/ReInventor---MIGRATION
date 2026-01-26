# state/flask_session_state.py

class FlaskSessionState:
    """
    Streamlit-like session state wrapper for Flask.
    Wraps flask.session.
    """

    def __init__(self, flask_session):
        self._session = flask_session

    def __getitem__(self, key):
        return self._session[key]

    def __setitem__(self, key, value):
        self._session[key] = value

    def get(self, key, default=None):
        return self._session.get(key, default)

    def __contains__(self, key):
        return key in self._session

    def keys(self):
        return self._session.keys()
    
    def clear(self):
        """Clear entire session state"""
        self._session.clear()

    def clear_except(self, allowed_keys: set):
        for key in list(self._session.keys()):
            if key not in allowed_keys:
                del self._session[key]
