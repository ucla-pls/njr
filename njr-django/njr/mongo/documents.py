from mongoengine import signals
from mongoengine import *

import mongo.models as models
import mongo.utils as utils
import bson
import json

class StatsDocument():
    buildid = StringField(required=True)
    timing = DecimalField(required=True)

class NJRDocument(Document):
    """An abstract generic NJR document."""

    name = StringField(required=True, unique=True)
    name.__doc__ = """Unique name of the document."""
    visited = DateTimeField()

    stats = DynamicField(required=False)

    meta = {
        "abstract": True
    }

    def dependencies(self):
        return {}

    def children(self):
        return {}

    def to_dict(self, *attr, _dep=True, _chd=True, **recattr):
        """Converts a document to a dictionary, removing database specific keys."""
        attrs = {k: v for k,v in {
            **{k: True for k in attr},
            **recattr
        }.items() if v}

        def plain_fields(doc):
            return [
                n
                for n,f in doc._fields.items()
                if not isinstance(f, ReferenceField) and not isinstance(f, ObjectIdField)
            ]

        def rec_keys(recattrs, key):
            kwargs = recattrs.get(key, {})
            if kwargs and not isinstance(kwargs, dict):
                kwargs = {}
            return kwargs

        dct = self.to_mongo().to_dict()
        dct = utils.omit(dct, "_cls", "_id")
        dct = utils.only(dct, *plain_fields(self))
        dct = utils.only(dct, *[k for k in attrs])

        if _dep:
            for k, v in self.dependencies().items():
                if not attrs or (k in attrs and v):
                    fields = [f for f in plain_fields(v)] + [f for f in v.dependencies()]
                    dct[k] = v.to_dict(_chd=False, **utils.only(rec_keys(attrs, k), *fields))

        if _chd:
            for k, v in self.children().items():
                if not attrs or (k in attrs and v):
                    dct[k] = []
                    for c in v:
                        fields = [f for f in plain_fields(c)] + [f for f in c.children()]
                        dct[k].append(c.to_dict(_dep=False, **utils.only(rec_keys(attrs, k), *fields)))

        return dct

    def to_json(self, *attr, **recattr):
        """Converts a document to a JSON string."""
        return utils.json_dump(self.to_dict(*attr, **recattr), indent=None, default=bson.json_util.default)

    @classmethod
    def get_or_init(cls, model):
        return cls.objects(name=model.name).first() or cls(name=model.name)

    @classmethod
    def upsert(cls, model, deep=False):
        if isinstance(model, Document):
            doc = model
        else:
            doc = cls.get_or_init(model)
        if deep:
            doc.deep_merge(model)
        else:
            doc.merge(model)
        doc.save()
        return doc


class RepoSourceDocument(NJRDocument):
    """An abstract generic repo source."""

    meta = {
        "allow_inheritance" : True
    }

    @staticmethod
    def subclass(model):
        return {
            models.GitSource: GitSourceDocument,
            models.UrlSource: UrlSourceDocument
        }.get(model.__class__, model.__class__)

    def deep_merge(self, model):
        self.merge(model)
        return self

    def children(self):
        return { "repos": RepoDocument.objects(repo_source=self) }


class GitSourceDocument(RepoSourceDocument, models.GitSource):
    """
    Example::

        {
            "name": "git5a26771_integration_test2_git",
            "rev": "9be73f2f064328d2db83166b0bcf8be75439e93b",
            "url": "https://github.com/aas-integration/integration-test2.git"
        }

    """

    url = URLField(required=True)
    url.__doc__ = """Source Git URL."""

    rev = StringField(required=True)
    rev.__doc__ = """Git revision."""


class UrlSourceDocument(RepoSourceDocument, models.UrlSource):
    """
    Example::

        {
            "name": "url5a26771_integration_test2_git",
            "url": "https://github.com/aas-integration/integration-test2.git"
        }

    """

    url = URLField(required=True)
    url.__doc__ = """Source URL"""



''' To be supported...
class MuseSource(RepoSource):
    pass
'''


class RepoDocument(NJRDocument, models.Repo):
    """
    Example::

        {
            "name": "5a26771_integration_test2_git",
            "path": "/nix/store/5dp02b68v5wd3xz136f1n5h56q3036r7-5a26771_integration_test2_git",
            "sha256": "010cnd7z9238v6dr1v81fi68hci7ppvghw2vj296kdzrdh1qyb5c",
            "repo_source": *reference to a RepoSource document*
        }

    """

    path = StringField()
    path.__doc__ = """Unique Nix store path where the repo is installed."""

    buildable = BooleanField(required=True, default=True)
    buildable.__doc__ = """Indication if a repo is downloadable and buildable into projects"""

    sha256 = StringField()
    sha256.__doc__ = """Integrity hash."""

    subfolders = ListField(StringField(), default=[])
    subfolders.__doc__ = """List of subfolders where projects could be build from."""

    repo_source = ReferenceField(RepoSourceDocument)
    repo_source.__doc__ = """Reference to the repo source which the repo is built from."""

    def deep_merge(self, model):
        self.merge(model)
        self.repo_source = RepoSourceDocument.subclass(model.repo_source).upsert(model.repo_source, deep=True)
        return self

    def dependencies(self):
        return { "repo_source": self.repo_source }

    def children(self):
        return { "projects": ProjectDocument.objects(repo=self) }


class ProjectDocument(NJRDocument, models.Project):
    """
    Example::

        {
            "name": "5a26771_integration_test2_git-corpus_Sort10",
            "path": "/nix/store/kribks69g57jnbbp5gc2vrnzx7hbykb5-5a26771_integration_test2_git-corpus_Sort10",
            "subfolder": "corpus/Sort10",
            "sha256": "0ga1hp0w32qkg2h4cmvd8k8396p3ppl11zwsid4g9v2963rlj4vh",
            "buildwith": "ant",
            "classes": [
                "Sort10"
            ],
            "mainclasses": [
                "Sort10"
            ],
            "repo": *reference to a Repo document*
        }

    """

    subfolder = StringField(required=True)
    subfolder.__doc__ = """Subfolder of the referenced repo where the project is built from."""

    path = StringField()
    path.__doc__ = """Unique Nix store path where the project is installed."""

    buildable = BooleanField(required=True, default=True)
    buildable.__doc__ = """Indication if a project is buildable into benchmarks."""

    javaversion = IntField(required=True)
    javaversion.__doc__ = """The java version the project is built with."""

    sha256 = StringField()
    sha256.__doc__ = """Integrity hash."""

    buildwith = StringField()
    buildwith.__doc__ = """Build tool used to build the project."""

    classes = ListField(StringField(), default=[])
    classes.__doc__ = """List of classes generated from building the project"""

    mainclasses = ListField(StringField(), default=[])
    mainclasses.__doc__ = """List of main classes generated from building the project."""

    repo = ReferenceField(RepoDocument)
    repo.__doc__ = """Reference to the repo which the project is built from."""

    def deep_merge(self, model):
        self.merge(model)
        self.repo = RepoDocument.upsert(model.repo, deep=True)
        return self

    def dependencies(self):
        return { "repo": self.repo }

    def children(self):
        return { "benchmarks": BenchmarkDocument.objects(project=self) }


class InputDocument(EmbeddedDocument, models.Input):
    """Represents a set of input to a `Benchmark`."""

    name = StringField(required=True, default="")
    name.__doc__ = """Name of the `Input`."""

    args = ListField(StringField(), default=[])
    args.__doc__ = """List of arguments."""

    stdin = StringField()
    stdin.__doc__ = """Source of standard input."""

    def to_dict(self, *attr, **recattr):
        return utils.only(self.to_mongo().to_dict(), *attr)

    def to_json(self, *attr, **reacttr):
        return NJRDocument.to_json(self, *attr, **reacttr)


class BenchmarkDocument(NJRDocument, models.Benchmark):
    """
    Example::

        {
            name: "5a26771_integration_test2_git-corpus_Sort10-Sort10",
            "mainclass": "Sort10",
            "inputs": [
                {
                    "args": [],
                    "name": "empty",
                    "stdin": ""
                }
            ],
            "project": *reference to a project document*
        }

    """

    mainclass = StringField(required=True, unique=True, unique_with='project')
    mainclass.__doc__ = """Unique (per project) main class of the benchmark."""

    inputs = ListField(EmbeddedDocumentField(InputDocument), default=[])
    inputs.__doc__ = """List of inputs."""

    project = ReferenceField(ProjectDocument)
    project.__doc__ = """Reference to the project where the benchmark is generated."""

    def merge(self, model):
        models.Benchmark.merge(self, model)
        self.inputs = [InputDocument(name=i.name, args=i.args, stdin=i.stdin) for i in model.inputs]
        return self

    def deep_merge(self, model):
        self.merge(model)
        self.project = ProjectDocument.upsert(model.project, deep=True)
        self.inputs = [InputDocument(name=i.name, args=i.args, stdin=i.stdin) for i in model.inputs]
        return self

    def dependencies(self):
        return { "project": self.project }

    def children(self):
        return { "analysis_results": AnalysisResultDocument.objects(benchmark=self) }


class AnalysisResultDocument(NJRDocument, models.AnalysisResult):
    analysis = StringField(required=True, unique=True, unique_with="benchmark")
    analysis.__doc__ = """Name of the analysis."""

    path = StringField()
    path.__doc__ = """Unique path to the analysis result in the nix store."""

    buildable = BooleanField(required=True, default=True)
    buildable.__doc__ = """Indication if an analysis result is buildable."""

    benchmark = ReferenceField(BenchmarkDocument)
    benchmark.__doc__ = """Reference to the benchmark from which this analysis result was created."""

    lower = IntField()
    lower.__doc__ = """Lower count."""

    upper = IntField()
    upper.__doc__ = """Upper count."""

    difference = IntField()
    difference.__doc__ = """Difference count."""

    world = IntField()
    world.__doc__ = """World count."""

    def deep_merge(self, model):
        self.merge(model)
        self.benchmark = BenchmarkDocument.upsert(model.benchmark, deep=True)
        return self

    def dependencies(self):
        return { "benchmark": self.benchmark }
