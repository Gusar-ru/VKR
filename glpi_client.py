import requests
import base64
import importlib

def _load_glpi_sdk():
    for name in ("glpi_api", "py_glpi"):
        try:
            mod = importlib.import_module(name)
            return mod
        except Exception:
            pass
    try:
        mod = importlib.import_module("glpi")
        if hasattr(mod, "GlpiTicket"):
            return mod
    except Exception:
        pass
    return None

class GLPI:
    def __init__(self, url, user, password, app_token=None):
        self.url = url.rstrip('/') + '/'
        self.user = user
        self.password = password
        self.app_token = app_token
        self.session_token = None
        self.headers = {
            'Content-Type': 'application/json'
        }
        if self.app_token:
            self.headers['App-Token'] = self.app_token
        self.sdk = None
        self.sdk_client = None
        sdk_mod = _load_glpi_sdk()
        if sdk_mod and self.app_token:
            try:
                if hasattr(sdk_mod, "GLPI"):
                    self.sdk_client = sdk_mod.GLPI(self.url.rstrip('/'), self.app_token, (self.user, self.password), verify_certs=False, use_headers=True)
                elif hasattr(sdk_mod, "GlpiTicket"):
                    self.sdk = sdk_mod.GlpiTicket(self.url.rstrip('/'), self.app_token, username=self.user, password=self.password)
            except Exception:
                self.sdk_client = None
                self.sdk = None

    def init_session(self):
        init_url = self.url + "initSession"
        headers = {'Content-Type': 'application/json'}
        if self.app_token:
            headers['App-Token'] = self.app_token
        auth_str = f"{self.user}:{self.password}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        headers['Authorization'] = f"Basic {auth_b64}"
        try:
            response = requests.get(init_url, headers=headers, verify=False)
            if response.status_code != 200:
                return False
            data = response.json()
            self.session_token = data.get('session_token')
            if not self.session_token:
                return False
            if self.app_token:
                self.headers['App-Token'] = self.app_token
            self.headers['Session-Token'] = self.session_token
            return True
        except Exception:
            return False

    def kill_session(self):
        if not self.session_token:
            return
        kill_url = self.url + "killSession"
        try:
            requests.get(kill_url, headers=self.headers, verify=False)
            self.session_token = None
        except:
            pass

    def get_tickets(self):
        if self.sdk_client:
            try:
                return self.sdk_client.get_all_items("Ticket")
            except Exception as e:
                return f"SDK error: {e}"
        if self.sdk:
            try:
                return self.sdk.get_all()
            except Exception as e:
                return f"SDK error: {e}"
        if not self.session_token:
            if not self.init_session():
                return "Failed to login to GLPI"
        url = self.url + "Ticket"
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"Error fetching tickets: {e}"

    def create_ticket(self, title, content):
        if self.sdk_client:
            try:
                data = {"name": title, "content": content, "urgency": 3}
                return self.sdk_client.add("Ticket", data)
            except Exception as e:
                return f"SDK error: {e}"
        if self.sdk:
            try:
                sdk_mod = _load_glpi_sdk()
                TicketModel = getattr(sdk_mod, "Ticket", None)
                if TicketModel:
                    t = TicketModel(name=title, content=content, urgency=3)
                else:
                    t = {"name": title, "content": content, "urgency": 3}
                return self.sdk.create(t)
            except Exception as e:
                return f"SDK error: {e}"
        if not self.session_token:
            if not self.init_session():
                return "Failed to login to GLPI"
        url = self.url + "Ticket"
        payload = {
            "input": {
                "name": title,
                "content": content,
                "urgency": 3
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"Error creating ticket: {e}"
