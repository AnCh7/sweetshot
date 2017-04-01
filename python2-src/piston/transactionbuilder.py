from __future__ import absolute_import
import logging

from piston.instance import shared_steem_instance
from pistonbase import transactions, operations
from pistonbase.account import PrivateKey
from pistonbase.operations import Operation
from pistonbase.signedtransactions import Signed_Transaction

from .account import Account
from .exceptions import (
    InsufficientAuthorityError,
    MissingKeyError,
    InvalidKeyFormat
)
log = logging.getLogger(__name__)


class TransactionBuilder(dict):
    u""" This class simplifies the creation of transactions by adding
        operations and signers.
    """

    def __init__(self, tx={}, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()

        self.op = []
        self.wifs = []
        if not isinstance(tx, dict):
            raise ValueError(u"Invalid TransactionBuilder Format")
        super(TransactionBuilder, self).__init__(tx)

    def appendOps(self, ops):
        if isinstance(ops, list):
            for op in ops:
                self.op.append(op)
        else:
            self.op.append(ops)
        self.constructTx()

    def appendSigner(self, account, permission):
        u""" Try to obtain the wif key from the wallet by telling which account
            and permission is supposed to sign the transaction
        """
        assert permission in [u"active", u"owner", u"posting"], u"Invalid permission"
        account = Account(account, steem_instance=self.steem)
        required_treshold = account[permission][u"weight_threshold"]

        def fetchkeys(account, level=0):
            if level > 2:
                return []
            r = []
            for authority in account[permission][u"key_auths"]:
                wif = self.steem.wallet.getPrivateKeyForPublicKey(authority[0])
                if wif:
                    r.append([wif, authority[1]])

            if sum([x[1] for x in r]) < required_treshold:
                # go one level deeper
                for authority in account[permission][u"account_auths"]:
                    auth_account = Account(authority[0], steem_instance=self.steem)
                    r.extend(fetchkeys(auth_account, level + 1))

            return r
        keys = fetchkeys(account)
        self.wifs.extend([x[0] for x in keys])

    def appendWif(self, wif):
        if wif:
            try:
                PrivateKey(wif)
                self.wifs.append(wif)
            except:
                raise InvalidKeyFormat

    def constructTx(self):
        if isinstance(self.op, list):
            ops = [Operation(o) for o in self.op]
        else:
            ops = [Operation(self.op)]
        expiration = transactions.formatTimeFromNow(self.steem.expiration)
        ref_block_num, ref_block_prefix = transactions.getBlockParams(self.steem.rpc)
        tx = Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        super(TransactionBuilder, self).__init__(tx.json())

    def sign(self):
        u""" Sign a provided transaction witht he provided key(s)

            :param dict tx: The transaction to be signed and returned
            :param string wifs: One or many wif keys to use for signing
                a transaction. If not present, the keys will be loaded
                from the wallet as defined in "missing_signatures" key
                of the transactions.
        """

        # We need to set the default prefix, otherwise pubkeys are
        # presented wrongly!
        if self.steem.rpc:
            operations.default_prefix = self.steem.rpc.chain_params[u"prefix"]
        elif u"blockchain" in self:
            operations.default_prefix = self[u"blockchain"][u"prefix"]

        try:
            signedtx = Signed_Transaction(**self.json())
        except:
            raise ValueError(u"Invalid TransactionBuilder Format")

        if not any(self.wifs):
            raise MissingKeyError

        signedtx.sign(self.wifs, chain=self.steem.rpc.chain_params)
        self[u"signatures"].extend(signedtx.json().get(u"signatures"))

    def verify_authority(self):
        u""" Verify the authority of the signed transaction
        """
        try:
            if not self.steem.rpc.verify_authority(self.json()):
                raise InsufficientAuthorityError
        except Exception, e:
            raise e

    def broadcast(self):
        u""" Broadcast a transaction to the Steem network

            :param tx tx: Signed transaction to broadcast
        """
        if self.steem.nobroadcast:
            log.warning(u"Not broadcasting anything!")
            return self

        try:
            if not self.steem.rpc.verify_authority(self.json()):
                raise InsufficientAuthorityError
        except Exception, e:
            raise e

        try:
            self.steem.rpc.broadcast_transaction(self.json(), api=u"network_broadcast")
        except Exception, e:
            raise e

        return self

    def clear(self):
        u""" Clear the transaction builder and start from scratch
        """
        self.ops = []
        self.wifs = []
        super(TransactionBuilder, self).__init__({})

    def addSigningInformation(self, account, permission):
        u""" This is a private method that adds side information to a
            unsigned/partial transaction in order to simplify later
            signing (e.g. for multisig or coldstorage)
        """
        accountObj = Account(account, steem_instance=self.steem)
        authority = accountObj[permission]
        # We add a required_authorities to be able to identify
        # how to sign later. This is an array, because we
        # may later want to allow multiple operations per tx
        self.update({u"required_authorities": {
            account: authority
        }})
        for account_auth in authority[u"account_auths"]:
            account_auth_account = Account(account_auth[0], steem_instance=self.steem)
            self[u"required_authorities"].update({
                account_auth[0]: account_auth_account.get(permission)
            })

        # Try to resolve required signatures for offline signing
        self[u"missing_signatures"] = [
            x[0] for x in authority[u"key_auths"]
        ]
        # Add one recursion of keys from account_auths:
        for account_auth in authority[u"account_auths"]:
            account_auth_account = Account(account_auth[0], steem_instance=self.steem)
            self[u"missing_signatures"].extend(
                [x[0] for x in account_auth_account[permission][u"key_auths"]]
            )
        self[u"blockchain"] = self.steem.rpc.chain_params

    def json(self):
        return dict(self)

    def appendMissingSignatures(self, wifs):
        missing_signatures = self.get(u"missing_signatures", [])
        for pub in missing_signatures:
            wif = self.steem.wallet.getPrivateKeyForPublicKey(pub)
            if wif:
                self.appendWif(wif)
