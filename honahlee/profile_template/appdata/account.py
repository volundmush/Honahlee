from honahlee.core import BaseConfig
import re


class Config(BaseConfig):

    def __init__(self):
        super().__init__()
        self.name = "account"
        self.application = "honahlee_account.app.Application"

    def _config_regex(self):
        self.regex["default"] = re.compile(r"(?s)^(\w|\.|-| |')+$")
        self.regex["emailish"] = re.compile(r"(?s)^(\w|\.|-| |'|@)+$")

    def _config_classes(self):
        self.classes['services']['couch'] = 'honahlee_portal.app.CouchDBService'
