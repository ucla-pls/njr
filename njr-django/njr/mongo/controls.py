from njr.documents import *
from njr.models import *
from njr.exceptions import *
from njr.utils import only, omit
import njr.jbxutils as jbx
import njr

import os
import json
import time
import mongoengine
from functools import partial
from multiprocessing import Pool

import logging
logger = logging.getLogger(__name__)
timelog = logging.getLogger("measurements")

class NJR:
    def __init__(self, db, config={}):
        # additional data for building ("populating") repos/projects
        self.db = db
        self.config = config

    def sources_status(self):
        return {
            "git-source": {
                "total": self.db.git_sources().count()
            },
            "url-source": {
                "total": self.db.url_sources().count()
            }
        }

    def repos_status(self):
        repos = self.db.repos()
        buildable = repos.filter(buildable=True)
        unbuildable = repos.filter(buildable=False)
        built = repos.filter(path__ne=None)

        return {
            "total": repos.count(),
            "buildable": buildable.count(),
            "unbuildable": unbuildable.count(),
            "built": built.count()
        }

    def projects_status(self):
        projects = self.db.projects()
        buildable = projects.filter(buildable=True)
        unbuildable = projects.filter(buildable=False)
        built = projects.filter(path__ne=None)

        nzclasses = built.filter(classes__not__size=0)
        nzmainclasses = built.filter(mainclasses__not__size=0)

        return {
            "total": projects.count(),
            "buildable": buildable.count(),
            "unbuildable": unbuildable.count(),
            "built": {
                "total": built.count(),
                "has-classes": nzclasses.count(),
                "has-mainclasses": nzmainclasses.count()
            }
        }

    def benchmarks_status(self):
        return {"total": self.db.benchmarks().count()}

    def analysis_results_status(self):
        analysis_results = self.db.analysis_results()
        buildable = analysis_results.filter(buildable=True)
        unbuildable = analysis_results.filter(buildable=False)
        built = analysis_results.filter(path__ne=None)

        status = {}
        for analysis in analysis_results.distinct("analysis"):
            status[analysis] = {
                "total": analysis_results.filter(analysis=analysis).count(),
                "buildable": buildable.filter(analysis=analysis).count(),
                "unbuildable": unbuildable.filter(analysis=analysis).count(),
                "built": built.filter(analysis=analysis).count()
            }

        status["total"] = analysis_results.count()
        status["buildable"] = buildable.count()
        status["unbuildable"] = unbuildable.count()
        status["built"] = built.count()
        return status

    def status(self):
        return {
            "source": self.sources_status(),
            "repo": self.repos_status(),
            "project": self.projects_status(),
            "benchmark": self.benchmarks_status(),
            "analysis-result": self.analysis_results_status()
        }

    def get_repo_source(self, name):
        try:
            return self.db.repo_sources(name=name).get()
        except njr.documents.DoesNotExist:
            raise NJRArgumentError("No such repo source: " + name)

    def get_benchmark(self, name):
        try:
            return self.db.benchmarks(name=name).get()
        except njr.documents.DoesNotExist:
            raise NJRArgumentError("No such benchmark: " + name)

    def add_repo_sources(self, sources):
        start = time.perf_counter()

        rsrcs = self.db.import_models(set(sources))
        s_end = time.perf_counter()

        timelog.info("Adding repo sources took %s secs.", s_end - start)
        return rsrcs

    def populate(self, **kwargs):
        start = time.perf_counter()
        self.populate_repos(**kwargs)
        self.populate_projects(**kwargs)
        self.populate_benchmarks(**kwargs)
        timelog.info("Populating end-to-end took %s secs.", time.perf_counter() - start)

    def populate_repos(self, **kwargs):
        start = time.perf_counter()
        logger.info("Generating repos from sources.")
        count = 0
        for source in self.db.repo_sources():
            count += len(
                self.db.import_repos(
                    source.generate_repos(),
                    upsert=False
                ))

        logger.info("Created %s new repos.", count)
        logger.info("Populating repos.")
        self.populate_models(self.db.repos(), **kwargs)
        logger.info("Done populating repos.")
        timelog.info("Populating repos took %s secs.", time.perf_counter() - start)

    def populate_projects(self, **kwargs):
        start = time.perf_counter()
        logger.info("Generating projects from repos.")
        count = 0
        javav = self.config["javaversion"] if self.config else njr.JAVAVERSION
        for repo in self.db.repos():
            count += len(
                self.db.import_projects(
                    repo.generate_projects(javav),
                    upsert=False
                ))

        logger.info("Created %s new projects.", count)
        logger.info("Populating projects.")
        self.populate_models(self.db.projects(), **kwargs)
        logger.info("Done populating projects.")
        timelog.info("Populating projects took %s secs.", time.perf_counter() - start)

    def populate_benchmarks(self, **kwargs):
        start = time.perf_counter()
        logger.info("Generating benchmarks from projects.")
        count = 0
        for project in self.db.projects():
            count += len(
                self.db.import_benchmarks(
                    project.generate_benchmarks(),
                    upsert=False
                ))
        logger.info("Created %s new benchmarks.", count)
        timelog.info("Populating benchmarks took %s secs.", time.perf_counter() - start)

    def populate_source(self, source, **kwargs):
        start = time.perf_counter()
        logger.info("Generating repo for source %s.", source.name)
        self.db.import_repos(source.generate_repos(), upsert=False)

        logger.info("Populating repo for source %s.", source.name)
        self.populate_models(self.db.repos(repo_source=source), **kwargs)
        logger.info("Done populating repo for source %s.", source.name)

        javav = self.config["javaversion"] if self.config else njr.JAVAVERSION
        for repo in self.db.repos(repo_source=source):
            logger.info("Generating projects for repo %s.", repo.name)
            proj_c = len(self.db.import_projects(repo.generate_projects(javav), upsert=False))
            logger.info("Created %s new projects for repo %s.", proj_c, repo.name)

            logger.info("Populating projects for repo %s.", repo.name)
            self.populate_models(self.db.projects(repo=repo), **kwargs)
            logger.info("Done populating projects.")

            for project in self.db.projects(repo=repo):
                bmrk_c = len(self.db.import_benchmarks(project.generate_benchmarks(), upsert=False))
                logger.info("Created %s new benchmarks for project %s.", bmrk_c, project.name)
        timelog.info("Populating source %s took %s secs.", source.name, time.perf_counter() - start)

    def analyze(self, analysis, benchmark=None, **kwargs):
        start = time.perf_counter()
        if benchmark:
            benchmarks = [benchmark]
            a_results = self.db.analysis_results(benchmark=benchmark, analysis=analysis)
        else:
            benchmarks = self.db.benchmarks()
            a_results = self.db.analysis_results(analysis=analysis)
            logger.info("Analyze %s benchmarks.", benchmarks.count())

        for bmark in benchmarks:
            self.db.import_analysis_results(
                bmark.generate_analysis_results(analysis),
                upsert=False
            )

        self.populate_models(a_results, **kwargs)
        timelog.info("Analyzing %s on benchmark(s) took %s secs.", analysis, time.perf_counter() - start)

    def populate_models(self, models, retry=False, nproc=None):
        if not retry:
            models = models.filter(buildable=True, path=None)
        results = Populator(self.config).populate_async(models.timeout(False), nproc=nproc)
        for result in results:
            self.db.upsert_model(result)

class Populator():

    def __init__(self, config):
        self.config = config

    def populate(self, model):
        from random import randrange
        jobid = '%05x' % randrange(16**5)
        log = logger.getChild(jobid)
        self.config["logger"] = log

        log.info("Populating %r", model.name)
        try:
            env = njr.get_jbx_env(self.config) if self.config else jbx.STDENV
            model.populate(self.config, env)
        except Exception as e:
            log.warn("Could not populate, %r", e)
        log.info("Done populating")

        return model

    def populate_async(self, models, nproc=None):
        with Pool(processes=nproc) as pool:
            yield from pool.imap_unordered(self.populate, models)
