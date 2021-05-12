import datetime
from honahlee.utils import generate_name
from honahlee.core import BaseService
from passlib.context import CryptContext
from typing import Union


class AccountService(BaseService):
    setup_order = 1

    def __init__(self, app):
        super().__init__(app)
        self.accounts = dict()
        self.names = dict()
        self.docs = dict()
        self.couch = None
        self.db = None
        self.crypt = CryptContext(schemes=['argon2'])

    async def setup(self):
        self.couch = self.app.services['couch']
        self.db = self.couch["accounts"]

        async for doc in self.db.all_docs.docs():
            self.docs[doc["_id"]] = doc
            self.names[doc["username"].upper()] = doc

    async def create_account(self, username: str, password: str, host: str = None, validator: str = "default"):
        if not (vali := self.app.config.regex.get(validator, None)):
            return False, f"Invalid regex validator: {validator}"
        username = username.strip()
        if not username:
            return False, "No username provided."
        if not vali.match(username):
            return False, "Invalid username."
        if username.upper() in self.names:
            return False, "That name is already in use."
        if not password:
            return False, "No password provided."
        new_id = generate_name("account_", self.accounts.keys())
        data = {
            "username": username,
            "password_hash": self.crypt.hash(password),
            "created": datetime.datetime.utcnow().timestamp(),
        }
        entry = await self.db.create(new_id, data=data)
        await entry.save()
        self.accounts[new_id] = entry
        self.names[username.upper()] = entry
        return entry, False

    async def rename_account(self, _id: str, new_name: str, validator: str = "default"):
        if not (acc := self.accounts.get(_id, None)):
            return False, "Account not found."
        new_name = new_name.strip()
        if not (vali := self.app.config.regex.get(validator, None)):
            return False, f"Invalid regex validator: {validator}"
        if not vali.match(new_name):
            return False, "Invalid username."
        if (found := self.names.get(new_name.upper(), None)):
            if acc != found:
                return False, "That name is already in use."

    async def find_account(self, username: str):
        if (acc := self.names.get(username.strip().upper(), None)):
            return acc, None
        else:
            return False, "Account not found."

    async def authenticate(self, account: Union[Account, str], secret: str):
        if isinstance(account, Account):
            acc = account
        else:
            if not (acc := self.accounts.get(account.strip().upper(), None)):
                return False, "Account not found."
        acc["password_hash"] = self.crypt.hash(secret)
        acc["password_changed"] = datetime.datetime.utcnow().timestamp()