from njr.documents import *
from njr.models import *
import mongoengine

import logging
logger = logging.getLogger(__name__)

class Database:
    instance = None

    def __init__(self, config):
        self.config = config

    def _connect(self):
        self._engine = mongoengine.connect(**self.config)
        return self

    @classmethod
    def connect(cls, config):
        if not cls.instance:
            return cls(config)._connect()
        else:
            raise NJRDatabaseError("Can't connect to database twice")

    @staticmethod
    def saved_models(models):
        for model in models:
            doc = Database.get_or_init(model)
            if doc.id:
                yield doc

    @staticmethod
    def new_models(models):
        for model in models:
            doc = Database.get_or_init(model)
            if not doc.id:
                yield doc

    @staticmethod
    def modify(doc, **kwargs):
        return doc.modify(**kwargs)

    @staticmethod
    def repo_sources(**kwargs):
        return RepoSourceDocument.objects(**kwargs)

    @staticmethod
    def upsert_model(model):
        logger.info("Upserting %r in the db", model.name)
        return class_lookup(model).upsert(model)

    @staticmethod
    def import_models(models, upsert=True):
        filter = {}
        for model in models:
            filter.setdefault(model.__class__, []).append(model)

        result = []
        for c, l in filter.items():
            result += getattr(Database, METHOD_LOOKUP[c][2])(l, upsert=upsert)
        return result

    @staticmethod
    def get_or_init(model):
        return class_lookup(model).get_or_init(model)

CLASS_LOOKUP = {
    GitSource: GitSourceDocument,
    UrlSource: UrlSourceDocument,
    Repo: RepoDocument,
    Project: ProjectDocument,
    Benchmark: BenchmarkDocument,
    AnalysisResult: AnalysisResultDocument
}

METHOD_LOOKUP = {
    GitSource: ["git_sources", "upsert_git_source", "import_git_sources"],
    UrlSource: ["url_sources", "upsert_url_source", "import_url_sources"],
    Repo: ["repos", "upsert_repo", "import_repos"],
    Project: ["projects", "upsert_project", "import_projects"],
    Benchmark: ["benchmarks", "upsert_benchmark", "import_benchmarks"],
    AnalysisResult: ["analysis_results", "upsert_analysis_result", "import_analysis_results"]
}

def class_lookup(model):
    if isinstance(model, NJRDocument):
        return model.__class__
    else:
        return CLASS_LOOKUP[model.__class__]

def build_query_method(cls):
    def fun(**kwargs):
        return cls.objects(**kwargs)
    return fun

def build_upsert_method(cls):
    def fun(model):
        return cls.upsert(model)
    return fun

def build_import_method(cls):
    def fun(models, upsert=True):
        docs = [cls.get_or_init(model).merge(model) for model in models]
        new = [doc for doc in docs if not doc.id]
        old = []
        if new:
            new = cls.objects.insert(new)
        if upsert:
            old = [doc for doc in docs if doc.id]
            for doc in old:
                doc.save()
        return old + new
    return fun

for c, l in METHOD_LOOKUP.items():
    setattr(Database, l[0], staticmethod(build_query_method(CLASS_LOOKUP[c])))
    setattr(Database, l[1], staticmethod(build_upsert_method(CLASS_LOOKUP[c])))
    setattr(Database, l[2], staticmethod(build_import_method(CLASS_LOOKUP[c])))
