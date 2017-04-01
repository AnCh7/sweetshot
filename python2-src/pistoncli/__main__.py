#!/usr/bin/env python3

from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import sys
import os
import argparse
import json
import re
from pprint import pprint
from pistonbase.account import PrivateKey, PublicKey, Address
import pistonbase.transactions as transactions
from piston.storage import configStorage as config
from piston.utils import (
    resolveIdentifier,
    yaml_parse_file,
    formatTime,
    strfage,
)
from piston.steem import Steem
from piston.amount import Amount
from piston.account import Account
from piston.post import Post
from piston.blockchain import Blockchain
from piston.block import Block
from piston.dex import Dex
from piston.witness import Witness
import frontmatter
import time
from prettytable import PrettyTable
import logging
from .ui import (
    dump_recursive_parents,
    dump_recursive_comments,
    list_posts,
    markdownify,
    format_operation_details,
    confirm,
    print_permissions,
    get_terminal
)
from piston.exceptions import AccountDoesNotExistsException
import pkg_resources  # part of setuptools
from io import open


availableConfigurationKeys = [
    u"default_author",
    u"default_voter",
    u"default_account",
    u"node",
    u"rpcuser",
    u"rpcpassword",
    u"default_vote_weight",
    u"list_sorting",
    u"categories_sorting",
    u"limit",
    u"post_category",
]


def main():
    global args

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=u"Command line tool to interact with the Steem network"
    )

    u"""
        Default settings for all tools
    """
    parser.add_argument(
        u'--node',
        type=unicode,
        default=config[u"node"],
        help=u'Websocket URL for public Steem API (default: "wss://this.piston.rocks/")'
    )
    parser.add_argument(
        u'--rpcuser',
        type=unicode,
        default=config[u"rpcuser"],
        help=u'Websocket user if authentication is required'
    )
    parser.add_argument(
        u'--rpcpassword',
        type=unicode,
        default=config[u"rpcpassword"],
        help=u'Websocket password if authentication is required'
    )
    parser.add_argument(
        u'--nobroadcast', u'-d',
        action=u'store_true',
        help=u'Do not broadcast anything'
    )
    parser.add_argument(
        u'--nowallet', u'-p',
        action=u'store_true',
        help=u'Do not load the wallet'
    )
    parser.add_argument(
        u'--unsigned', u'-x',
        action=u'store_true',
        help=u'Do not try to sign the transaction'
    )
    parser.add_argument(
        u'--expires', u'-e',
        default=30,
        help=u'Expiration time in seconds (defaults to 30)'
    )
    parser.add_argument(
        u'--verbose', u'-v',
        type=int,
        default=3,
        help=u'Verbosity'
    )
    parser.add_argument(
        u'--version',
        action=u'version',
        version=u'%(prog)s {version}'.format(
            version=pkg_resources.require(u"piston-cli")[0].version
        )
    )

    subparsers = parser.add_subparsers(help=u'sub-command help')

    u"""
        Command "set"
    """
    setconfig = subparsers.add_parser(u'set', help=u'Set configuration')
    setconfig.add_argument(
        u'key',
        type=unicode,
        choices=availableConfigurationKeys,
        help=u'Configuration key'
    )
    setconfig.add_argument(
        u'value',
        type=unicode,
        help=u'Configuration value'
    )
    setconfig.set_defaults(command=u"set")

    u"""
        Command "config"
    """
    configconfig = subparsers.add_parser(u'config', help=u'Show local configuration')
    configconfig.set_defaults(command=u"config")

    u"""
        Command "info"
    """
    parser_info = subparsers.add_parser(u'info', help=u'Show infos about piston and Steem')
    parser_info.set_defaults(command=u"info")
    parser_info.add_argument(
        u'objects',
        nargs=u'*',
        type=unicode,
        help=u'General information about the blockchain, a block, an account name, a post, a public key, ...'
    )

    u"""
        Command "changewalletpassphrase"
    """
    changepasswordconfig = subparsers.add_parser(u'changewalletpassphrase', help=u'Change wallet password')
    changepasswordconfig.set_defaults(command=u"changewalletpassphrase")

    u"""
        Command "addkey"
    """
    addkey = subparsers.add_parser(u'addkey', help=u'Add a new key to the wallet')
    addkey.add_argument(
        u'--unsafe-import-key',
        nargs=u'*',
        type=unicode,
        help=u'private key to import into the wallet (unsafe, unless you delete your bash history)'
    )
    addkey.set_defaults(command=u"addkey")

    u"""
        Command "delkey"
    """
    delkey = subparsers.add_parser(u'delkey', help=u'Delete keys from the wallet')
    delkey.add_argument(
        u'pub',
        nargs=u'*',
        type=unicode,
        help=u'the public key to delete from the wallet'
    )
    delkey.set_defaults(command=u"delkey")

    u"""
        Command "getkey"
    """
    getkey = subparsers.add_parser(u'getkey', help=u'Dump the privatekey of a pubkey from the wallet')
    getkey.add_argument(
        u'pub',
        type=unicode,
        help=u'the public key for which to show the private key'
    )
    getkey.set_defaults(command=u"getkey")

    u"""
        Command "listkeys"
    """
    listkeys = subparsers.add_parser(u'listkeys', help=u'List available keys in your wallet')
    listkeys.set_defaults(command=u"listkeys")

    u"""
        Command "listaccounts"
    """
    listaccounts = subparsers.add_parser(u'listaccounts', help=u'List available accounts in your wallet')
    listaccounts.set_defaults(command=u"listaccounts")

    u"""
        Command "list"
    """
    parser_list = subparsers.add_parser(u'list', help=u'List posts on Steem')
    parser_list.set_defaults(command=u"list")
    parser_list.add_argument(
        u'--start',
        type=unicode,
        help=u'Start list from this identifier (pagination)'
    )
    parser_list.add_argument(
        u'--category',
        type=unicode,
        help=u'Only posts with in this category'
    )
    parser_list.add_argument(
        u'--sort',
        type=unicode,
        default=config[u"list_sorting"],
        choices=[u"trending", u"created", u"active", u"cashout", u"payout", u"votes", u"children", u"hot"],
        help=u'Sort posts'
    )
    parser_list.add_argument(
        u'--limit',
        type=int,
        default=config[u"limit"],
        help=u'Limit posts by number'
    )
    parser_list.add_argument(
        u'--columns',
        type=unicode,
        nargs=u"+",
        help=u'Display custom columns'
    )

    u"""
        Command "categories"
    """
    parser_categories = subparsers.add_parser(u'categories', help=u'Show categories')
    parser_categories.set_defaults(command=u"categories")
    parser_categories.add_argument(
        u'--sort',
        type=unicode,
        default=config[u"categories_sorting"],
        choices=[u"trending", u"best", u"active", u"recent"],
        help=u'Sort categories'
    )
    parser_categories.add_argument(
        u'category',
        nargs=u"?",
        type=unicode,
        help=u'Only categories used by this author'
    )
    parser_categories.add_argument(
        u'--limit',
        type=int,
        default=config[u"limit"],
        help=u'Limit categories by number'
    )

    u"""
        Command "read"
    """
    parser_read = subparsers.add_parser(u'read', help=u'Read a post on Steem')
    parser_read.set_defaults(command=u"read")
    parser_read.add_argument(
        u'post',
        type=unicode,
        help=u'@author/permlink-identifier of the post to read (e.g. @xeroc/python-steem-0-1)'
    )
    parser_read.add_argument(
        u'--full',
        action=u'store_true',
        help=u'Show full header information (YAML formated)'
    )
    parser_read.add_argument(
        u'--comments',
        action=u'store_true',
        help=u'Also show all comments'
    )
    parser_read.add_argument(
        u'--parents',
        type=int,
        default=0,
        help=u'Show x parents for the reply'
    )
    parser_read.add_argument(
        u'--format',
        type=unicode,
        default=config[u"format"],
        help=u'Format post',
        choices=[u"markdown", u"raw"],
    )

    u"""
        Command "post"
    """
    parser_post = subparsers.add_parser(u'post', help=u'Post something new')
    parser_post.set_defaults(command=u"post")
    parser_post.add_argument(
        u'--author',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Publish post as this user (requires to have the key installed in the wallet)'
    )
    parser_post.add_argument(
        u'--permlink',
        type=unicode,
        required=False,
        help=u'The permlink (together with the author identifies the post uniquely)'
    )
    parser_post.add_argument(
        u'--category',
        default=config[u"post_category"],
        type=unicode,
        help=u'Specify category'
    )
    parser_post.add_argument(
        u'--tags',
        default=[],
        help=u'Specify tags',
        nargs=u'*',
    )
    parser_post.add_argument(
        u'--title',
        type=unicode,
        required=False,
        help=u'Title of the post'
    )
    parser_post.add_argument(
        u'--file',
        type=unicode,
        default=None,
        help=u'Filename to open. If not present, or "-", stdin will be used'
    )

    u"""
        Command "reply"
    """
    reply = subparsers.add_parser(u'reply', help=u'Reply to an existing post')
    reply.set_defaults(command=u"reply")
    reply.add_argument(
        u'replyto',
        type=unicode,
        help=u'@author/permlink-identifier of the post to reply to (e.g. @xeroc/python-steem-0-1)'
    )
    reply.add_argument(
        u'--author',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Publish post as this user (requires to have the key installed in the wallet)'
    )
    reply.add_argument(
        u'--permlink',
        type=unicode,
        required=False,
        help=u'The permlink (together with the author identifies the post uniquely)'
    )
    reply.add_argument(
        u'--title',
        type=unicode,
        required=False,
        help=u'Title of the post'
    )
    reply.add_argument(
        u'--file',
        type=unicode,
        required=False,
        help=u'Send file as responds. If "-", read from stdin'
    )

    u"""
        Command "edit"
    """
    parser_edit = subparsers.add_parser(u'edit', help=u'Edit to an existing post')
    parser_edit.set_defaults(command=u"edit")
    parser_edit.add_argument(
        u'post',
        type=unicode,
        help=u'@author/permlink-identifier of the post to edit to (e.g. @xeroc/python-steem-0-1)'
    )
    parser_edit.add_argument(
        u'--author',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Post an edit as another author'
    )
    parser_edit.add_argument(
        u'--file',
        type=unicode,
        required=False,
        help=u'Patch with content of this file'
    )
    parser_edit.add_argument(
        u'--replace',
        action=u'store_true',
        help=u"Don't patch but replace original post (will make you lose votes)"
    )

    u"""
        Command "upvote"
    """
    parser_upvote = subparsers.add_parser(u'upvote', help=u'Upvote a post')
    parser_upvote.set_defaults(command=u"upvote")
    parser_upvote.add_argument(
        u'post',
        type=unicode,
        help=u'@author/permlink-identifier of the post to upvote to (e.g. @xeroc/python-steem-0-1)'
    )
    parser_upvote.add_argument(
        u'--voter',
        type=unicode,
        required=False,
        default=config[u"default_voter"],
        help=u'The voter account name'
    )
    parser_upvote.add_argument(
        u'--weight',
        type=float,
        default=config[u"default_vote_weight"],
        required=False,
        help=u'Actual weight (from 0.1 to 100.0)'
    )

    u"""
        Command "downvote"
    """
    parser_downvote = subparsers.add_parser(u'downvote', help=u'Downvote a post')
    parser_downvote.set_defaults(command=u"downvote")
    parser_downvote.add_argument(
        u'--voter',
        type=unicode,
        default=config[u"default_voter"],
        help=u'The voter account name'
    )
    parser_downvote.add_argument(
        u'post',
        type=unicode,
        help=u'@author/permlink-identifier of the post to downvote to (e.g. @xeroc/python-steem-0-1)'
    )
    parser_downvote.add_argument(
        u'--weight',
        type=float,
        default=config[u"default_vote_weight"],
        required=False,
        help=u'Actual weight (from 0.1 to 100.0)'
    )

    u"""
        Command "replies"
    """
    replies = subparsers.add_parser(u'replies', help=u'Show recent replies to your posts')
    replies.set_defaults(command=u"replies")
    replies.add_argument(
        u'--author',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Show replies to this author'
    )
    replies.add_argument(
        u'--limit',
        type=int,
        default=config[u"limit"],
        help=u'Limit posts by number'
    )

    u"""
        Command "transfer"
    """
    parser_transfer = subparsers.add_parser(u'transfer', help=u'Transfer STEEM')
    parser_transfer.set_defaults(command=u"transfer")
    parser_transfer.add_argument(
        u'to',
        type=unicode,
        help=u'Recepient'
    )
    parser_transfer.add_argument(
        u'amount',
        type=float,
        help=u'Amount to transfer'
    )
    parser_transfer.add_argument(
        u'asset',
        type=unicode,
        choices=[u"STEEM", u"SBD", u"GOLOS", u"GBG"],
        help=u'Asset to transfer (i.e. STEEM or SDB)'
    )
    parser_transfer.add_argument(
        u'memo',
        type=unicode,
        nargs=u"?",
        default=u"",
        help=u'Optional memo'
    )
    parser_transfer.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Transfer from this account'
    )

    u"""
        Command "powerup"
    """
    parser_powerup = subparsers.add_parser(u'powerup', help=u'Power up (vest STEEM as STEEM POWER)')
    parser_powerup.set_defaults(command=u"powerup")
    parser_powerup.add_argument(
        u'amount',
        type=unicode,
        help=u'Amount of VESTS to powerup'
    )
    parser_powerup.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Powerup from this account'
    )
    parser_powerup.add_argument(
        u'--to',
        type=unicode,
        required=False,
        default=None,
        help=u'Powerup this account'
    )

    u"""
        Command "powerdown"
    """
    parser_powerdown = subparsers.add_parser(u'powerdown', help=u'Power down (start withdrawing STEEM from piston POWER)')
    parser_powerdown.set_defaults(command=u"powerdown")
    parser_powerdown.add_argument(
        u'amount',
        type=unicode,
        help=u'Amount of VESTS to powerdown'
    )
    parser_powerdown.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'powerdown from this account'
    )

    u"""
        Command "powerdownroute"
    """
    parser_powerdownroute = subparsers.add_parser(u'powerdownroute', help=u'Setup a powerdown route')
    parser_powerdownroute.set_defaults(command=u"powerdownroute")
    parser_powerdownroute.add_argument(
        u'to',
        type=unicode,
        default=config[u"default_author"],
        help=u'The account receiving either VESTS/SteemPower or STEEM.'
    )
    parser_powerdownroute.add_argument(
        u'--percentage',
        type=float,
        default=100,
        help=u'The percent of the withdraw to go to the "to" account'
    )
    parser_powerdownroute.add_argument(
        u'--account',
        type=unicode,
        default=config[u"default_author"],
        help=u'The account which is powering down'
    )
    parser_powerdownroute.add_argument(
        u'--auto_vest',
        action=u'store_true',
        help=(u'Set to true if the from account should receive the VESTS as'
              u'VESTS, or false if it should receive them as STEEM.')
    )

    u"""
        Command "convert"
    """
    parser_convert = subparsers.add_parser(u'convert', help=u'Convert STEEMDollars to Steem (takes a week to settle)')
    parser_convert.set_defaults(command=u"convert")
    parser_convert.add_argument(
        u'amount',
        type=float,
        help=u'Amount of SBD to convert'
    )
    parser_convert.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Convert from this account'
    )

    u"""
        Command "balance"
    """
    parser_balance = subparsers.add_parser(u'balance', help=u'Show the balance of one more more accounts')
    parser_balance.set_defaults(command=u"balance")
    parser_balance.add_argument(
        u'account',
        type=unicode,
        nargs=u"*",
        default=config[u"default_author"],
        help=u'balance of these account (multiple accounts allowed)'
    )

    u"""
        Command "history"
    """
    parser_history = subparsers.add_parser(u'history', help=u'Show the history of an account')
    parser_history.set_defaults(command=u"history")
    parser_history.add_argument(
        u'account',
        type=unicode,
        nargs=u"?",
        default=config[u"default_author"],
        help=u'History of this account'
    )
    parser_history.add_argument(
        u'--limit',
        type=int,
        default=config[u"limit"],
        help=u'Limit number of entries'
    )
    parser_history.add_argument(
        u'--memos',
        action=u'store_true',
        help=u'Show (decode) memos'
    )
    parser_history.add_argument(
        u'--csv',
        action=u'store_true',
        help=u'Output in CSV format'
    )
    parser_history.add_argument(
        u'--first',
        type=int,
        default=99999999999999,
        help=u'Transaction number (#) of the last transaction to show.'
    )
    parser_history.add_argument(
        u'--types',
        type=unicode,
        nargs=u"*",
        default=[],
        help=u'Show only these operation types'
    )
    parser_history.add_argument(
        u'--exclude_types',
        type=unicode,
        nargs=u"*",
        default=[],
        help=u'Do not show operations of this type'
    )

    u"""
        Command "interest"
    """
    interest = subparsers.add_parser(u'interest', help=u'Get information about interest payment')
    interest.set_defaults(command=u"interest")
    interest.add_argument(
        u'account',
        type=unicode,
        nargs=u"*",
        default=config[u"default_author"],
        help=u'Inspect these accounts'
    )

    u"""
        Command "permissions"
    """
    parser_permissions = subparsers.add_parser(u'permissions', help=u'Show permissions of an account')
    parser_permissions.set_defaults(command=u"permissions")
    parser_permissions.add_argument(
        u'account',
        type=unicode,
        nargs=u"?",
        default=config[u"default_author"],
        help=u'Account to show permissions for'
    )

    u"""
        Command "allow"
    """
    parser_allow = subparsers.add_parser(u'allow', help=u'Allow an account/key to interact with your account')
    parser_allow.set_defaults(command=u"allow")
    parser_allow.add_argument(
        u'--account',
        type=unicode,
        nargs=u"?",
        default=config[u"default_author"],
        help=u'The account to allow action for'
    )
    parser_allow.add_argument(
        u'foreign_account',
        type=unicode,
        nargs=u"?",
        help=u'The account or key that will be allowed to interact as your account'
    )
    parser_allow.add_argument(
        u'--permission',
        type=unicode,
        default=u"posting",
        choices=[u"owner", u"posting", u"active"],
        help=(u'The permission to grant (defaults to "posting")')
    )
    parser_allow.add_argument(
        u'--weight',
        type=int,
        default=None,
        help=(u'The weight to use instead of the (full) threshold. '
              u'If the weight is smaller than the threshold, '
              u'additional signatures are required')
    )
    parser_allow.add_argument(
        u'--threshold',
        type=int,
        default=None,
        help=(u'The permission\'s threshold that needs to be reached '
              u'by signatures to be able to interact')
    )

    u"""
        Command "disallow"
    """
    parser_disallow = subparsers.add_parser(u'disallow', help=u'Remove allowance an account/key to interact with your account')
    parser_disallow.set_defaults(command=u"disallow")
    parser_disallow.add_argument(
        u'--account',
        type=unicode,
        nargs=u"?",
        default=config[u"default_author"],
        help=u'The account to disallow action for'
    )
    parser_disallow.add_argument(
        u'foreign_account',
        type=unicode,
        help=u'The account or key whose allowance to interact as your account will be removed'
    )
    parser_disallow.add_argument(
        u'--permission',
        type=unicode,
        default=u"posting",
        choices=[u"owner", u"posting", u"active"],
        help=(u'The permission to remove (defaults to "posting")')
    )
    parser_disallow.add_argument(
        u'--threshold',
        type=int,
        default=None,
        help=(u'The permission\'s threshold that needs to be reached '
              u'by signatures to be able to interact')
    )

    u"""
        Command "newaccount"
    """
    parser_newaccount = subparsers.add_parser(u'newaccount', help=u'Create a new account')
    parser_newaccount.set_defaults(command=u"newaccount")
    parser_newaccount.add_argument(
        u'accountname',
        type=unicode,
        help=u'New account name'
    )
    parser_newaccount.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Account that pays the fee'
    )

    u"""
        Command "importaccount"
    """
    parser_importaccount = subparsers.add_parser(u'importaccount', help=u'Import an account using a passphrase')
    parser_importaccount.set_defaults(command=u"importaccount")
    parser_importaccount.add_argument(
        u'account',
        type=unicode,
        help=u'Account name'
    )
    parser_importaccount.add_argument(
        u'--roles',
        type=unicode,
        nargs=u"*",
        default=[u"active", u"posting", u"memo"],  # no owner
        help=u'Import specified keys (owner, active, posting, memo)'
    )

    u"""
        Command "updateMemoKey"
    """
    parser_updateMemoKey = subparsers.add_parser(u'updatememokey', help=u'Update an account\'s memo key')
    parser_updateMemoKey.set_defaults(command=u"updatememokey")
    parser_updateMemoKey.add_argument(
        u'--account',
        type=unicode,
        nargs=u"?",
        default=config[u"default_author"],
        help=u'The account to updateMemoKey action for'
    )
    parser_updateMemoKey.add_argument(
        u'--key',
        type=unicode,
        default=None,
        help=u'The new memo key'
    )

    u"""
        Command "approvewitness"
    """
    parser_approvewitness = subparsers.add_parser(u'approvewitness', help=u'Approve a witnesses')
    parser_approvewitness.set_defaults(command=u"approvewitness")
    parser_approvewitness.add_argument(
        u'witness',
        type=unicode,
        help=u'Witness to approve'
    )
    parser_approvewitness.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Your account'
    )

    u"""
        Command "disapprovewitness"
    """
    parser_disapprovewitness = subparsers.add_parser(u'disapprovewitness', help=u'Disapprove a witnesses')
    parser_disapprovewitness.set_defaults(command=u"disapprovewitness")
    parser_disapprovewitness.add_argument(
        u'witness',
        type=unicode,
        help=u'Witness to disapprove'
    )
    parser_disapprovewitness.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Your account'
    )

    u"""
        Command "sign"
    """
    parser_sign = subparsers.add_parser(u'sign', help=u'Sign a provided transaction with available and required keys')
    parser_sign.set_defaults(command=u"sign")
    parser_sign.add_argument(
        u'--file',
        type=unicode,
        required=False,
        help=u'Load transaction from file. If "-", read from stdin (defaults to "-")'
    )

    u"""
        Command "broadcast"
    """
    parser_broadcast = subparsers.add_parser(u'broadcast', help=u'broadcast a signed transaction')
    parser_broadcast.set_defaults(command=u"broadcast")
    parser_broadcast.add_argument(
        u'--file',
        type=unicode,
        required=False,
        help=u'Load transaction from file. If "-", read from stdin (defaults to "-")'
    )

    u"""
        Command "orderbook"
    """
    orderbook = subparsers.add_parser(u'orderbook', help=u'Obtain orderbook of the internal market')
    orderbook.set_defaults(command=u"orderbook")
    orderbook.add_argument(
        u'--chart',
        action=u'store_true',
        help=u"Enable charting (requires matplotlib)"
    )

    u"""
        Command "buy"
    """
    parser_buy = subparsers.add_parser(u'buy', help=u'Buy STEEM or SBD from the internal market')
    parser_buy.set_defaults(command=u"buy")
    parser_buy.add_argument(
        u'amount',
        type=float,
        help=u'Amount to buy'
    )
    parser_buy.add_argument(
        u'asset',
        type=unicode,
        choices=[u"STEEM", u"SBD", u"GOLOS", u"GBG"],
        help=u'Asset to buy (i.e. STEEM or SDB)'
    )
    parser_buy.add_argument(
        u'price',
        type=float,
        help=u'Limit buy price denoted in (SBD per STEEM)'
    )
    parser_buy.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_account"],
        help=u'Buy with this account (defaults to "default_account")'
    )

    u"""
        Command "sell"
    """
    parser_sell = subparsers.add_parser(u'sell', help=u'Sell STEEM or SBD from the internal market')
    parser_sell.set_defaults(command=u"sell")
    parser_sell.add_argument(
        u'amount',
        type=float,
        help=u'Amount to sell'
    )
    parser_sell.add_argument(
        u'asset',
        type=unicode,
        choices=[u"STEEM", u"SBD", u"GOLOS", u"GBG"],
        help=u'Asset to sell (i.e. STEEM or SDB)'
    )
    parser_sell.add_argument(
        u'price',
        type=float,
        help=u'Limit sell price denoted in (SBD per STEEM)'
    )
    parser_sell.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_account"],
        help=u'Sell from this account (defaults to "default_account")'
    )
    u"""
        Command "cancel"
    """
    parser_cancel = subparsers.add_parser(u'cancel', help=u'Cancel order in the internal market')
    parser_cancel.set_defaults(command=u"cancel")
    parser_cancel.add_argument(
        u'orderid',
        type=int,
        help=u'Orderid'
    )
    parser_cancel.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_account"],
        help=u'Cancel from this account (defaults to "default_account")'
    )

    u"""
        Command "resteem"
    """
    parser_resteem = subparsers.add_parser(u'resteem', help=u'Resteem an existing post')
    parser_resteem.set_defaults(command=u"resteem")
    parser_resteem.add_argument(
        u'identifier',
        type=unicode,
        help=u'@author/permlink-identifier of the post to resteem'
    )
    parser_resteem.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'Resteem as this user (requires to have the key installed in the wallet)'
    )

    u"""
        Command "follow"
    """
    parser_follow = subparsers.add_parser(u'follow', help=u'Follow another account')
    parser_follow.set_defaults(command=u"follow")
    parser_follow.add_argument(
        u'follow',
        type=unicode,
        help=u'Account to follow'
    )
    parser_follow.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_account"],
        help=u'Follow from this account'
    )
    parser_follow.add_argument(
        u'--what',
        type=unicode,
        required=False,
        nargs=u"*",
        default=[u"blog"],
        help=u'Follow these objects (defaults to "blog")'
    )

    u"""
        Command "unfollow"
    """
    parser_unfollow = subparsers.add_parser(u'unfollow', help=u'unfollow another account')
    parser_unfollow.set_defaults(command=u"unfollow")
    parser_unfollow.add_argument(
        u'unfollow',
        type=unicode,
        help=u'Account to unfollow'
    )
    parser_unfollow.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_account"],
        help=u'Unfollow from this account'
    )
    parser_unfollow.add_argument(
        u'--what',
        type=unicode,
        required=False,
        nargs=u"*",
        default=[],
        help=u'Unfollow these objects (defaults to "blog")'
    )

    u"""
        Command "setprofile"
    """
    parser_setprofile = subparsers.add_parser(u'setprofile', help=u'Set a variable in an account\'s profile')
    parser_setprofile.set_defaults(command=u"setprofile")
    parser_setprofile.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'setprofile as this user (requires to have the key installed in the wallet)'
    )
    parser_setprofileA = parser_setprofile.add_argument_group(u'Multiple keys at once')
    parser_setprofileA.add_argument(
        u'--pair',
        type=unicode,
        nargs=u'*',
        help=u'"Key=Value" pairs'
    )
    parser_setprofileB = parser_setprofile.add_argument_group(u'Just a single key')
    parser_setprofileB.add_argument(
        u'variable',
        type=unicode,
        nargs=u'?',
        help=u'Variable to set'
    )
    parser_setprofileB.add_argument(
        u'value',
        type=unicode,
        nargs=u'?',
        help=u'Value to set'
    )

    u"""
        Command "delprofile"
    """
    parser_delprofile = subparsers.add_parser(u'delprofile', help=u'Set a variable in an account\'s profile')
    parser_delprofile.set_defaults(command=u"delprofile")
    parser_delprofile.add_argument(
        u'--account',
        type=unicode,
        required=False,
        default=config[u"default_author"],
        help=u'delprofile as this user (requires to have the key installed in the wallet)'
    )
    parser_delprofile.add_argument(
        u'variable',
        type=unicode,
        nargs=u'*',
        help=u'Variable to set'
    )

    u"""
        Command "witnessupdate"
    """
    parser_witnessprops = subparsers.add_parser(u'witnessupdate', help=u'Change witness properties')
    parser_witnessprops.set_defaults(command=u"witnessupdate")
    parser_witnessprops.add_argument(
        u'--witness',
        type=unicode,
        default=config[u"default_account"],
        help=u'Witness name'
    )
    parser_witnessprops.add_argument(
        u'--maximum_block_size',
        type=float,
        required=False,
        help=u'Max block size'
    )
    parser_witnessprops.add_argument(
        u'--account_creation_fee',
        type=float,
        required=False,
        help=u'Account creation fee'
    )
    parser_witnessprops.add_argument(
        u'--sbd_interest_rate',
        type=float,
        required=False,
        help=u'SBD interest rate in percent'
    )
    parser_witnessprops.add_argument(
        u'--url',
        type=unicode,
        required=False,
        help=u'Witness URL'
    )
    parser_witnessprops.add_argument(
        u'--signing_key',
        type=unicode,
        required=False,
        help=u'Signing Key'
    )

    u"""
        Command "witnesscreate"
    """
    parser_witnesscreate = subparsers.add_parser(u'witnesscreate', help=u'Create a witness')
    parser_witnesscreate.set_defaults(command=u"witnesscreate")
    parser_witnesscreate.add_argument(
        u'witness',
        type=unicode,
        help=u'Witness name'
    )
    parser_witnesscreate.add_argument(
        u'signing_key',
        type=unicode,
        help=u'Signing Key'
    )
    parser_witnesscreate.add_argument(
        u'--maximum_block_size',
        type=float,
        default=u"65536",
        help=u'Max block size'
    )
    parser_witnesscreate.add_argument(
        u'--account_creation_fee',
        type=float,
        default=30,
        help=u'Account creation fee'
    )
    parser_witnesscreate.add_argument(
        u'--sbd_interest_rate',
        type=float,
        default=0.0,
        help=u'SBD interest rate in percent'
    )
    parser_witnesscreate.add_argument(
        u'--url',
        type=unicode,
        default=u"",
        help=u'Witness URL'
    )

    u"""
        Parse Arguments
    """
    args = parser.parse_args()

    # Logging
    log = logging.getLogger(__name__)
    verbosity = [u"critical",
                 u"error",
                 u"warn",
                 u"info",
                 u"debug"][int(min(args.verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter(u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)

    # GrapheneAPI logging
    if args.verbose > 4:
        verbosity = [u"critical",
                     u"error",
                     u"warn",
                     u"info",
                     u"debug"][int(min((args.verbose - 4), 4))]
        gphlog = logging.getLogger(u"graphenebase")
        gphlog.setLevel(getattr(logging, verbosity.upper()))
        gphlog.addHandler(ch)
    if args.verbose > 8:
        verbosity = [u"critical",
                     u"error",
                     u"warn",
                     u"info",
                     u"debug"][int(min((args.verbose - 8), 4))]
        gphlog = logging.getLogger(u"grapheneapi")
        gphlog.setLevel(getattr(logging, verbosity.upper()))
        gphlog.addHandler(ch)

    if not hasattr(args, u"command"):
        parser.print_help()
        sys.exit(2)

    # We don't require RPC for these commands
    rpc_not_required = [
        u"set",
        u"config",
        u""]
    if args.command not in rpc_not_required and args.command:
        options = {
            u"node": args.node,
            u"rpcuser": args.rpcuser,
            u"rpcpassword": args.rpcpassword,
            u"nobroadcast": args.nobroadcast,
            u"unsigned": args.unsigned,
            u"expires": args.expires
        }

        # preload wallet with empty keys
        if args.nowallet:
            options.update({u"wif": []})

        # Signing only requires the wallet, no connection
        # essential for offline/coldstorage signing
        if args.command == u"sign":
            options.update({u"offline": True})

        steem = Steem(**options)

    if args.command == u"set":
        if (args.key in [u"default_author",
                         u"default_voter",
                         u"default_account"] and
                args.value[0] == u"@"):
            args.value = args.value[1:]
        config[args.key] = args.value

    elif args.command == u"config":
        t = PrettyTable([u"Key", u"Value"])
        t.align = u"l"
        for key in config:
            if key in availableConfigurationKeys:  # hide internal config data
                t.add_row([key, config[key]])
        print t

    elif args.command == u"info":
        if not args.objects:
            t = PrettyTable([u"Key", u"Value"])
            t.align = u"l"
            blockchain = Blockchain(mode=u"head")
            info = blockchain.info()
            median_price = steem.rpc.get_current_median_history_price()
            steem_per_mvest = (
                Amount(info[u"total_vesting_fund_steem"]).amount /
                (Amount(info[u"total_vesting_shares"]).amount / 1e6)
            )
            price = (
                Amount(median_price[u"base"]).amount /
                Amount(median_price[u"quote"]).amount
            )
            for key in info:
                t.add_row([key, info[key]])
            t.add_row([u"steem per mvest", steem_per_mvest])
            t.add_row([u"internal price", price])
            print t.get_string(sortby=u"Key")

        for obj in args.objects:
            # Block
            if re.match(u"^[0-9]*$", obj):
                block = Block(obj)
                if block:
                    t = PrettyTable([u"Key", u"Value"])
                    t.align = u"l"
                    for key in sorted(block):
                        value = block[key]
                        if key == u"transactions":
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print t
                else:
                    print u"Block number %s unknown" % obj
            # Account name
            elif re.match(u"^[a-zA-Z0-9\-\._]{2,16}$", obj):
                from math import log10
                account = Account(obj)
                t = PrettyTable([u"Key", u"Value"])
                t.align = u"l"
                for key in sorted(account):
                    value = account[key]
                    if (key == u"json_metadata"):
                        value = json.dumps(
                            json.loads(value or u"{}"),
                            indent=4
                        )
                    if key in [u"posting",
                               u"witness_votes",
                               u"active",
                               u"owner"]:
                        value = json.dumps(value, indent=4)
                    if key == u"reputation" and int(value) > 0:
                        value = int(value)
                        rep = (max(log10(value) - 9, 0) * 9 + 25 if value > 0
                               else max(log10(-value) - 9, 0) * -9 + 25)
                        value = u"{:.2f} ({:d})".format(
                            rep, value
                        )
                    t.add_row([key, value])
                print t

                # witness available?
                try:
                    witness = Witness(obj)
                    t = PrettyTable([u"Key", u"Value"])
                    t.align = u"l"
                    for key in sorted(witness):
                        value = witness[key]
                        if key in [u"props",
                                   u"sbd_exchange_rate"]:
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print t
                except:
                    pass
            # Public Key
            elif re.match(u"^STM.{48,55}$", obj):
                account = steem.wallet.getAccountFromPublicKey(obj)
                if account:
                    t = PrettyTable([u"Account"])
                    t.align = u"l"
                    t.add_row([account])
                    print t
                else:
                    print u"Public Key not known" % obj
            # Post identifier
            elif re.match(u".*@.{3,16}/.*$", obj):
                post = Post(obj)
                if post:
                    t = PrettyTable([u"Key", u"Value"])
                    t.align = u"l"
                    for key in sorted(post):
                        value = post[key]
                        if (key in [u"tags",
                                    u"json_metadata",
                                    u"active_votes"
                                    ]):
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print t
                else:
                    print u"Post now known" % obj
            else:
                print u"Couldn't identify object to read"

    elif args.command == u"changewalletpassphrase":
        steem.wallet.changePassphrase()

    elif args.command == u"addkey":
        if args.unsafe_import_key:
            for key in args.unsafe_import_key:
                try:
                    steem.wallet.addPrivateKey(key)
                except Exception, e:
                    print unicode(e)
        else:
            import getpass
            while True:
                wifkey = getpass.getpass(u'Private Key (wif) [Enter to quit]:')
                if not wifkey:
                    break
                try:
                    steem.wallet.addPrivateKey(wifkey)
                except Exception, e:
                    print unicode(e)
                    continue

                installedKeys = steem.wallet.getPublicKeys()
                if len(installedKeys) == 1:
                    name = steem.wallet.getAccountFromPublicKey(installedKeys[0])
                    print u"=" * 30
                    print u"Setting new default user: %s" % name
                    print
                    print u"You can change these settings with:"
                    print u"    piston set default_author <account>"
                    print u"    piston set default_voter <account>"
                    print u"    piston set default_account <account>"
                    print u"=" * 30
                    config[u"default_author"] = name
                    config[u"default_voter"] = name
                    config[u"default_account"] = name

    elif args.command == u"delkey":
        if confirm(
            u"Are you sure you want to delete keys from your wallet?\n"
            u"This step is IRREVERSIBLE! If you don't have a backup, "
            u"You may lose access to your account!"
        ):
            for pub in args.pub:
                steem.wallet.removePrivateKeyFromPublicKey(pub)

    elif args.command == u"getkey":
        print steem.wallet.getPrivateKeyForPublicKey(args.pub)

    elif args.command == u"listkeys":
        t = PrettyTable([u"Available Key"])
        t.align = u"l"
        for key in steem.wallet.getPublicKeys():
            t.add_row([key])
        print t

    elif args.command == u"listaccounts":
        t = PrettyTable([u"Name", u"Type", u"Available Key"])
        t.align = u"l"
        for account in steem.wallet.getAccounts():
            t.add_row([
                account[u"name"] or u"n/a",
                account[u"type"] or u"n/a",
                account[u"pubkey"]
            ])
        print t

    elif args.command == u"reply":
        from textwrap import indent
        parent = steem.get_content(args.replyto)
        if parent[u"id"] == u"0.0.0":
            print u"Can't find post %s" % args.replyto
            return

        reply_message = indent(parent[u"body"], u"> ")

        post = frontmatter.Post(reply_message, **{
            u"title": args.title if args.title else u"Re: " + parent[u"title"],
            u"author": args.author if args.author else u"required",
            u"replyto": args.replyto,
        })

        meta, json_meta, message = yaml_parse_file(args, initial_content=post)

        for required in [u"author", u"title"]:
            if (required not in meta or
                    not meta[required] or
                    meta[required] == u"required"):
                print u"'%s' required!" % required
                # TODO, instead of terminating here, send the user back
                # to the EDITOR
                return

        pprint(steem.reply(
            meta[u"replyto"],
            message,
            title=meta[u"title"],
            author=meta[u"author"],
            meta=json_meta,
        ))

    elif args.command == u"post" or args.command == u"yaml":
        initmeta = {
            u"title": args.title or u"required",
            u"author": args.author or u"required",
            u"category": args.category or u"required",
            u"tags": args.tags or [],
            u"max_accepted_payout": u"1000000.000 %s" % steem.symbol(u"SBD"),
            u"percent_steem_dollars": 100,
            u"allow_votes": True,
            u"allow_curation_rewards": True,
        }

        post = frontmatter.Post(u"", **initmeta)
        meta, json_meta, body = yaml_parse_file(args, initial_content=post)

        # Default "app"
        if u"app" not in json_meta:
            version = pkg_resources.require(u"piston-cli")[0].version
            json_meta[u"app"] = u"piston/{}".format(version)

        if not body:
            print u"Empty body! Not posting!"
            return

        for required in [u"author", u"title", u"category"]:
            if (required not in meta or
                    not meta[required] or
                    meta[required] == u"required"):
                print u"'%s' required!" % required
                # TODO, instead of terminating here, send the user back
                # to the EDITOR
                return

        pprint(steem.post(
            meta[u"title"],
            body,
            author=meta[u"author"],
            category=meta[u"category"],
            meta=json_meta,
        ))

    elif args.command == u"edit":
        original_post = steem.get_content(args.post)

        edited_message = None
        if original_post[u"id"] == u"0.0.0":
            print u"Can't find post %s" % args.post
            return

        post = frontmatter.Post(original_post[u"body"], **{
            u"title": original_post[u"title"] + u" (immutable)",
            u"author": original_post[u"author"] + u" (immutable)",
            u"tags": original_post[u"tags"]
        })

        meta, json_meta, edited_message = yaml_parse_file(args, initial_content=post)
        pprint(steem.edit(
            args.post,
            edited_message,
            replace=args.replace,
            meta=json_meta,
        ))

    elif args.command == u"upvote" or args.command == u"downvote":
        post = Post(args.post)
        if args.command == u"downvote":
            weight = -float(args.weight)
        else:
            weight = +float(args.weight)
        if not args.voter:
            print u"Not voter provided!"
            return
        pprint(post.vote(weight, voter=args.voter))

    elif args.command == u"read":
        post_author, post_permlink = resolveIdentifier(args.post)

        if args.parents:
            # FIXME inconsistency, use @author/permlink instead!
            dump_recursive_parents(
                steem.rpc,
                post_author,
                post_permlink,
                args.parents,
                format=args.format
            )

        if not args.comments and not args.parents:
            post = steem.get_content(args.post)

            if post[u"id"] == u"0.0.0":
                print u"Can't find post %s" % args.post
                return
            if args.format == u"markdown":
                body = markdownify(post[u"body"])
            else:
                body = post[u"body"]

            if args.full:
                meta = {}
                for key in post:
                    if key in [u"steem", u"body"]:
                        continue
                    if isinstance(post[key], Amount):
                        meta[key] = unicode(post[key])
                    else:
                        meta[key] = post[key]
                yaml = frontmatter.Post(body, **meta)
                print frontmatter.dumps(yaml)
            else:
                print body

        if args.comments:
            dump_recursive_comments(
                steem.rpc,
                post_author,
                post_permlink,
                format=args.format
            )

    elif args.command == u"categories":
        categories = steem.get_categories(
            sort=args.sort,
            begin=args.category,
            limit=args.limit
        )
        t = PrettyTable([u"name", u"discussions", u"payouts"])
        t.align = u"l"
        for category in categories:
            t.add_row([
                category[u"name"],
                category[u"discussions"],
                category[u"total_payouts"],
            ])
        print t

    elif args.command == u"list":
        list_posts(
            steem.get_posts(
                limit=args.limit,
                sort=args.sort,
                category=args.category,
                start=args.start
            ),
            args.columns
        )

    elif args.command == u"replies":
        if not args.author:
            print u"Please specify an author via --author\n "
                  u"or define your default author with:\n"
                  u"   piston set default_author x"
        else:
            discussions = steem.get_replies(args.author)
            list_posts(discussions[0:args.limit])

    elif args.command == u"transfer":
        pprint(steem.transfer(
            args.to,
            args.amount,
            args.asset,
            memo=args.memo,
            account=args.account
        ))

    elif args.command == u"powerup":
        pprint(steem.transfer_to_vesting(
            args.amount,
            account=args.account,
            to=args.to
        ))

    elif args.command == u"powerdown":
        pprint(steem.withdraw_vesting(
            args.amount,
            account=args.account,
        ))

    elif args.command == u"convert":
        pprint(steem.convert(
            args.amount,
            account=args.account,
        ))

    elif args.command == u"powerdownroute":
        pprint(steem.set_withdraw_vesting_route(
            args.to,
            percentage=args.percentage,
            account=args.account,
            auto_vest=args.auto_vest
        ))

    elif args.command == u"balance":
        t = PrettyTable([u"Account", u"STEEM", u"SBD", u"VESTS",
                         u"VESTS (in STEEM)", u"Savings (STEEM)",
                         u"Savings (SBD)"])
        t.align = u"r"
        if isinstance(args.account, unicode):
            args.account = [args.account]
        for a in args.account:
            b = steem.get_balances(a)
            t.add_row([
                a,
                b[u"balance"],
                b[u"sbd_balance"],
                b[u"vesting_shares"],
                b[u"vesting_shares_steem"],
                b[u"savings_balance"],
                b[u"savings_sbd_balance"]
            ])
        print t

    elif args.command == u"history":
        header = [u"#", u"time (block)", u"operation", u"details"]
        if args.csv:
            import csv
            t = csv.writer(sys.stdout, delimiter=u";")
            t.writerow(header)
        else:
            t = PrettyTable(header)
            t.align = u"l"
        if isinstance(args.account, unicode):
            args.account = [args.account]
        if isinstance(args.types, unicode):
            args.types = [args.types]

        for a in args.account:
            for b in Account(a).rawhistory(
                first=args.first,
                limit=args.limit,
                only_ops=args.types,
                exclude_ops=args.exclude_types
            ):
                row = [
                    b[0],
                    u"%s (%s)" % (b[1][u"timestamp"], b[1][u"block"]),
                    b[1][u"op"][0],
                    format_operation_details(b[1][u"op"], memos=args.memos),
                ]
                if args.csv:
                    t.writerow(row)
                else:
                    t.add_row(row)
        if not args.csv:
            print t

    elif args.command == u"interest":
        t = PrettyTable([u"Account",
                         u"Last Interest Payment",
                         u"Next Payment",
                         u"Interest rate",
                         u"Interest"])
        t.align = u"r"
        if isinstance(args.account, unicode):
            args.account = [args.account]
        for a in args.account:
            i = steem.interest(a)

            t.add_row([
                a,
                i[u"last_payment"],
                u"in %s" % strfage(i[u"next_payment_duration"]),
                u"%.1f%%" % i[u"interest_rate"],
                u"%.3f %s" % (i[u"interest"], steem.symbol(u"SBD")),
            ])
        print t

    elif args.command == u"permissions":
        account = Account(args.account)
        print_permissions(account)

    elif args.command == u"allow":
        if not args.foreign_account:
            from pistonbase.account import PasswordKey
            pwd = get_terminal(text=u"Password for Key Derivation: ", confirm=True)
            args.foreign_account = format(PasswordKey(args.account, pwd, args.permission).get_public(), u"STM")
        pprint(steem.allow(
            args.foreign_account,
            weight=args.weight,
            account=args.account,
            permission=args.permission,
            threshold=args.threshold
        ))

    elif args.command == u"disallow":
        pprint(steem.disallow(
            args.foreign_account,
            account=args.account,
            permission=args.permission,
            threshold=args.threshold
        ))

    elif args.command == u"updatememokey":
        if not args.key:
            # Loop until both match
            from pistonbase.account import PasswordKey
            pw = get_terminal(text=u"Password for Memo Key: ", confirm=True, allowedempty=False)
            memo_key = PasswordKey(args.account, pw, u"memo")
            args.key = format(memo_key.get_public_key(), u"STM")
            memo_privkey = memo_key.get_private_key()
            # Add the key to the wallet
            if not args.nobroadcast:
                steem.wallet.addPrivateKey(memo_privkey)
        pprint(steem.update_memo_key(
            args.key,
            account=args.account
        ))

    elif args.command == u"newaccount":
        import getpass
        while True:
            pw = getpass.getpass(u"New Account Passphrase: ")
            if not pw:
                print u"You cannot chosen an empty password!"
                continue
            else:
                pwck = getpass.getpass(
                    u"Confirm New Account Passphrase: "
                )
                if (pw == pwck):
                    break
                else:
                    print u"Given Passphrases do not match!"
        pprint(steem.create_account(
            args.accountname,
            creator=args.account,
            password=pw,
        ))

    elif args.command == u"importaccount":
        from pistonbase.account import PasswordKey
        import getpass
        password = getpass.getpass(u"Account Passphrase: ")
        account = Account(args.account)
        imported = False

        if u"owner" in args.roles:
            owner_key = PasswordKey(args.account, password, role=u"owner")
            owner_pubkey = format(owner_key.get_public_key(), u"STM")
            if owner_pubkey in [x[0] for x in account[u"owner"][u"key_auths"]]:
                print u"Importing owner key!"
                owner_privkey = owner_key.get_private_key()
                steem.wallet.addPrivateKey(owner_privkey)
                imported = True

        if u"active" in args.roles:
            active_key = PasswordKey(args.account, password, role=u"active")
            active_pubkey = format(active_key.get_public_key(), u"STM")
            if active_pubkey in [x[0] for x in account[u"active"][u"key_auths"]]:
                print u"Importing active key!"
                active_privkey = active_key.get_private_key()
                steem.wallet.addPrivateKey(active_privkey)
                imported = True

        if u"posting" in args.roles:
            posting_key = PasswordKey(args.account, password, role=u"posting")
            posting_pubkey = format(posting_key.get_public_key(), u"STM")
            if posting_pubkey in [x[0] for x in account[u"posting"][u"key_auths"]]:
                print u"Importing posting key!"
                posting_privkey = posting_key.get_private_key()
                steem.wallet.addPrivateKey(posting_privkey)
                imported = True

        if u"memo" in args.roles:
            memo_key = PasswordKey(args.account, password, role=u"memo")
            memo_pubkey = format(memo_key.get_public_key(), u"STM")
            if memo_pubkey == account[u"memo_key"]:
                print u"Importing memo key!"
                memo_privkey = memo_key.get_private_key()
                steem.wallet.addPrivateKey(memo_privkey)
                imported = True

        if not imported:
            print u"No matching key(s) found. Password correct?"

    elif args.command == u"sign":
        if args.file and args.file != u"-":
            if not os.path.isfile(args.file):
                raise Exception(u"File %s does not exist!" % args.file)
            with open(args.file) as fp:
                tx = fp.read()
        else:
            tx = sys.stdin.read()
        tx = eval(tx)
        pprint(steem.sign(tx))

    elif args.command == u"broadcast":
        if args.file and args.file != u"-":
            if not os.path.isfile(args.file):
                raise Exception(u"File %s does not exist!" % args.file)
            with open(args.file) as fp:
                tx = fp.read()
        else:
            tx = sys.stdin.read()
        tx = eval(tx)
        steem.broadcast(tx)

    elif args.command == u"orderbook":
        if args.chart:
            try:
                import numpy
                import Gnuplot
                from itertools import accumulate
            except:
                print u"To use --chart, you need gnuplot and gnuplot-py installed"
                sys.exit(1)
        dex = Dex(steem)
        orderbook = dex.returnOrderBook()

        if args.chart:
            g = Gnuplot.Gnuplot()
            g.title(u"Steem internal market - SBD:STEEM")
            g.xlabel(u"price in SBD")
            g.ylabel(u"volume")
            g(u"""
                set style data line
                set term xterm
                set border 15
            """)
            xbids = [x[u"price"] for x in orderbook[u"bids"]]
            ybids = list(accumulate([x[u"sbd"] for x in orderbook[u"bids"]]))
            dbids = Gnuplot.Data(xbids, ybids, with_=u"lines")
            xasks = [x[u"price"] for x in orderbook[u"asks"]]
            yasks = list(accumulate([x[u"sbd"] for x in orderbook[u"asks"]]))
            dasks = Gnuplot.Data(xasks, yasks, with_=u"lines")
            g(u"set terminal dumb")
            g.plot(dbids, dasks)  # write SVG data directly to stdout ...

        t = {}
        # Bid side
        bidssteem = 0
        bidssbd = 0
        t[u"bids"] = PrettyTable([
            u"SBD", u"sum SBD", u"STEEM", u"sum STEEM", u"price"
        ])
        for i, o in enumerate(orderbook[u"asks"]):
            bidssbd += orderbook[u"bids"][i][u"sbd"]
            bidssteem += orderbook[u"bids"][i][u"steem"]
            t[u"bids"].add_row([
                u"%.3f Ṩ" % orderbook[u"bids"][i][u"sbd"],
                u"%.3f ∑" % bidssbd,
                u"%.3f ȿ" % orderbook[u"bids"][i][u"steem"],
                u"%.3f ∑" % bidssteem,
                u"%.3f Ṩ/ȿ" % orderbook[u"bids"][i][u"price"],
            ])

        # Ask side
        askssteem = 0
        askssbd = 0
        t[u"asks"] = PrettyTable([
            u"price", u"STEEM", u"sum STEEM", u"SBD", u"sum SBD"
        ])
        for i, o in enumerate(orderbook[u"asks"]):
            askssbd += orderbook[u"asks"][i][u"sbd"]
            askssteem += orderbook[u"asks"][i][u"steem"]
            t[u"asks"].add_row([
                u"%.3f Ṩ/ȿ" % orderbook[u"asks"][i][u"price"],
                u"%.3f ȿ" % orderbook[u"asks"][i][u"steem"],
                u"%.3f ∑" % askssteem,
                u"%.3f Ṩ" % orderbook[u"asks"][i][u"sbd"],
                u"%.3f ∑" % askssbd
            ])

        book = PrettyTable([u"bids", u"asks"])
        book.add_row([t[u"bids"], t[u"asks"]])
        print book

    elif args.command == u"buy":
        if args.asset == steem.symbol(u"SBD"):
            price = 1.0 / args.price
        else:
            price = args.price
        dex = Dex(steem)
        pprint(dex.buy(
            args.amount,
            args.asset,
            price,
            account=args.account
        ))

    elif args.command == u"sell":
        if args.asset == steem.symbol(u"SBD"):
            price = 1.0 / args.price
        else:
            price = args.price
        dex = Dex(steem)
        pprint(dex.sell(
            args.amount,
            args.asset,
            price,
            account=args.account
        ))

    elif args.command == u"cancel":
        dex = Dex(steem)
        pprint(
            dex.cancel(args.orderid)
        )

    elif args.command == u"approvewitness":
        pprint(steem.approve_witness(
            args.witness,
            account=args.account
        ))

    elif args.command == u"disapprovewitness":
        pprint(steem.disapprove_witness(
            args.witness,
            account=args.account
        ))

    elif args.command == u"resteem":
        pprint(steem.resteem(
            args.identifier,
            account=args.account
        ))

    elif args.command == u"follow":
        pprint(steem.follow(
            args.follow,
            what=args.what,
            account=args.account
        ))

    elif args.command == u"unfollow":
        pprint(steem.unfollow(
            args.unfollow,
            what=args.what,
            account=args.account
        ))

    elif args.command == u"setprofile":
        from piston.profile import Profile
        keys = []
        values = []
        if args.pair:
            for pair in args.pair:
                key, value = pair.split(u"=")
                keys.append(key)
                values.append(value)
        if args.variable and args.value:
            keys.append(args.variable)
            values.append(args.value)

        profile = Profile(keys, values)

        account = Account(args.account)
        account[u"json_metadata"] = Profile(
            account[u"json_metadata"]
            if account[u"json_metadata"]
            else {}
        )
        account[u"json_metadata"].update(profile)

        pprint(steem.update_account_profile(
            account[u"json_metadata"],
            account=args.account
        ))

    elif args.command == u"delprofile":
        from .profile import Profile
        account = Account(args.account)
        account[u"json_metadata"] = Profile(account[u"json_metadata"])

        for var in args.variable:
            account[u"json_metadata"].remove(var)

        pprint(steem.update_account_profile(
            account[u"json_metadata"],
            account=args.account
        ))

    elif args.command == u"witnessupdate":

        witness = Witness(args.witness)
        props = witness[u"props"]
        if args.account_creation_fee:
            props[u"account_creation_fee"] = unicode(Amount(u"%f STEEM" % args.account_creation_fee))
        if args.maximum_block_size:
            props[u"maximum_block_size"] = args.maximum_block_size
        if args.sbd_interest_rate:
            props[u"sbd_interest_rate"] = int(args.sbd_interest_rate * 100)

        pprint(steem.witness_update(
            args.signing_key or witness[u"signing_key"],
            args.url or witness[u"url"],
            props,
            account=args.witness
        ))

    elif args.command == u"witnesscreate":
        props = {
            u"account_creation_fee": unicode(Amount(u"%f STEEM" % args.account_creation_fee)),
            u"maximum_block_size": args.maximum_block_size,
            u"sbd_interest_rate": int(args.sbd_interest_rate * 100)
        }
        pprint(steem.witness_update(
            args.signing_key,
            args.url,
            props,
            account=args.witness
        ))

    else:
        print u"No valid command given"


args = None

if __name__ == u'__main__':
    main()
