from __future__ import absolute_import
import sys
import json
from prettytable import PrettyTable, ALL as allBorders
from textwrap import fill, TextWrapper
import frontmatter
import re
from piston.storage import configStorage as config
from piston.utils import constructIdentifier
from piston import steem as stm

# For recursive display of a discussion thread (--comments + --parents)
currentThreadDepth = 0


class UIError(Exception):
    pass


def markdownify(t):
    width = 120

    def mdCodeBlock(t):
        return (u"    " +
                Back.WHITE +
                Fore.BLUE +
                u"   " +
                t.group(1) +
                u"   " +
                Fore.RESET +
                Back.RESET)

    def mdCodeInline(t):
        return (Back.WHITE +
                Fore.BLUE +
                u" " +
                t.group(1) +
                u" " +
                Fore.RESET +
                Back.RESET)

    def mdList(t):
        return (Fore.GREEN +
                u" " +
                t.group(1) +
                u" " +
                Fore.RESET +
                t.group(2))

    def mdLink(t):
        return (Fore.RED +
                u"[%s]" % t.group(1) +
                Fore.GREEN +
                u"(%s)" % t.group(2) +
                Fore.RESET)

    def mdHeadline(t):
        colors = [
            Back.RED,
            Back.GREEN,
            Back.YELLOW,
            Back.BLUE,
            Back.MAGENTA,
            Back.CYAN,
        ]
        color = colors[len(t.group(1)) % len(colors)]
        # width = 80 - 15 * len(t.group(1))
        headline = (color +
                    u'{:^{len}}'.format(t.group(2), len=width) +
                    Back.RESET)
        return (Style.BRIGHT +
                headline +
                Style.NORMAL)

    def mdBold(t):
        return (Style.BRIGHT +
                t.group(1) +
                Style.NORMAL)

    def mdLight(t):
        return (Style.DIM +
                t.group(1) +
                Style.NORMAL)

    def wrapText(t):
        postWrapper = TextWrapper()
        postWrapper.width = width
        return (u"\n".join(postWrapper.fill(l) for l in t.splitlines()))

    import colorama
    from colorama import Fore, Back, Style
    colorama.init()

    t = re.sub(ur"\n\n", u"{NEWLINE}", t, flags=re.M)
    t = re.sub(ur"\n(^[^#\-\*].*)", ur"\1", t, flags=re.M)
    t = re.sub(ur"{NEWLINE}", u"\n\n", t, flags=re.M)

    t = re.sub(ur"\*\*(.*)\*\*", mdBold, t, flags=re.M)
    t = re.sub(ur"\*(.*)\*", mdLight, t, flags=re.M)

    t = re.sub(ur"`(.*)`", mdCodeInline, t, flags=re.M)
    t = re.sub(ur"^ {4,}(.*)", mdCodeBlock, t, flags=re.M)
    t = re.sub(ur"^([\*\-])\s*(.*)", mdList, t, flags=re.M)
    t = re.sub(ur"\[(.*)\]\((.*)\)", mdLink, t, flags=re.M)

    t = wrapText(t)

    t = re.sub(ur"^(#+)\s*(.*)$", mdHeadline, t, flags=re.M)
    t = re.sub(ur"```(.*)```", mdCodeBlock, t, flags=re.M)

    return t


def __get_text_wrapper(width=60):
    u"""
    Get text wrapper with a fixed with.

    :param width: width of the wrapper. Default 60.
    :return: text wrapper
    :rtype: :py:class:`TextWrapper`
    """
    wrapper = TextWrapper()
    wrapper.width = width
    wrapper.subsequent_indent = u" "

    return wrapper


def list_posts(discussions, custom_columns=None):
    u"""
    List posts using PrettyTable. Use default layout if custom column list
    is not specified. Default layout is [ "identifier", "title", "category",
    "replies", "votes", "payouts"]. Custom layout can contain one or more
    allowed columns and rows always start with [ "identifier", "title" ].

    :param discussions: discussions (posts) list
    :type discussions: list
    :param custom_columns: custom columns to display
    :type custom_columns: list

    :raises: :py:class:`UIError`: If tried to use wrong column(s).
    """
    if not discussions:
        return
    if not custom_columns:
        t = PrettyTable([
            u"identifier",
            u"title",
            u"category",
            u"replies",
            # "votes",
            u"payouts",
        ])
        t.align = u"l"
        t.align[u"payouts"] = u"r"
        # t.align["votes"] = "r"
        t.align[u"replies"] = u"c"
        for d in discussions:
            # Some discussions are dicts or identifiers
            if isinstance(d, unicode):
                d = discussions[d]
            identifier = constructIdentifier(d[u"author"], d[u"permlink"])
            identifier_wrapper = __get_text_wrapper()
            row = [
                identifier_wrapper.fill(identifier),
                identifier_wrapper.fill(d[u"title"]),
                d[u"category"],
                d[u"children"],
                # d["net_rshares"],
                d[u"pending_payout_value"],
            ]
            t.add_row(row)
    else:
        available_attrs = set(vars(discussions[0]))
        if not set(custom_columns).issubset(available_attrs):
            wrong_columns = set(custom_columns).difference(available_attrs)
            raise UIError(u"Please use allowed column names only: %s. "
                          u"Error caused by %s." %
                          (sorted(available_attrs), wrong_columns))
        # move identifier and title to front if available
        for c in [u"title", u"identifier"]:
            if c in custom_columns:
                custom_columns.insert(0, custom_columns.pop(
                    custom_columns.index(c)))
        t = PrettyTable(custom_columns)
        t.align = u"l"
        for d in discussions:
            display_columns = custom_columns.copy()
            if isinstance(d, unicode):
                d = discussions[d]
            identifier = constructIdentifier(d[u"author"], d[u"permlink"])
            identifier_wrapper = __get_text_wrapper()
            row = []
            # identifier and title always go first if available
            if u"identifier" in display_columns:
                row.append(identifier_wrapper.fill(identifier))
                display_columns.remove(u"identifier")
            if u"title" in display_columns:
                row.append(identifier_wrapper.fill(d[u"title"]))
                display_columns.remove(u"title")
            for column in display_columns:
                row.append(d[column])
            if row:
                t.add_row(row)
    print t


def dump_recursive_parents(rpc,
                           post_author,
                           post_permlink,
                           limit=1,
                           format=u"markdown"):
    global currentThreadDepth

    limit = int(limit)

    postWrapper = TextWrapper()
    postWrapper.width = 120
    postWrapper.initial_indent = u"  " * (limit)
    postWrapper.subsequent_indent = u"  " * (limit)

    if limit > currentThreadDepth:
        currentThreadDepth = limit + 1

    post = rpc.get_content(post_author, post_permlink)

    if limit and post[u"parent_author"]:
        parent = rpc.get_content_replies(post[u"parent_author"], post[u"parent_permlink"])
        if len(parent):
            dump_recursive_parents(rpc, post[u"parent_author"], post[u"parent_permlink"], limit - 1)

    meta = {}
    for key in [u"author", u"permlink"]:
        meta[key] = post[key]
    meta[u"reply"] = u"@{author}/{permlink}".format(**post)
    if format == u"markdown":
        body = markdownify(post[u"body"])
    else:
        body = post[u"body"]
    yaml = frontmatter.Post(body, **meta)
    print frontmatter.dumps(yaml)


def dump_recursive_comments(rpc,
                            post_author,
                            post_permlink,
                            depth=0,
                            format=u"markdown"):
    global currentThreadDepth
    postWrapper = TextWrapper()
    postWrapper.width = 120
    postWrapper.initial_indent = u"  " * (depth + currentThreadDepth)
    postWrapper.subsequent_indent = u"  " * (depth + currentThreadDepth)

    depth = int(depth)

    posts = rpc.get_content_replies(post_author, post_permlink)
    for post in posts:
        meta = {}
        for key in [u"author", u"permlink"]:
            meta[key] = post[key]
        meta[u"reply"] = u"@{author}/{permlink}".format(**post)
        if format == u"markdown":
            body = markdownify(post[u"body"])
        else:
            body = post[u"body"]
        yaml = frontmatter.Post(body, **meta)
        print frontmatter.dumps(yaml)
        reply = rpc.get_content_replies(post[u"author"], post[u"permlink"])
        if len(reply):
            dump_recursive_comments(rpc, post[u"author"], post[u"permlink"], depth + 1)


def format_operation_details(op, memos=False):
    if op[0] == u"vote":
        return u"%s: %s" % (
            op[1][u"voter"],
            constructIdentifier(op[1][u"author"], op[1][u"permlink"])
        )
    elif op[0] == u"comment":
        return u"%s: %s" % (
            op[1][u"author"],
            constructIdentifier(op[1][u"author"], op[1][u"permlink"])
        )
    elif op[0] == u"transfer":
        str_ = u"%s -> %s %s" % (
            op[1][u"from"],
            op[1][u"to"],
            op[1][u"amount"],
        )

        if memos:
            memo = op[1][u"memo"]
            if len(memo) > 0 and memo[0] == u"#":
                steem = stm.Steem()
                # memo = steem.decode_memo(memo, op[1]["from"])
                memo = steem.decode_memo(memo, op)
            str_ += u" (%s)" % memo
        return str_
    elif op[0] == u"interest":
        return u"%s" % (
            op[1][u"interest"]
        )
    else:
        return json.dumps(op[1], indent=4)


def confirm(question, default=u"yes"):
    u""" Confirmation dialog that requires *manual* input.

        :param str question: Question to ask the user
        :param str default: default answer
        :return: Choice of the user
        :rtype: bool

    """
    valid = {u"yes": True, u"y": True, u"ye": True,
             u"no": False, u"n": False}
    if default is None:
        prompt = u" [y/n] "
    elif default == u"yes":
        prompt = u" [Y/n] "
    elif default == u"no":
        prompt = u" [y/N] "
    else:
        raise ValueError(u"invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == u'':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(u"Please respond with 'yes' or 'no' "
                             u"(or 'y' or 'n').\n")


def print_permissions(account):
    t = PrettyTable([u"Permission", u"Threshold", u"Key/Account"], hrules=allBorders)
    t.align = u"r"
    for permission in [u"owner", u"active", u"posting"]:
        auths = []
        for type_ in [u"account_auths", u"key_auths"]:
            for authority in account[permission][type_]:
                auths.append(u"%s (%d)" % (authority[0], authority[1]))
        t.add_row([
            permission,
            account[permission][u"weight_threshold"],
            u"\n".join(auths),
        ])
    print t


def get_terminal(text=u"Password", confirm=False, allowedempty=False):
    import getpass
    while True:
        pw = getpass.getpass(text)
        if not pw and not allowedempty:
            print u"Cannot be empty!"
            continue
        else:
            if not confirm:
                break
            pwck = getpass.getpass(
                u"Confirm " + text
            )
            if (pw == pwck):
                break
            else:
                print u"Not matching!"
    return pw
