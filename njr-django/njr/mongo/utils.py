import os
import re
import json
import hashlib
import logging
import subprocess

from subprocess import CalledProcessError

from mongo.exceptions import NJRError

import logging
logger = logging.getLogger(__name__)

def is_githash(rev):
    """Returns True if `rev` is a valid git hash and False otherwise."""
    return re.match("[0-9a-f]{40}", rev) is not None

def complement(dct1, dct2):
    """Complements dct1 with k,v pairs from dct2 not present in dct1."""
    return merge(dct1, {k:dct2[k] for k in set(dct2) - set(dct1)})

def merge(dct1, dct2, resolve=None):
    """Merge dct2 into dct1, overriding common keys in dct1."""
    def _fun(d1, d2, k):
        return d2[k]
    if not resolve:
        resolve = _fun
    keys1 = set(dct1)
    keys2 = set(dct2)
    common = keys1.intersection(keys2)

    result = {**{k:dct1[k] for k in (keys1 - keys2)}, **{k:dct2[k] for k in (keys2 - keys1)}}
    for k in common:
        result[k] = resolve(dct1, dct2, k)
    return result

def only(attr, *keys):
    """Returns a shallow copy of a dictionary with only the keys provided."""
    return {
        key: value
        for key, value in attr.items()
        if key in keys
    } if keys else attr

def omit(attr, *keys):
    """Returns a shallow copy of a dictionary excluding the keys provided."""
    return {
        key: value
        for key, value in attr.items()
        if key not in keys
    } if keys else attr

def sanitize(name):
    """Sanitizes strings removing anything non-alphanumeric."""
    san_regex = r"[^a-zA-Z0-9]"
    san_subst = "_"
    return re.sub(san_regex, san_subst, name)

def append(first, second):
    """Append two strings using a "-"."""
    separator = "-"
    return first + separator + second

def sha256(string):
  """Compute the SHA256 hash of a string."""
  return hashlib.sha256(string.encode('utf-8')).hexdigest()

def get_lines(filepath):
  """Return the contents of a file as a list of the file's lines"""
  try:
    with open(filepath) as f:
        return [ v for v in map(str.strip,f.read().splitlines()) if v];
  except:
    return []

def name_from_url(url):
    return sanitize(url.strip("/").rsplit("/",1)[1])

def json_dump(obj, **kwargs):
    return json.dumps(obj, **merge({"indent": 2, "sort_keys": True}, kwargs))

def toset(options, names):
    return { name for name in names if options[name]}

def read_json_file(fpath):
    with open(fpath) as f:
        return json.load(f)

def read_env(var):
    return os.environ[var]

def git_remote_revision(url, branch, logger=logger):
    """Gets the remote revision of a git repository at a branch.
    Throws a NJRError if the branch is not at the url, or if the url is
    not a git repository.
    """
    try:
        return check_output(
            ["git", "ls-remote", url, branch],
            logger=logger
        ).split()[0]
        logger.debug("Found %r as current rev.", rev)
    except IndexError:
        raise NJRError("No branch matching {!r} at {!r}".format(branch, url))
    except CalledProcessError:
        raise NJRError("No branch matching {!r} at {!r}".format(branch, url))

def git_verify_version(path, rev):
    try:
        realrev = check_output([
            "git",
            "--git-dir={}/.git".format(path),
            "--work-tree={}".format(path),
            "rev-parse",
            "HEAD"
        ])
        if realrev == rev:
            raise NJRError(("Git repository has the wrong version {!r}, but should"
            " have been {!r}").format(realrev, rev))
    except CalledProcessError as e:
        raise NJRError("The path {} is not a git repository:\n{}".format(path, e))


def git_verify_content(path):
    try:
        ext = check_output([
            "git",
            "--git-dir={}/.git".format(path),
            "--work-tree={}".format(path),
            "status",
            "--porcelain"
        ]).split("\n")[:-1]
        if ext:
            raise NJRError("Git repository is not clean: {} uncommitted files".format(len(ext)))
    except CalledProcessError as e:
        raise NJRError("Could not query the git repository")

def git_clone(url, rev, directory, logger=logger):
    """Fetches jbx repository corresponding to url and rev"""

    if not is_githash(rev):
        raise NJRError("jbx rev must be a SHA-1")

    try:
        logger.info("Cloning repository..")
        process(["git", "clone", "--recursive", url, directory],
                stdout=LineWrapper(logger.debug),
                timeout=300)
        logger.info("Resetting to revision %r", rev)
        process(["git", "--work-tree={}".format(directory), "reset", "--hard", rev],
                stdout=LineWrapper(logger.debug),
                timeout=300)
    except Exception as e:
        log.debug("Failed while running %s" % subprocess.list2cmdline(cmd))
        raise NJRError(
            "Failed to clone %r into %r: %s" % (url, directory, e)
        )


def check_output(cmd, **kwargs):
    """This function runs a command and returns it's output. It also
    logs the stderr to `logger.debug`` in real time."""
    log = kwargs.get("logger", logger).getChild("check_output")
    kwargs["logger"] = log

    if "stdout" in kwargs:
        raise ValueError("Can't set stdout in check_output")

    kwargs.setdefault("stderr", LineWrapper(log.debug))

    buf = []
    proc = process(cmd, stdout=buf.append, **kwargs)

    if proc == 0:
        return "".join(buf)
    else:
        log.debug("Failed while running %s" % subprocess.list2cmdline(cmd))
        raise subprocess.CalledProcessError(proc, subprocess.list2cmdline(cmd))


def process(cmd, stdout=None, stderr=None, env=None, timeout=None, block_size=1024, **kwargs):
    """Starts a new process using sane defaults. Use *env* to set the
    environment of the proccess and *timeout* to set a maximum amount of
    time allowed for the process.

    *stdenv* and *stderr* can be set with call back functions

    See :class:`subprocess.Popen` for more information.
    """
    import selectors
    import time

    block_size=1

    if timeout is not None:
        timeend = time.time() + timeout
        timeleft = timeend - time.time()
    else:
        timeleft = None

    with subprocess.Popen(
        cmd,
        stdout=stdout and subprocess.PIPE,
        stderr=stderr and subprocess.PIPE,
        universal_newlines=True,
        env=env
    ) as proc, selectors.DefaultSelector() as selector:
        if stdout: selector.register(proc.stdout, selectors.EVENT_READ, stdout)
        if stderr: selector.register(proc.stderr, selectors.EVENT_READ, stderr)
        while timeout is None or timeleft > 0:
            isdone = proc.poll() != None
            for key, event in selector.select(timeleft):
                # This repeat itself an unreasonable number of times
                data = key.fileobj.read(block_size)
                while isdone and block_size == len(data):
                    key.data(data)
                    data = key.fileobj.read(block_size)
                if len(data) > 0:
                    key.data(data)
            if timeout is not None:
                timeleft = timeend - time.time()
            if isdone:
                return proc.poll()
        proc.kill()
        raise TimeoutError("Process timed out")


def onall(*args):
    def inner (data):
        for fn in args:
            fn(data)
    return inner

def copy_with(d, **kwargs):
    return dict(d.items() + kwargs.items())

class LineWrapper:
    """ Wraps a callback function that expects lines, to make it expects blocks
    instead.
    """

    def __init__(self, callback):
        self._buffer = ''
        self.callback = callback

    def __call__(self, data):
        head, *lines = data.split("\n")
        line = self._buffer + head
        while lines:
            self.callback(line)
            line, *lines = lines
        self._buffer = line

    def close():
        if self._buffer:
            self.callback(self._buffer)
