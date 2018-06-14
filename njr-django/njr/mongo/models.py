"""
Models contains the models of the projects.
"""

from functools import partial
from mongo.utils import name_from_url, sha256, append, only, get_lines, sanitize
from abc import abstractmethod, ABCMeta
from mongo.exceptions import *

import mongo.jbxutils as jbx
import mongo.nixutils as nixutils
import mongo.nixast as nixast
import mongo

import os

class Model:
    def to_dict(self, *attr, **recattr):
        import inspect

        if not attr:
            attributes = inspect.getmembers(
                self,
                lambda a:not(inspect.isroutine(a))
            )
            return {k: v for k,v in attributes if not "__" in k}

        return {name: getattr(self, name) for name in attr}

    def normalform(self):
        dct = self.to_dict()
        return tuple(sorted(dct.items()))

    def __hash__(self):
        return hash(self.normalform())

    def __eq__(self, other):
        return (
            hasattr(other,"normalform")
            and self.normalform() == other.normalform()
        )

    def __repr__(self):
        return "{}(**{})".format(self.__class__.__name__,self.to_dict())


class NixBuildable:
    def __init__(self, path=None, buildable=True):
        super(NixBuildable, self).__init__()
        self.path = path
        self.buildable = buildable

    def to_nix():
        pass

    def populate(self, proc, env=jbx.STDENV):
        """ Populate the model with data from building the expression """
        try:
            self.path = self.build(proc, env)
            self.buildable = True
        except:
            self.path = None
            self.buildable = False
            raise

        return self

    def depopulate(self):
        """ Create a new version of yourself without nix derivable information."""
        pass

    def build(self, proc, env=jbx.STDENV):
        return nixutils.build(self.to_nix().bind(env), **proc)[0]

    def verify(self, force_verify=False, **proc):
        """ A NixBuildable structure is verifiable if after depopulating it we
        can retrive the same information again.

        Depending on whether the integrity of the nix store is trusted there is
        two modes. If the nix store is still trusted, verify will just check if
        building the object still results in the same path. Force verify will
        try to repopulate the model, and then checks if the model is the same.
        """
        if force_verify:
            return self == self.repopulate(**proc)
        else:
            return self.path == self.build(**proc)

    def repopulate(self, proc, env=jbx.STDENV):
        """ Depopulates the model and then repopulates it again. """
        copy = self.depopulate()
        copy.populate(proc, env)
        return copy

    def merge(self, other):
        self.path = other.path
        self.buildable = other.buildable
        return self

class UnpureNixBuildable(NixBuildable):
    """Like the NixBuildable, but is not pure. This means that the execution
    is not defined alone from its dependencies, but from some external source.

    An UnpureNixBuildable will besided having a path also have a `sha256` hash.
    """

    def __init__(self, path=None, buildable=True, sha256=None):
        super(UnpureNixBuildable, self).__init__(path, buildable)
        self.sha256 = sha256

    def populate(self, proc, env=jbx.STDENV):
        if self.sha256 is None:
            self.sha256 = "0" * 52
            try:
                self.sha256 = self.extract_hash(proc, env)
            except:
                self.sha256 = None
                self.buildable = False
                raise
        super(UnpureNixBuildable, self).populate(proc, env)
        return self

    def extract_hash(self, proc, env=jbx.STDENV):
        return nixutils.extract_hash(self.to_nix().bind(env), **proc)

    def merge(self, other):
        super(UnpureNixBuildable, self).merge(other)
        self.sha256 = other.sha256
        return self

class RepoSource(Model):
    def generate_repos(self):
        return [Repo(self)]


class GitSource(RepoSource):
    def __init__(self, url, rev, name=None):
        self.url = url
        self.rev = rev
        self.name = name or self.build_name()

    def fetchrepo(self, sha256):
        dct = self.to_dict("url", "rev", "name")
        dct['sha256'] = sha256
        return jbx.fetchrepo_git(dct)

    def build_name(self):
        return "git{}_{}".format(sha256(self.url + self.rev)[0:10], name_from_url(self.url))

    def merge(self, model):
        self.name = model.name
        self.url = model.url
        self.rev = model.rev
        return self


class UrlSource(RepoSource):
    def __init__(self, url, name=None):
        self.url = url
        self.name = name or self.build_name()

    def fetchrepo(self, sha256):
        dct = self.to_dict("url", "name")
        dct['sha256'] = sha256
        dct['name'] += self.file_ext()
        return jbx.fetchrepo_url(dct)

    def file_ext(self):
        return os.path.splitext(self.url)[1]

    def build_name(self):
        return "url{}_{}".format(sha256(self.url)[0:10], name_from_url(self.url))

    def merge(self, model):
        self.name = model.name
        self.url = model.url
        return self


class Repo(Model, UnpureNixBuildable):
    def __init__(
            self,
            repo_source,
            sha256=None,
            path=None,
            subfolders=None,
            name=None,
            buildable=True
    ):
        super(Repo, self).__init__(path, buildable, sha256)
        self.repo_source = repo_source
        self.name = name or self.build_name()
        self.subfolders = subfolders

    def to_nix(self, sha256=None):
        return self.repo_source.fetchrepo(sha256 or self.sha256)

    def depopulate(self):
        return Repo(repo_source = self.repo_source)

    def populate(self, proc, env=jbx.STDENV):
        if self.name != self.repo_source.name:
            raise InconsistentModelException(
                "Name should be the same as repo source"
            )
        super(Repo, self).populate(proc, env)
        self.subfolders = [""]
        return self

    def merge(self, model):
        super(Repo, self).merge(model)
        self.name = model.name
        self.subfolders = model.subfolders
        self.repo_source = model.repo_source
        return self

    def generate_projects(self, javaversion):
        return [
            Project(self, subfolder, javaversion)
            for subfolder in self.subfolders
        ]

    def build_name(self):
        return self.repo_source.name

class Project(Model, UnpureNixBuildable):
    def __init__(self,
                 repo,  # repo is required
                 subfolder, # subfolder is required
                 javaversion,
                 sha256=None,
                 path=None,
                 buildwith=None,
                 classes=None,
                 mainclasses=None,
                 name=None,
                 buildable=True
    ):
        super(Project, self).__init__(path, buildable, sha256)
        self.repo = repo
        self.subfolder = subfolder
        self.javaversion = javaversion
        self.name = name or self.build_name()

        self.buildwith = buildwith
        self.classes = classes
        self.mainclasses = mainclasses

    def to_nix(self, sha256=None):
        return jbx.nflatten.injectify(
            name=self.name,
            subfolder=self.subfolder,
            sha256=sha256 or self.sha256,
            src=self.repo.to_nix(),
            javaversion=jbx.getjava(self.javaversion)
        )

    def depopulate(self):
        return Project(
            repo=self.repo,
            subfolder=self.subfolder,
            javaversion=self.javaversion
        )

    def populate(self, proc, env=jbx.STDENV):
        super(Project, self).populate(proc, env)

        self.buildwith = self.buildwith or self._info("buildwith")[0]
        self.classes = self.classes or sorted(set(self._info("classes")))
        self.mainclasses = self.mainclasses or sorted(set(self._info("mainclasses")))

        return self

    def _info(self, filename):
        return get_lines(os.path.join(self.path, "info", filename))

    def build_name(self):
        return append(
            self.repo.name,
            sanitize("p{}J{}".format(self.subfolder, self.javaversion))
        )

    def merge(self, model):
        super(Project, self).merge(model)
        self.name = model.name
        self.subfolder = model.subfolder
        self.javaversion = model.javaversion
        self.buildwith = model.buildwith
        self.classes = model.classes
        self.mainclasses = model.mainclasses
        self.repo = model.repo
        return self

    def generate_benchmarks(self):
        return [
            Benchmark(self, mcl, [Input("empty")])
            for mcl in self.mainclasses
        ]

class Benchmark(Model):
    def __init__(self, project, mainclass, inputs, name=None):
        self.project = project
        self.mainclass = mainclass
        self.inputs = inputs
        self.name = name or self.build_name()

    def to_nix(self):
        return jbx.nbenchmark.injectify(
            benchmarktemplate=jbx.nbenchmarktemplate.injectify(
                project=self.project.to_nix(),
                name=self.name,
                mainclass=self.mainclass,
                inputs=[
                    Input(
                        name=inp.name, args=inp.args, stdin=inp.stdin
                    ).to_dict() for inp in self.inputs
                ]
            ),
            javaversion=jbx.getjava(self.project.javaversion)
        )

    def merge(self, model):
        self.name = model.name
        self.mainclass = model.mainclass
        self.inputs = [Input(i.name, args=i.args, stdin=i.stdin) for i in model.inputs]
        self.project = model.project
        return self

    def generate_analysis_results(self, analysis):
        return [AnalysisResult(self, analysis)]

    def build_name(self):
        return append(self.project.name, sanitize(self.mainclass))


class Input(Model):
    def __init__(self, name, args=[], stdin=""):
        self.name = name
        self.args = args
        self.stdin = stdin


class AnalysisResult(Model, NixBuildable):
    def __init__(self,
                 benchmark,
                 analysis,
                 path=None,
                 buildable=True,
                 name=None,
                 lower=None,
                 upper=None,
                 difference=None,
                 world=None):
        super(AnalysisResult, self).__init__(path, buildable)
        self.analysis = analysis
        self.benchmark = benchmark
        self.name = name or self.build_name()

        self.lower = lower
        self.upper = upper
        self.difference = difference
        self.world = world

    def to_nix(self):
        return jbx.nanalyze.injectify(
            benchmark=self.benchmark.to_nix(),
            analysis=jbx.analysis(self.analysis)
        )

    def depopulate(self):
        return AnalysisResult(benchmark=self.benchmark, analysis=self.analysis)

    def populate(self, proc, env=jbx.STDENV):
        super(AnalysisResult, self).populate(proc, env)

        self.lower = self._count("lower")
        self.upper = self._count("upper")
        self.difference = self._count("difference")
        self.world = self._count("world")
        return self

    def _count(self, filename):
        return len(get_lines(os.path.join(self.path, filename)))

    def build_name(self):
        return append(self.benchmark.name, sanitize(self.analysis))

    def merge(self, model):
        super(AnalysisResult, self).merge(model)
        self.name = model.name
        self.analysis = model.analysis
        self.benchmark = model.benchmark
        self.lower = model.lower
        self.upper = model.upper
        self.difference = model.difference
        self.world = model.world
        return self


class InconsistentModelException(NJRError):
    pass
