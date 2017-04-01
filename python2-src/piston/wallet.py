from __future__ import absolute_import
import logging
import os

from graphenebase import bip38
from pistonbase.account import PrivateKey, GraphenePrivateKey

from .account import Account
from .exceptions import (
    InvalidWifError,
    WalletExists
)

log = logging.getLogger(__name__)


class Wallet(object):
    u""" The wallet is meant to maintain access to private keys for
        your accounts. It either uses manually provided private keys
        or uses a SQLite database managed by storage.py.

        :param SteemNodeRPC rpc: RPC connection to a Steem node
        :param array,dict,string keys: Predefine the wif keys to shortcut the wallet database

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, steemlibs loads the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call ``Steem()`` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to ``Steem()``.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, ``posting`` or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!
    """
    keys = []
    rpc = None
    masterpassword = None

    # Keys from database
    configStorage = None
    MasterPassword = None
    keyStorage = None

    # Manually provided keys
    keys = {}  # struct with pubkey as key and wif as value
    keyMap = {}  # type:wif pairs to force certain keys

    def __init__(self, rpc, *args, **kwargs):
        from .storage import configStorage
        self.configStorage = configStorage

        # RPC
        Wallet.rpc = rpc

        # Prefix?
        if Wallet.rpc:
            self.prefix = Wallet.rpc.chain_params[u"prefix"]
        else:
            # If not connected, load prefix from config
            self.prefix = self.configStorage[u"prefix"]

        # Compatibility after name change from wif->keys
        if u"wif" in kwargs and u"keys" not in kwargs:
            kwargs[u"keys"] = kwargs[u"wif"]

        if u"keys" in kwargs:
            self.setKeys(kwargs[u"keys"])
        else:
            u""" If no keys are provided manually we load the SQLite
                keyStorage
            """
            from .storage import (keyStorage,
                                  MasterPassword)
            self.MasterPassword = MasterPassword
            self.keyStorage = keyStorage

    def setKeys(self, loadkeys):
        u""" This method is strictly only for in memory keys that are
            passed to Wallet/Steem with the ``keys`` argument
        """
        log.debug(u"Force setting of private keys. Not using the wallet database!")
        if isinstance(loadkeys, dict):
            Wallet.keyMap = loadkeys
            loadkeys = list(loadkeys.values())
        elif not isinstance(loadkeys, list):
            loadkeys = [loadkeys]

        for wif in loadkeys:
            try:
                key = PrivateKey(wif)
            except:
                raise InvalidWifError
            Wallet.keys[format(key.pubkey, self.prefix)] = unicode(key)

    def unlock(self, pwd=None):
        u""" Unlock the wallet database
        """
        if not self.created():
            self.newWallet()

        if (self.masterpassword is None and
                self.configStorage[self.MasterPassword.config_key]):
            if pwd is None:
                pwd = self.getPassword()
            masterpwd = self.MasterPassword(pwd)
            self.masterpassword = masterpwd.decrypted_master

    def lock(self):
        u""" Lock the wallet database
        """
        self.masterpassword = None

    def locked(self):
        u""" Is the wallet database locked?
        """
        return False if self.masterpassword else True

    def changePassphrase(self):
        u""" Change the passphrase for the wallet database
        """
        # Open Existing Wallet
        pwd = self.getPassword()
        masterpwd = self.MasterPassword(pwd)
        self.masterpassword = masterpwd.decrypted_master
        # Provide new passphrase
        print u"Please provide the new password"
        newpwd = self.getPassword(confirm=True)
        # Change passphrase
        masterpwd.changePassword(newpwd)

    def created(self):
        u""" Do we have a wallet database already?
        """
        if len(self.getPublicKeys()):
            # Already keys installed
            return True
        elif self.MasterPassword.config_key in self.configStorage:
            # no keys but a master password
            return True
        else:
            return False

    def newWallet(self):
        u""" Create a new wallet database
        """
        if self.created():
            raise WalletExists(u"You already have created a wallet!")
        print u"Please provide a password for the new wallet"
        pwd = self.getPassword(confirm=True)
        masterpwd = self.MasterPassword(pwd)
        self.masterpassword = masterpwd.decrypted_master

    def encrypt_wif(self, wif):
        u""" Encrypt a wif key
        """
        self.unlock()
        return format(bip38.encrypt(PrivateKey(wif), self.masterpassword), u"encwif")

    def decrypt_wif(self, encwif):
        u""" decrypt a wif key
        """
        try:
            # Try to decode as wif
            PrivateKey(encwif)
            return encwif
        except:
            pass
        self.unlock()
        return format(bip38.decrypt(encwif, self.masterpassword), u"wif")

    def getPassword(self, confirm=False, text=u'Passphrase: '):
        u""" Obtain a password from the user
        """
        import getpass
        if u"UNLOCK" in os.environ:
            # overwrite password from environmental variable
            return os.environ.get(u"UNLOCK")
        if confirm:
            # Loop until both match
            while True:
                pw = self.getPassword(confirm=False)
                if not pw:
                    print u"You cannot chosen an empty password! " +
                        u"If you want to automate the use of the libs, " +
                        u"please use the `UNLOCK` environmental variable!"
                    continue
                else:
                    pwck = self.getPassword(
                        confirm=False,
                        text=u"Confirm Passphrase: "
                    )
                    if (pw == pwck):
                        return(pw)
                    else:
                        print u"Given Passphrases do not match!"
        else:
            # return just one password
            return getpass.getpass(text)

    def addPrivateKey(self, wif):
        u""" Add a private key to the wallet database
        """
        # it could be either graphenebase or pistonbase so we can't check the type directly
        if isinstance(wif, PrivateKey) or isinstance(wif, GraphenePrivateKey):
            wif = unicode(wif)
        try:
            pub = format(PrivateKey(wif).pubkey, self.prefix)
        except:
            raise InvalidWifError(u"Invalid Private Key Format. Please use WIF!")

        if self.keyStorage:
            # Test if wallet exists
            if not self.created():
                self.newWallet()
            self.keyStorage.add(self.encrypt_wif(wif), pub)

    def getPrivateKeyForPublicKey(self, pub):
        u""" Obtain the private key for a given public key

            :param str pub: Public Key
        """
        if(Wallet.keys):
            if pub in Wallet.keys:
                return Wallet.keys[pub]
            elif len(Wallet.keys) == 1:
                # If there is only one key in my overwrite-storage, then
                # use that one! Whether it will has sufficient
                # authorization is left to ensure by the developer
                return list(self.keys.values())[0]
        else:
            # Test if wallet exists
            if not self.created():
                self.newWallet()

            return self.decrypt_wif(self.keyStorage.getPrivateKeyForPublicKey(pub))

    def removePrivateKeyFromPublicKey(self, pub):
        u""" Remove a key from the wallet database
        """
        if self.keyStorage:
            # Test if wallet exists
            if not self.created():
                self.newWallet()
            self.keyStorage.delete(pub)

    def removeAccount(self, account):
        u""" Remove all keys associated with a given account
        """
        accounts = self.getAccounts()
        for a in accounts:
            if a[u"name"] == account:
                self.removePrivateKeyFromPublicKey(a[u"pubkey"])

    def getOwnerKeyForAccount(self, name):
        u""" Obtain owner Private Key for an account from the wallet database
        """
        if u"owner" in Wallet.keyMap:
            return Wallet.keyMap.get(u"owner")
        else:
            account = self.rpc.get_account(name)
            if not account:
                return
            for authority in account[u"owner"][u"key_auths"]:
                key = self.getPrivateKeyForPublicKey(authority[0])
                if key:
                    return key
            return False

    def getPostingKeyForAccount(self, name):
        u""" Obtain owner Posting Key for an account from the wallet database
        """
        if u"posting" in Wallet.keyMap:
            return Wallet.keyMap.get(u"posting")
        else:
            account = self.rpc.get_account(name)
            if not account:
                return
            for authority in account[u"posting"][u"key_auths"]:
                key = self.getPrivateKeyForPublicKey(authority[0])
                if key:
                    return key
            return False

    def getMemoKeyForAccount(self, name):
        u""" Obtain owner Memo Key for an account from the wallet database
        """
        if u"memo" in Wallet.keyMap:
            return Wallet.keyMap.get(u"memo")
        else:
            account = self.rpc.get_account(name)
            if not account:
                return
            key = self.getPrivateKeyForPublicKey(account[u"memo_key"])
            if key:
                return key
            return False

    def getActiveKeyForAccount(self, name):
        u""" Obtain owner Active Key for an account from the wallet database
        """
        if u"active" in Wallet.keyMap:
            return Wallet.keyMap.get(u"active")
        else:
            account = self.rpc.get_account(name)
            if not account:
                return
            for authority in account[u"active"][u"key_auths"]:
                key = self.getPrivateKeyForPublicKey(authority[0])
                if key:
                    return key
            return False

    def getAccountFromPrivateKey(self, wif):
        u""" Obtain account name from private key
        """
        pub = format(PrivateKey(wif).pubkey, self.prefix)
        return self.getAccountFromPublicKey(pub)

    def getAccountFromPublicKey(self, pub):
        u""" Obtain account name from public key
        """
        # FIXME, this only returns the first associated key.
        # If the key is used by multiple accounts, this
        # will surely lead to undesired behavior
        names = self.rpc.get_key_references([pub], api=u"account_by_key")[0]
        if not names:
            return None
        else:
            return names[0]

    def getAccount(self, pub):
        u""" Get the account data for a public key
        """
        name = self.getAccountFromPublicKey(pub)
        if not name:
            return {u"name": None,
                    u"type": None,
                    u"pubkey": pub
                    }
        else:
            try:
                account = Account(name)
            except:
                return
            keyType = self.getKeyType(account, pub)
            return {u"name": name,
                    u"account": account,
                    u"type": keyType,
                    u"pubkey": pub
                    }

    def getKeyType(self, account, pub):
        u""" Get key type
        """
        for authority in [u"owner", u"posting", u"active"]:
            for key in account[authority][u"key_auths"]:
                if pub == key[0]:
                    return authority
        if pub == account[u"memo_key"]:
            return u"memo"
        return None

    def getAccounts(self):
        u""" Return all accounts installed in the wallet database
        """
        pubkeys = self.getPublicKeys()
        accounts = []
        for pubkey in pubkeys:
            # Filter those keys not for our network
            if pubkey[:len(self.prefix)] == self.prefix:
                accounts.append(self.getAccount(pubkey))
        return accounts

    def getAccountsWithPermissions(self):
        u""" Return a dictionary for all installed accounts with their
            corresponding installed permissions
        """
        accounts = [self.getAccount(a) for a in self.getPublicKeys()]
        r = {}
        for account in accounts:
            name = account[u"name"]
            if not name:
                continue
            type = account[u"type"]
            if name not in r:
                r[name] = {u"posting": False,
                           u"owner": False,
                           u"active": False,
                           u"memo": False}
            r[name][type] = True
        return r

    def getPublicKeys(self):
        u""" Return all installed public keys
        """
        if self.keyStorage:
            return self.keyStorage.getPublicKeys()
        else:
            return list(Wallet.keys.keys())
