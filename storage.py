import os
from nio.store import DefaultStore, MatrixStore
from nio.store.file_trustdb import KeyStore

class Storage(DefaultStore):
    def __init__(self, user_id, device_id, store_path, database_name, pickle_key):
        self.user_id = user_id
        self.device_id = device_id
        self.store_path = store_path
        self.database_name = database_name
        self.pickle_key = pickle_key
        
        # Initialize the parent MatrixStore (skipping DefaultStore's init which fails on Windows)
        MatrixStore.__init__(self, user_id, device_id, store_path, database_name, pickle_key)
        
        # Manually initialize the trust databases with sanitized filenames
        self._init_trust_db()

    def _init_trust_db(self):
        # Sanitize user_id for Windows filenames (replace : with _)
        sanitized_user_id = self.user_id.replace(":", "_").replace("@", "")
        
        trust_file_path = os.path.join(self.store_path, f"{sanitized_user_id}_{self.device_id}.trusted_devices")
        self.trust_db = KeyStore(trust_file_path)

        blacklist_file_path = os.path.join(self.store_path, f"{sanitized_user_id}_{self.device_id}.blacklisted_devices")
        self.blacklist_db = KeyStore(blacklist_file_path)

        ignore_file_path = os.path.join(self.store_path, f"{sanitized_user_id}_{self.device_id}.ignored_devices")
        self.ignore_db = KeyStore(ignore_file_path)
