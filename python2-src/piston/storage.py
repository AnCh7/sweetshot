from __future__ import absolute_import
import argparse
import shutil
import time
import os
import sqlite3
from .aes import AESCipher
from appdirs import user_data_dir
from datetime import datetime
import logging
from binascii import hexlify
import random
import hashlib
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

timeformat = u"%Y%m%d-%H%M%S"


class DataDir(object):
    u""" This class ensures that the user's data is stored in its OS
        preotected user directory:

        **OSX:**

         * `~/Library/Application Support/<AppName>`

        **Windows:**

         * `C:\Documents and Settings\<User>\Application Data\Local Settings\<AppAuthor>\<AppName>`
         * `C:\Documents and Settings\<User>\Application Data\<AppAuthor>\<AppName>`

        **Linux:**

         * `~/.local/share/<AppName>`

         Furthermore, it offers an interface to generated backups
         in the `backups/` directory every now and then.
    """

    appname = u"piston"
    appauthor = u"ChainSquad GmbH"
    storageDatabase = u"wallet.sqlite"

    data_dir = user_data_dir(appname, appauthor)
    sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

    def __init__(self):
        #: Storage
        self.check_legacy_v1()
        self.check_legacy_v2()
        self.mkdir_p()

    def check_legacy_v1(self):
        u""" Look for legacy wallet and move to new directory
        """
        appname = u"piston"
        appauthor = u"Fabian Schuh"
        storageDatabase = u"piston.sqlite"
        data_dir = user_data_dir(appname, appauthor)
        sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

        if os.path.isdir(data_dir) and not os.path.isdir(self.data_dir):
            # Move whole directory
            shutil.copytree(data_dir, self.data_dir)
            # Copy piston.sql to steem.sql (no deletion!)
            shutil.copy(sqlDataBaseFile, self.sqlDataBaseFile)
            log.info(u"Your settings have been moved to {}".format(self.data_dir))

    def check_legacy_v2(self):
        u""" Look for legacy wallet and move to new directory
        """
        appname = u"steem"
        appauthor = u"Fabian Schuh"
        storageDatabase = u"steem.sqlite"
        data_dir = user_data_dir(appname, appauthor)
        sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

        if os.path.isdir(data_dir) and not os.path.exists(self.sqlDataBaseFile):
            # Move whole directory
            try:
                shutil.copytree(data_dir, self.data_dir)
            except FileExistsError:
                pass
            # Copy piston.sql to steem.sql (no deletion!)
            shutil.copy(sqlDataBaseFile, self.sqlDataBaseFile)
            log.info(u"Your settings have been moved to {}".format(self.sqlDataBaseFile))

    def mkdir_p(self):
        u""" Ensure that the directory in which the data is stored
            exists
        """
        if os.path.isdir(self.data_dir):
            return
        else:
            try:
                os.makedirs(self.data_dir)
            except FileExistsError:
                return
            except OSError:
                raise

    def sqlite3_backup(self, dbfile, backupdir):
        u""" Create timestamped database copy
        """
        if not os.path.isdir(backupdir):
            os.mkdir(backupdir)
        backup_file = os.path.join(
            backupdir,
            os.path.basename(self.storageDatabase) +
            datetime.now().strftime(u"-" + timeformat))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        # Lock database before making a backup
        cursor.execute(u'begin immediate')
        # Make new backup file
        shutil.copyfile(dbfile, backup_file)
        log.info(u"Creating {}...".format(backup_file))
        # Unlock database
        connection.rollback()
        configStorage[u"lastBackup"] = datetime.now().strftime(timeformat)

    def clean_data(self):
        u""" Delete files older than 70 days
        """
        log.info(u"Cleaning up old backups")
        for filename in os.listdir(self.data_dir):
            backup_file = os.path.join(self.data_dir, filename)
            if os.stat(backup_file).st_ctime < (time.time() - 70 * 86400):
                if os.path.isfile(backup_file):
                    os.remove(backup_file)
                    log.info(u"Deleting {}...".format(backup_file))

    def refreshBackup(self):
        u""" Make a new backup
        """
        backupdir = os.path.join(self.data_dir, u"backups")
        self.sqlite3_backup(self.sqlDataBaseFile, backupdir)
        self.clean_data()


class Key(DataDir):
    __tablename__ = u'keys'

    def __init__(self):
        u""" This is the key storage that stores the public key and the
            (possibly encrypted) private key in the `keys` table in the
            SQLite3 database.
        """
        super(Key, self).__init__()

    def exists_table(self):
        u""" Check if the database table exists
        """
        query = (u"SELECT name FROM sqlite_master " +
                 u"WHERE type='table' AND name=?",
                 (self.__tablename__, ))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        return True if cursor.fetchone() else False

    def create_table(self):
        u""" Create the new table in the SQLite database
        """
        query = (u'CREATE TABLE %s (' % self.__tablename__ +
                 u'id INTEGER PRIMARY KEY AUTOINCREMENT,' +
                 u'pub STRING(256),' +
                 u'wif STRING(256)' +
                 u')')
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    def getPublicKeys(self):
        u""" Returns the public keys stored in the database
        """
        query = (u"SELECT pub from %s " % (self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return [x[0] for x in results]

    def getPrivateKeyForPublicKey(self, pub):
        u""" Returns the (possibly encrypted) private key that
            corresponds to a public key

           :param str pub: Public key

           The encryption scheme is BIP38
        """
        query = (u"SELECT wif from %s " % (self.__tablename__) +
                 u"WHERE pub=?",
                 (pub,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        key = cursor.fetchone()
        if key:
            return key[0]
        else:
            return None

    def updateWif(self, pub, wif):
        u""" Change the wif to a pubkey

           :param str pub: Public key
           :param str wif: Private key
        """
        query = (u"UPDATE %s " % self.__tablename__ +
                 u"SET wif=? WHERE pub=?",
                 (wif, pub))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def add(self, wif, pub):
        u""" Add a new public/private key pair (correspondence has to be
            checked elsewhere!)

           :param str pub: Public key
           :param str wif: Private key
        """
        if self.getPrivateKeyForPublicKey(pub):
            raise ValueError(u"Key already in storage")
        query = (u'INSERT INTO %s (pub, wif) ' % self.__tablename__ +
                 u'VALUES (?, ?)',
                 (pub, wif))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def delete(self, pub):
        u""" Delete the key identified as `pub`

           :param str pub: Public key
        """
        query = (u"DELETE FROM %s " % (self.__tablename__) +
                 u"WHERE pub=?",
                 (pub,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()


class Configuration(DataDir):
    __tablename__ = u"config"

    #: Default configuration
    config_defaults = {
        u"categories_sorting": u"trending",
        u"default_vote_weight": 100.0,
        u"format": u"markdown",
        u"limit": 10,
        u"list_sorting": u"trending",
        u"node": u"wss://this.piston.rocks,wss://steemd.steemit.com,wss://node.steem.ws",
        u"post_category": u"steem",
        u"rpcpassword": u"",
        u"rpcuser": u"",
        u"web:port": 5054,
        u"web:debug": False,
        u"web:host": u"127.0.0.1",
        u"web:nobroadcast": False,
        u"prefix": u"STM"
    }

    def __init__(self):
        u""" This is the configuration storage that stores key/value
            pairs in the `config` table of the SQLite3 database.
        """
        super(Configuration, self).__init__()

    def exists_table(self):
        u""" Check if the database table exists
        """
        query = (u"SELECT name FROM sqlite_master " +
                 u"WHERE type='table' AND name=?",
                 (self.__tablename__, ))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        return True if cursor.fetchone() else False

    def create_table(self):
        u""" Create the new table in the SQLite database
        """
        query = (u'CREATE TABLE %s (' % self.__tablename__ +
                 u'id INTEGER PRIMARY KEY AUTOINCREMENT,' +
                 u'key STRING(256),' +
                 u'value STRING(256)' +
                 u')')
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    def checkBackup(self):
        u""" Backup the SQL database every 7 days
        """
        if (u"lastBackup" not in configStorage or
                configStorage[u"lastBackup"] == u""):
            print u"No backup has been created yet!"
            self.refreshBackup()
        try:
            if (
                datetime.now() -
                datetime.strptime(configStorage[u"lastBackup"],
                                  timeformat)
            ).days > 7:
                print u"Backups older than 7 days!"
                self.refreshBackup()
        except:
            self.refreshBackup()

    def _haveKey(self, key):
        u""" Is the key `key` available int he configuration?
        """
        query = (u"SELECT value FROM %s " % (self.__tablename__) +
                 u"WHERE key=?",
                 (key,)
                 )
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        return True if cursor.fetchone() else False

    def __getitem__(self, key):
        u""" This method behaves differently from regular `dict` in that
            it returns `None` if a key is not found!
        """
        query = (u"SELECT value FROM %s " % (self.__tablename__) +
                 u"WHERE key=?",
                 (key,)
                 )
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        result = cursor.fetchone()
        if result:
            value = result[0]
        else:
            if key in self.config_defaults:
                value = self.config_defaults[key]
            else:
                return None
        # arrays are "," separated (especially for nodes)
        if isinstance(value, unicode) and u"," in value:
            return value.split(u",")
        else:
            return value

    def get(self, key, default=None):
        u""" Return the key if exists or a default value
        """
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    def __contains__(self, key):
        if self._haveKey(key) or key in self.config_defaults:
            return True
        else:
            return False

    def __setitem__(self, key, value):
        if self._haveKey(key):
            query = (u"UPDATE %s " % self.__tablename__ +
                     u"SET value=? WHERE key=?",
                     (value, key))
        else:
            query = (u"INSERT INTO %s " % self.__tablename__ +
                     u"(key, value) VALUES (?, ?)",
                     (key, value))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def delete(self, key):
        u""" Delete a key from the configuration store
        """
        query = (u"DELETE FROM %s " % (self.__tablename__) +
                 u"WHERE key=?",
                 (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def __iter__(self):
        query = (u"SELECT key, value from %s " % (self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        r = {}
        for key, value in cursor.fetchall():
            r[key] = value
        return iter(r)

    def __len__(self):
        query = (u"SELECT id from %s " % (self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        return len(cursor.fetchall())


class WrongMasterPasswordException(Exception):
    pass


class MasterPassword(object):
    u""" The keys are encrypted with a Masterpassword that is stored in
        the configurationStore. It has a checksum to verify correctness
        of the password
    """

    password = u""
    decrypted_master = u""

    #: This key identifies the encrypted master password stored in the confiration
    config_key = u"encrypted_master_password"

    def __init__(self, password):
        u""" The encrypted private keys in `keys` are encrypted with a
            random encrypted masterpassword that is stored in the
            configuration.

            The password is used to encrypt this masterpassword. To
            decrypt the keys stored in the keys database, one must use
            BIP38, decrypt the masterpassword from the configuration
            store with the user password, and use the decrypted
            masterpassword to decrypt the BIP38 encrypted private keys
            from the keys storage!

            :param str password: Password to use for en-/de-cryption
        """
        self.password = password
        if self.config_key not in configStorage:
            self.newMaster()
            self.saveEncrytpedMaster()
        else:
            self.decryptEncryptedMaster()

    def decryptEncryptedMaster(self):
        u""" Decrypt the encrypted masterpassword
        """
        aes = AESCipher(self.password)
        checksum, encrypted_master = configStorage[self.config_key].split(u"$")
        try:
            decrypted_master = aes.decrypt(encrypted_master)
        except:
            raise WrongMasterPasswordException
        if checksum != self.deriveChecksum(decrypted_master):
            raise WrongMasterPasswordException
        self.decrypted_master = decrypted_master

    def saveEncrytpedMaster(self):
        u""" Store the encrypted master password in the configuration
            store
        """
        configStorage[self.config_key] = self.getEncryptedMaster()

    def newMaster(self):
        u""" Generate a new random masterpassword
        """
        # make sure to not overwrite an existing key
        if (self.config_key in configStorage and
                configStorage[self.config_key]):
            return
        self.decrypted_master = hexlify(os.urandom(32)).decode(u"ascii")

    def deriveChecksum(self, s):
        u""" Derive the checksum
        """
        checksum = hashlib.sha256(str(s).encode("ascii")).hexdigest()
        return checksum[:4]

    def getEncryptedMaster(self):
        u""" Obtain the encrypted masterkey
        """
        if not self.decrypted_master:
            raise Exception(u"master not decrypted")
        aes = AESCipher(self.password)
        return u"{}${}".format(self.deriveChecksum(self.decrypted_master),
                              aes.encrypt(self.decrypted_master))

    def changePassword(self, newpassword):
        u""" Change the password
        """
        self.password = newpassword
        self.saveEncrytpedMaster()

    def purge(self):
        u""" Remove the masterpassword from the configuration store
        """
        configStorage[self.config_key] = u""


# Create keyStorage
keyStorage = Key()
configStorage = Configuration()

# Create Tables if database is brand new
if not configStorage.exists_table():
    configStorage.create_table()

newKeyStorage = False
if not keyStorage.exists_table():
    newKeyStorage = True
    keyStorage.create_table()
