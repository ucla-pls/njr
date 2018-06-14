from mongoengine import *
from mongo.documents import RepoSourceDocument, RepoDocument, ProjectDocument, BenchmarkDocument, AnalysisResultDocument
import MySQLdb
import json

def add_repo_source():
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE repo_source;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_repo_source = ("INSERT INTO repo_source "
                    "(mongo_id, _cls, name, visited, url) "
                    "VALUES (%s, %s, %s, %s, %s)")

    connect('njr')
    for obj in RepoSourceDocument.objects:
        data_repo_source = (str(obj.id), obj._cls, obj.name, obj.visited, obj.url)
        cursor.execute(add_repo_source, data_repo_source)

    db.commit()

def add_repo():
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE repo;")
    cursor.execute("TRUNCATE TABLE stats;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_stats = ("INSERT INTO stats "
        "(buildid, timing) "
        "VALUES (%s, %s)")

    add_repo = ("INSERT INTO repo "
                    "(mongo_id, name, subfolders, repo_source_id, visited, sha256, path, stats_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")

    connect('njr')
    for obj in RepoDocument.objects:

        #get repo source id
        cursor.execute("SELECT repo_source_id FROM njr.repo_source WHERE mongo_id = '" + str(obj.to_mongo()['repo_source']) + "' LIMIT 1;")
        repo_source_id = cursor.fetchone()[0]

        #add stats object
        data_stats = (obj.stats['buildid'], obj.stats['timing'])
        cursor.execute(add_stats, data_stats)
        stats_id = cursor.lastrowid  

        data_repo = (str(obj.id), obj.name, json.dumps(obj.subfolders), repo_source_id, obj.visited, obj.sha256, obj.path, stats_id)
        cursor.execute(add_repo, data_repo)
    
    db.commit()

def add_project():
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE project;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_stats = ("INSERT INTO stats "
        "(buildid, timing) "
        "VALUES (%s, %s)")

    add_class = ("INSERT INTO class "
        "(name) "
        "VALUES (%s)")

    add_project_class = ("INSERT INTO project_class "
        "(project_id, class_id) "
        "VALUES (%s, %s)")

    add_project_mainclass = ("INSERT INTO project_mainclass "
        "(project_id, class_id) "
        "VALUES (%s, %s)")

    add_project = ("INSERT INTO project "
                    "(mongo_id, name, subfolder, javaversion, repo_id, visited, sha256, path, buildwith, stats_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    connect('njr')
    for obj in ProjectDocument.objects:

        #add stats object
        data_stats = (obj.stats['buildid'], obj.stats['timing'])
        cursor.execute(add_stats, data_stats)
        stats_id = cursor.lastrowid  

        #get repo id
        cursor.execute("SELECT repo_id FROM njr.repo WHERE mongo_id = '" + str(obj.to_mongo()['repo']) + "' LIMIT 1;")
        repo_id = cursor.fetchone()[0]

        data_project = (str(obj.id), obj.name, obj.subfolder, obj.javaversion, repo_id, obj.visited, obj.sha256, obj.path, obj.buildwith, stats_id)
        cursor.execute(add_project, data_project)
        project_id = cursor.lastrowid

        #add classes
        for c in obj.classes:
            data_class = (c,)
            cursor.execute(add_class, data_class)
            class_id = cursor.lastrowid
            data_project_class = (project_id, class_id)
            cursor.execute(add_project_class, data_project_class)

        #add main classes
        for c in obj.mainclasses:
            data_class = (c,)
            cursor.execute(add_class, data_class)
            class_id = cursor.lastrowid
            data_project_mainclass = (project_id, class_id)
            cursor.execute(add_project_mainclass, data_project_mainclass)

    db.commit()
        
def add_benchmark():
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE benchmark;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_class = ("INSERT INTO class "
        "(name) "
        "VALUES (%s)")

    add_input = ("INSERT INTO input "
        "(name, args, stdin, benchmark_id) "
        "VALUES (%s, %s, %s, %s)")

    add_benchmark = ("INSERT INTO benchmark "
                    "(mongo_id, name, mainclass_id, project_id, visited) "
                    "VALUES (%s, %s, %s, %s, %s)")

    connect('njr')
    for obj in BenchmarkDocument.objects.batch_size(10):

        #get project id
        cursor.execute("SELECT project_id FROM njr.project WHERE mongo_id = '" + str(obj.to_mongo()['project']) + "' LIMIT 1;")
        project_id = cursor.fetchone()[0]

        #add main class
        data_class = (obj.mainclass,)
        cursor.execute(add_class, data_class)
        mainclass_id = cursor.lastrowid

        data_benchmark = (str(obj.id), obj.name, mainclass_id, project_id, obj.visited)
        cursor.execute(add_benchmark, data_benchmark)
        benchmark_id = cursor.lastrowid

        #add inputs
        for input in obj.inputs:
            data_input = (input.name, json.dumps(input.args), input.stdin, benchmark_id)
            cursor.execute(add_input, data_input)

    db.commit()

def add_analysis_result():
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE analysis_result;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_stats = ("INSERT INTO stats "
        "(buildid, timing) "
        "VALUES (%s, %s)")

    add_analysis_result = ("INSERT INTO analysis_result "
                    "(mongo_id, name, analysis, benchmark_id, visited, world, upper, path, lower, stats_id, difference) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    connect('njr')
    for obj in AnalysisResultDocument.objects.batch_size(10):
        #add stats object
        data_stats = (obj.stats['buildid'], obj.stats['timing'])
        cursor.execute(add_stats, data_stats)
        stats_id = cursor.lastrowid  

        #get benchmark id
        cursor.execute("SELECT benchmark_id FROM njr.benchmark WHERE mongo_id = '" + str(obj.to_mongo()['benchmark']) + "' LIMIT 1;")
        benchmark_id = cursor.fetchone()[0]

        data_analysis_result = (str(obj.id), obj.name, obj.analysis, benchmark_id, obj.visited, obj.world, obj.upper, obj.path, obj.lower, stats_id, obj.difference)
        cursor.execute(add_analysis_result, data_analysis_result)

    db.commit()


db = MySQLdb.connect("localhost","root","supersecretpassword","njr")
cursor = db.cursor()

#add_repo_source()
#add_repo()
#add_project()
#add_benchmark()
add_analysis_result()

cursor.close()
db.close()
