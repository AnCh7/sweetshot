from __future__ import with_statement
from __future__ import absolute_import
import os
import re
import sys
import time
from datetime import datetime

import frontmatter
from io import open


def constructIdentifier(author, slug):
    return u"@%s/%s" % (author, slug)


def sanitizePermlink(permlink):
    permlink = permlink.strip()
    permlink = re.sub(u"_|\s|\.", u"-", permlink)
    permlink = re.sub(u"[^\w-]", u"", permlink)
    permlink = re.sub(u"[^a-zA-Z0-9-]", u"", permlink)
    permlink = permlink.lower()
    return permlink


def derivePermlink(title, parent_permlink=None):
    permlink = u""
    if parent_permlink:
        permlink += u"re-"
        permlink += parent_permlink
        permlink += u"-" + formatTime(time.time())
    else:
        permlink += title

    return sanitizePermlink(permlink)


def resolveIdentifier(identifier):
    match = re.match(u"@?([\w\-\.]*)/([\w\-]*)", identifier)
    if not hasattr(match, u"group"):
        raise ValueError(u"Invalid identifier")
    return match.group(1), match.group(2)


def yaml_parse_file(args, initial_content):
    message = None

    if args.file and args.file != u"-":
        if not os.path.isfile(args.file):
            raise Exception(u"File %s does not exist!" % args.file)
        with open(args.file) as fp:
            message = fp.read()
    elif args.file == u"-":
        message = sys.stdin.read()
    else:
        import tempfile
        from subprocess import Popen
        EDITOR = os.environ.get(u'EDITOR', u'vim')
        # prefix = ""
        # if "permlink" in initial_content.metadata:
        #   prefix = initial_content.metadata["permlink"]
        with tempfile.NamedTemporaryFile(
                suffix=".md",
                prefix="steem-",
                delete=False
        ) as fp:
            # Write initial content
            fp.write(str(frontmatter.dumps(initial_content)).encode('utf-8'))
            fp.flush()
            # Define parameters for command
            args = [EDITOR]
            if re.match(u"gvim", EDITOR):
                args.append(u"-f")
            args.append(fp.name)
            # Execute command
            Popen(args).wait()
            # Read content of file
            fp.seek(0)
            message = fp.read().decode(u'utf-8')

    try:
        meta, body = frontmatter.parse(message)
    except:
        meta = initial_content.metadata
        body = message

    # make sure that at least the metadata keys of initial_content are
    # present!
    for key in initial_content.metadata:
        if key not in meta:
            meta[key] = initial_content.metadata[key]

    # Extract anything that is not steem-libs meta and return it separately
    # for json_meta field
    json_meta = dict((key, meta[key]) for key in meta if key not in [
        u"title",
        u"category",
        u"author"
    ])

    return meta, json_meta, body


def formatTime(t):
    u""" Properly Format Time for permlinks
    """
    return datetime.utcfromtimestamp(t).strftime(u"%Y%m%dt%H%M%S%Z")


def formatTimeString(t):
    u""" Properly Format Time for permlinks
    """
    return datetime.strptime(t, u'%Y-%m-%dT%H:%M:%S')


def strfage(time, fmt=None):
    u""" Format time/age
    """
    if not hasattr(time, u"days"):  # dirty hack
        now = datetime.now()
        if isinstance(time, unicode):
            time = datetime.strptime(time, u'%Y-%m-%dT%H:%M:%S')
        time = (now - time)

    d = {u"days": time.days}
    d[u"hours"], rem = divmod(time.seconds, 3600)
    d[u"minutes"], d[u"seconds"] = divmod(rem, 60)

    s = u"{seconds} seconds"
    if d[u"minutes"]:
        s = u"{minutes} minutes " + s
    if d[u"hours"]:
        s = u"{hours} hours " + s
    if d[u"days"]:
        s = u"{days} days " + s
    return s.format(**d)


def strfdelta(tdelta, fmt):
    u""" Format time/age
    """
    if not tdelta or not hasattr(tdelta, u"days"):  # dirty hack
        return None

    d = {u"days": tdelta.days}
    d[u"hours"], rem = divmod(tdelta.seconds, 3600)
    d[u"minutes"], d[u"seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def formatTimeFromNow(secs=0):
    u""" Properly Format Time that is `x` seconds in the future

        :param int secs: Seconds to go in the future (`x>0`) or the
                         past (`x<0`)
        :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
        :rtype: str

    """
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime(u'%Y-%m-%dT%H:%M:%S')


def is_comment(item):
    u"""Quick check whether an item is a comment (reply) to another post.
    The item can be a Post object or just a raw comment object from the blockchain.
    """
    return item[u'permlink'][:3] == u"re-" and item[u'parent_author']


def time_elapsed(posting_time):
    u"""Takes a string time from a post or blockchain event, and returns a time delta from now.
    """
    if type(posting_time) == unicode:
        posting_time = parse_time(posting_time)
    return datetime.utcnow() - posting_time


def parse_time(block_time):
    u"""Take a string representation of time from the blockchain, and parse it into datetime object.
    """
    return datetime.strptime(block_time, u'%Y-%m-%dT%H:%M:%S')


def time_diff(time1, time2):
    return parse_time(time1) - parse_time(time2)


def keep_in_dict(obj, allowed_keys=list()):
    u""" Prune a class or dictionary of all but allowed keys.
    """
    if type(obj) == dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()

    return dict((k, v) for k, v in items if k in allowed_keys)


def remove_from_dict(obj, remove_keys=list()):
    u""" Prune a class or dictionary of specified keys.
    """
    if type(obj) == dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()

    return dict((k, v) for k, v in items if k not in remove_keys)
