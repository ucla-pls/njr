"""
Nix utils consists of basic methods to run nix asts from python.
"""

import subprocess
import tempfile
import re
import json

import mongo.nixast as nixast
from mongo.utils import check_output, process, onall, copy_with, LineWrapper

import logging
logger = logging.getLogger(__name__)

def evaluate(ast):
    """Evaluates a nix ast.
    """
    fname = tofile(ast)
    output = check_output(["nix-instantiate", "--eval", "--json", fname])
    return json.loads(output)


def extract_hash(expr, **kwargs):
    """This method extract the hash from the error message, if the
    build fails. If the build does not fail a error is thrown.

    Returns a sha256 hash.
    """
    log = kwargs.get("logger", logger).getChild("extract_hash")
    kwargs["logger"] = log
    extractor = HashExtractor()
    kwargs.setdefault("stderr", onall(LineWrapper(log.debug), extractor))

    try:
        build(expr, **kwargs)
    except subprocess.CalledProcessError as e:
        if extractor.sha256 is None:
            raise ValueError("Unbuildable expression, could not extract hash")
        return extractor.sha256
    else:
        raise ValueError("Expression builds with current hash")


def verify(method, data, **kwargs):
    """This method verifies that the *data* has a sha256 attribute, which
    if given to *method* will produce correct derivation. If the data does not
    have a sha256, verify then will try to guess the hash from the error message.

    If the build succeed, the path of the result is added to the data.
    """
    log = kwargs.get("logger", logger).getChild("verify")
    kwargs["logger"] = log
    data = dict(data)

    if not "sha256" in data:
        data["sha256"] = "0" * 52
        data["sha256"] = extract_hash(method(data))

    try:
        kwargs.setdefault("stderr", LineWrapper(log.debug))
        paths = build(method(data), **kwargs)
    except subprocess.CalledProcessError as e:
        raise ValueError("Unverifiable build")

    if len(paths) != 1:
        raise ValueError("Malformed expr, too many derivations")

    data["path"] = paths[0]

    return data


def build(ast, **kwargs):
    """Given an ast that evaluates to one or more derivations, this method
    will build the derivation(s) and return a list of the /nix/store names,
    after building them.
    """
    log = kwargs.get("logger", logger).getChild("build")
    kwargs["logger"] = log
    fname = tofile(ast)

    cmd = ["nix-build"]
    # nix-build flags
    cmd += ["--no-out-link", "--show-trace"]
    cmd += [fname]


    log.debug("Building %r", fname)
    kwargs.setdefault("stderr", LineWrapper(log.debug))
    out = check_output(cmd, **kwargs)
    log.debug("Done building")

    return out.splitlines()

# Helper functions from here on
# =============================

def tofile(ast):
    """Creates a new temporary file with the pretty printed ast.
    """
    expr = nixast.dumps(ast)
    (fp, tmpname) = tempfile.mkstemp()
    with open(fp, "w") as fp:
        fp.write(expr)
    return tmpname

class HashExtractor:
    HASH_REGEXS = [
        re.compile(
            r"output path ‘[^’]+’ should have r:sha256 hash ‘[^‘]+’, instead has ‘([^‘]+)’"
        ),
        re.compile(
            r"output path ‘[^’]+’ should have sha256 hash ‘[^‘]+’, instead has ‘([^‘]+)’"
        ),
        re.compile(
            r"output path ‘[^’]+’ has r:sha256 hash ‘([^‘]+)’ when ‘[^‘]+’ was expected"
        ),
        re.compile(
            r"output path ‘[^’]+’ has sha256 hash ‘([^‘]+)’ when ‘[^‘]+’ was expected"
        )
    ]
    def __init__(self):
        self._buffer = []

    def __call__(self, data):
        self._buffer.append(data)

    @property
    def sha256(self):
        try:
            return self._sha256
        except AttributeError:
            buf = "".join(self._buffer)
            for regex in self.HASH_REGEXS:
                match = regex.search(buf);
                if match:
                    self._sha256 = match.group(1);
                    break
            else:
                self._sha256 = None
            return self._sha256
