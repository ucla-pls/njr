""" The goal of this module is to interface with jbx.

"""
from mongo.nixast import *
from mongo.utils import only, get_lines
from mongo.nixutils import build

import mongo

def nimport(path, env={}):
    """Nix expression to load jbx"""
    return nixexpr(App(Import(path), nixify(env)))

@nixexpr
def nfetchgit(nixpkgs):
    """Nix expression to get fetchgit"""
    return Lookup(nixpkgs, "fetchgit")

@nixexpr
def nfetchurl(nixpkgs):
    """Nix expression to get fetchurl"""
    return Lookup(nixpkgs, "fetchurl")

@nixexpr
def nfetchmuse(jbx):
    """Nix expression to get fetchmuse"""
    return lookup(jbx, "utils.fetchmuse")

def fetchrepo_git(data):
    """Nix expression to fetch git repository"""
    nixdata = nixify(data)
    def inner(fetchgit):
        return App(fetchgit, nixdata)
    return nixexpr(inner)

def fetchrepo_url(data):
    """Nix expression to fetch repo by url"""
    nixdata = nixify(data)
    def inner(fetchurl):
        return App(fetchurl, nixdata)
    return nixexpr(inner)

def fetchrepo_muse(data, fetchmuse):
    """Nix expression to fetch muse repository"""
    nixdata = nixify(data)
    def inner(fetchmuse):
        return app(fetchmuse, nixdata)
    return nixexpr(inner)

def getjava(javaversion):
    def inner(java):
        return lookup(java,"java{}".format(javaversion))
    return nixexpr(inner)

@nixexpr
def nflatten(name, subfolder, sha256, src, flattenRepository, buildJar, javaversion):
    """Nix expression to flatten a repository"""
    return app(
        buildJar,
        app(
            flattenRepository,
            Attrset({
                "subfolder": subfolder,
                "sha256": sha256,
                "src": src,
                "name": name
            })
        ),
        javaversion
    )

nfoldl_ = Lookup(BUILTINS, "foldl'")
nmap = Lookup(BUILTINS, "map")
nid = fun(lambda a: a)

def analysis(analysis):
    """Retrieves an analysis from the jbx collection of analyses"""
    def inner(jbx):
        return lookup(lookup(jbx, "analyses"), analysis)
    return nixexpr(inner)

@nixexpr
def nbenchmarktemplate(utils, project, name, mainclass, inputs):
    """Nix expression to create a benchmark template"""
    return app(
        lookup(utils, "mkBenchmarkTemplate"),
        Attrset({
            "build": Fun(lambda javaversion: project),
            "name": name,
            "mainclass": mainclass,
            "inputs": inputs
        })
    )

@nixexpr
def nbenchmark(benchmarktemplate, javaversion):
    """Nix expression to create a benchmark"""
    return app(lookup(benchmarktemplate, "withJava"), javaversion)

@nixexpr
def ntransform(benchmark, transformers):
    """Nix expression to apply transformers to a benchmark"""
    return app(nfoldl_, fun(lambda bp, t: app(t,bp)), benchmark, transformers)

@nixexpr
def nanalyze(benchmark, environment, analysis=nid):
    """Nix expression to apply analysis to a benchmark"""
    return app(analysis, benchmark, environment)

STDENV = {
    "jbx" : nimport("<jbx>"),
    "nixpkgs": nixexpr(lambda jbx: lookup(jbx, "pkgs")),
    "utils": nixexpr(lambda jbx: lookup(jbx, "utils")),
    "java": nixexpr(lambda jbx: lookup(jbx, "java")),
    "environment": nixexpr(lambda jbx: lookup(jbx, "env")),
    "lib": nixexpr(lambda nixpkgs: lookup(nixpkgs, "lib")),
    "buildJar": nixexpr(lambda utils: lookup(utils, "buildJar")),
    "flattenRepository": nixexpr(lambda utils: lookup(utils, "flattenRepository")),
    "fetchgit" : nfetchgit,
    "fetchmuse" : nfetchmuse,
    "fetchurl" : nfetchurl
}
