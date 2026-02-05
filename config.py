import yaml
import os

class Config:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.homeserver = self.config['matrix']['homeserver']
        self.user_id = self.config['matrix']['user_id']
        self.password = self.config['matrix']['password']
        self.device_id = self.config['matrix']['device_id']
        self.store_path = self.config['matrix']['store_path']
        self.access_token = self.config['matrix'].get('access_token')
        
        self.glpi_url = self.config['glpi']['url']
        self.glpi_user = self.config['glpi']['user']
        self.glpi_password = self.config['glpi']['password']
        self.glpi_app_token = self.config['glpi'].get('app_token')
        self.glpi_user_token = self.config['glpi'].get('user_token')
