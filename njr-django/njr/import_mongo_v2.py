from mongoengine import *
from mongo.documents import RepoSourceDocument, RepoDocument, ProjectDocument, BenchmarkDocument, AnalysisResultDocument
import MySQLdb
import json
import uuid

def add_raw_repo():
    print("Building Raw Repo")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE raw_repo;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_raw_repo = ("INSERT INTO raw_repo "
                    "(mongo_id, _cls, name, url, uuid) "
                    "VALUES (%s, %s, %s, %s, %s)")

    connect('njr')
    for obj in RepoSourceDocument.objects:
        data_raw_repo = (str(obj.id), obj._cls, obj.name, obj.url, uuid.uuid4().hex)
        cursor.execute(add_raw_repo, data_raw_repo)

    db.commit()

def add_processed_repo():
    print("Building Processed Repo")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE processed_repo;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_processed_repo = ("INSERT INTO processed_repo "
                    "(mongo_id, raw_repo_id, sha256, path, uuid) "
                    "VALUES (%s, %s, %s, %s, %s)")

    connect('njr')
    for obj in RepoDocument.objects:

        #get repo source id
        cursor.execute("SELECT raw_repo_id FROM njr_v2.raw_repo WHERE mongo_id = '" + str(obj.to_mongo()['repo_source']) + "' LIMIT 1;")
        raw_repo_id = cursor.fetchone()[0] 

        data_processed_repo = (str(obj.id), raw_repo_id, obj.sha256, obj.path, uuid.uuid4().hex)
        cursor.execute(add_processed_repo, data_processed_repo)
    
    db.commit()

def add_project():
    print("Building Raw Project")
    print("Building Processed Project")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE raw_project;")
    cursor.execute("TRUNCATE TABLE processed_project;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_class = ("INSERT INTO class "
        "(processed_project_id, name, uuid) "
        "VALUES (%s, %s, %s)")

    add_main_class = ("INSERT INTO class "
        "(processed_project_id, name, uuid, is_mainclass) "
        "VALUES (%s, %s, %s, 1)")

    add_raw_project = ("INSERT INTO raw_project "
                    "(mongo_id, name, subfolder, javaversion, processed_repo_id, uuid) "
                    "VALUES (%s, %s, %s, %s, %s, %s)")
                
    add_processed_project = ("INSERT INTO processed_project "
                    "(mongo_id, raw_project_id, sha256, path, buildwith, uuid) "
                    "VALUES (%s, %s, %s, %s, %s, %s)")

    update_mainclass = ("UPDATE class SET is_mainclass = 1 WHERE name = %s AND processed_project_id = %s")

    connect('njr')
    for obj in ProjectDocument.objects.batch_size(10): 

        #get processed_repo id
        cursor.execute("SELECT processed_repo_id FROM njr_v2.processed_repo WHERE mongo_id = '" + str(obj.to_mongo()['repo']) + "' LIMIT 1;")
        processed_repo_id = cursor.fetchone()[0]

        data_raw_project = (str(obj.id), obj.name, obj.subfolder, obj.javaversion, processed_repo_id, uuid.uuid4().hex)
        cursor.execute(add_raw_project, data_raw_project)
        raw_project_id = cursor.lastrowid

        data_processed_project = (str(obj.id), raw_project_id, obj.sha256, obj.path, obj.buildwith, uuid.uuid4().hex)
        cursor.execute(add_processed_project, data_processed_project)
        processed_project_id = cursor.lastrowid

        #add classes (assuming main classes are added here as well)
        for c in obj.classes:
            data_class = (processed_project_id,c,uuid.uuid4().hex)
            cursor.execute(add_class, data_class)
        
        for m in obj.mainclasses:
            if m in obj.classes:
                data_update_class = (m,processed_project_id)
                cursor.execute(update_mainclass, data_update_class)
            else:
                data_class = (processed_project_id,m,uuid.uuid4().hex)
                cursor.execute(add_main_class, data_class)
                print("main class mismatch")

    db.commit()

def add_program():
    print("Building Raw Program")
    print("Building Processed Program")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE raw_program;")
    cursor.execute("TRUNCATE TABLE processed_program;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_raw_program = ("INSERT INTO raw_program "
                    "(mongo_id, name, mainclass_id, uuid) "
                    "VALUES (%s, %s, %s, %s)")

    add_processed_program = ("INSERT INTO processed_program "
                    "(mongo_id, raw_program_id, uuid) "
                    "VALUES (%s, %s, %s)")

    connect('njr')
    for obj in BenchmarkDocument.objects.batch_size(10):

        #get processed_project id
        cursor.execute("SELECT processed_project_id FROM njr_v2.processed_project WHERE mongo_id = '" + str(obj.to_mongo()['project']) + "' LIMIT 1;")
        processed_project_id = cursor.fetchone()[0]

        #get mainclass_id id
        cursor.execute("SELECT class_id FROM njr_v2.class WHERE name = '" + obj.mainclass + "' AND processed_project_id = " + str(processed_project_id) + " LIMIT 1;")
        mainclass_id = cursor.fetchone()[0]

        data_raw_program = (str(obj.id), obj.name, mainclass_id, uuid.uuid4().hex)
        cursor.execute(add_raw_program, data_raw_program)
        raw_program_id = cursor.lastrowid

        data_processed_program = (str(obj.id), raw_program_id, uuid.uuid4().hex)
        cursor.execute(add_processed_program, data_processed_program)
        raw_program_id = cursor.lastrowid

    db.commit()

def add_run():
    print("Building Raw Run")
    print("Building Processed Run")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE raw_run;")
    cursor.execute("TRUNCATE TABLE processed_run;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_raw_run = ("INSERT INTO raw_run "
                    "(mongo_id, processed_program_id, input_name, args, stdin, uuid) "
                    "VALUES (%s, %s, %s, %s, %s, %s)")

    add_processed_run = ("INSERT INTO processed_run "
                    "(mongo_id, name, analysis, raw_run_id, world, upper, path, lower, difference, uuid) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    connect('njr')
    for obj in AnalysisResultDocument.objects.batch_size(10):

        #get processed_program id
        cursor.execute("SELECT processed_program_id FROM njr_v2.processed_program WHERE mongo_id = '" + str(obj.to_mongo()['benchmark']) + "' LIMIT 1;")
        processed_program_id = cursor.fetchone()[0]

        pp = BenchmarkDocument.objects(id = str(obj.to_mongo()['benchmark']))[0]

        data_raw_run = (str(obj.id), processed_program_id, pp.inputs[0].name, json.dumps(pp.inputs[0].args), pp.inputs[0].stdin, uuid.uuid4().hex)
        cursor.execute(add_raw_run, data_raw_run)
        raw_run_id = cursor.lastrowid

        data_processed_run = (str(obj.id), obj.name, obj.analysis, raw_run_id, obj.world, obj.upper, obj.path, obj.lower, obj.difference, uuid.uuid4().hex)
        cursor.execute(add_processed_run, data_processed_run)

    db.commit()


db = MySQLdb.connect("localhost","root","supersecretpassword","njr_v2")
cursor = db.cursor()

#add_raw_repo()
#add_processed_repo()
add_project()
add_program()
add_run()

cursor.close()
db.close()
