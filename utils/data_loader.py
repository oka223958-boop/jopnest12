"""
def _save_pickle(obj, path: str) -> None:
    """Serialize an object to disk with pickle."""
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def _load_pickle(path: str):
    """Deserialize an object from a pickle file."""
    with open(path, "rb") as f:
        return pickle.load(f)
