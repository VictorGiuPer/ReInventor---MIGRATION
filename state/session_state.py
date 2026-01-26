# state/session_state.py

class SessionState:
    """
    A thin abstraction over a dict to replace st.session_state.
    This will later be backed by Flask sessions.
    """

    def __init__(self, backing_store: dict):
        self._state = backing_store

    def get(self, key, default=None):
        return self._state.get(key, default)

    def set_value(self, key, value):
        self._state[key] = value

    def delete(self, key):
        if key in self._state:
            del self._state[key]

    def keys(self):
        return self._state.keys()

    def contains(self, key):
        return key in self._state

    def clear_except(self, allowed_keys: set[str]):
        for key in list(self._state.keys()):
            if key not in allowed_keys:
                del self._state[key]

    # Optional sugar (helps readability later)
    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self._state[key] = value

    def __contains__(self, key):
        return key in self._state
