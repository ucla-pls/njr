from mongoengine import *
from mongo.documents import RepoSourceDocument, RepoDocument, ProjectDocument, BenchmarkDocument, AnalysisResultDocument
import MySQLdb
import json
import uuid
import json
import sys

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

def add_method_analysis():
    print("Adding method analysis")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE reachable_method;")
    cursor.execute("TRUNCATE TABLE method;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    add_method = ("INSERT INTO method "
                    "(class_id, name, uuid) "
                    "VALUES (%s, %s, %s)")

    add_reachable_method = ("INSERT INTO reachable_method "
                    "(method_id, tool_id, mainclass_id, uuid) "
                    "VALUES (%s, %s, %s, %s)")

    with open('/Users/alex/Drive/capstone/results.json') as f:
        i = 0
        p = 0
        for line in f:
            i += 1
            if i % 1524 == 0:
                p += 1
                print(str(p) + '%')
                db.commit()
            obj = json.loads(line)
            project = obj['project']
            mainclass_escaped = obj['mainclass']
            mainclass = mainclass_escaped.replace("/", ".")
            cursor.execute("SELECT pprj.processed_project_id, class.class_id FROM njr_v2.class as class "
                "INNER JOIN njr_v2.processed_project as pprj ON class.processed_project_id = pprj.processed_project_id "
                "INNER JOIN njr_v2.raw_project as rprj ON pprj.raw_project_id = rprj.raw_project_id "
                "WHERE rprj.name = '" + project + "' "
                "AND class.name = '" + mainclass + "' "
                "ORDER BY class_id")
            res = cursor.fetchone()
            processed_project_id = res[0]
            mainclass_id = res[1]

            for class_name_escaped in obj['reachable-methods']:
                class_name = class_name_escaped.replace("/", ".")
                cursor.execute("SELECT * FROM njr_v2.class "
                    "WHERE name = '" + class_name + "' "
                    "AND processed_project_id = " + str(processed_project_id) + " "
                    "ORDER BY class_id")
                class_id = cursor.fetchone()[0]
                for method_name in obj['reachable-methods'][class_name_escaped]:
                    data_method = (class_id, method_name, uuid.uuid4().hex)
                    cursor.execute(add_method, data_method)
                    method_id = cursor.lastrowid

                    if "W" in obj['reachable-methods'][class_name_escaped][method_name]:
                        data_reachable_method = (method_id, 3, mainclass_id, uuid.uuid4().hex)
                        cursor.execute(add_reachable_method, data_reachable_method)
                    
                    if "P" in obj['reachable-methods'][class_name_escaped][method_name]:
                        data_reachable_method = (method_id, 2, mainclass_id, uuid.uuid4().hex)
                        cursor.execute(add_reachable_method, data_reachable_method)

                    if "D" in obj['reachable-methods'][class_name_escaped][method_name]:
                        data_reachable_method = (method_id, 4, mainclass_id, uuid.uuid4().hex)
                        cursor.execute(add_reachable_method, data_reachable_method)

    print("Done!")
    db.commit()


db = MySQLdb.connect("localhost","root","supersecretpassword","njr_v2")
cursor = db.cursor()

#add_raw_repo()
#add_processed_repo()
#add_project()
#add_program()
#add_run()
add_method_analysis()

cursor.close()
db.close()


# SELECT COUNT(*) FROM (SELECT raw_program_id, COUNT(raw_program_id) FROM njr_v2.reachable_method 
# INNER JOIN njr_v2.method ON reachable_method.method_id = method.method_id
# INNER JOIN njr_v2.class ON method.class_id = class.class_id
# INNER JOIN njr_v2.raw_program ON class.class_id = raw_program.mainclass_id
# GROUP BY raw_program.raw_program_id
# HAVING COUNT(raw_program_id) > 100 AND COUNT(raw_program_id) < 200) as tbl;

# SELECT COUNT(*) FROM (SELECT raw_program_id, COUNT(raw_program_id) FROM njr_v2.reachable_method 
# INNER JOIN njr_v2.raw_program ON reachable_method.mainclass_id = raw_program.mainclass_id
# GROUP BY raw_program.raw_program_id
# HAVING COUNT(raw_program_id) > 100 AND COUNT(raw_program_id) < 200) as tbl;


# SELECT uTbl.mainclass_id, iCount / uCount FROM

# (
# 	SELECT mainclass_id, COUNT(*) AS uCount FROM 
# 	(
# 		SELECT method_id, mainclass_id FROM njr_v2.reachable_method WHERE tool_id = 2
# 		UNION 
# 		SELECT method_id, mainclass_id FROM njr_v2.reachable_method WHERE tool_id = 3
# 	) as u
# 	GROUP BY mainclass_id
# ) AS uTbl

# INNER JOIN

# (
# 	SELECT mainclass_id, COUNT(*) AS iCount FROM 
# 	(
# 		SELECT method_id, mainclass_id FROM njr_v2.reachable_method as rmi1 WHERE tool_id = 2
# 		AND EXISTS 
# 		(
# 			SELECT * FROM 
# 			njr_v2.reachable_method as rmi2 
# 			WHERE tool_id = 3
# 			AND rmi1.method_id = rmi2.method_id
# 			AND rmi1.mainclass_id = rmi2.mainclass_id
# 		)
# 	) as i
# 	GROUP BY mainclass_id
# ) AS iTbl

# ON uTbl.mainclass_id = iTbl.mainclass_id



# SELECT COUNT(*) FROM 
# (
# 	SELECT tbl3.mainclass_id FROM 
# 	(
# 		SELECT tbl1.mainclass_id, COUNT(tbl1.mainclass_id) as intersect FROM
# 		(
# 			SELECT mainclass_id, method_id, tool_id FROM njr_v2.reachable_method 
# 			WHERE tool_id = 3
# 		) as tbl1
# 		INNER JOIN 
# 		(
# 			SELECT mainclass_id, method_id, tool_id FROM njr_v2.reachable_method 
# 			WHERE tool_id = 2
# 		) as tbl2
# 		ON tbl1.mainclass_id = tbl2.mainclass_id AND tbl1.method_id = tbl2.method_id
# 		GROUP BY tbl1.mainclass_id
# 	) as tbl3

# 	INNER JOIN

# 	(
# 		SELECT mainclass_id, COUNT(mainclass_id) as total FROM njr_v2.reachable_method 
# 		WHERE tool_id = 3
# 		GROUP BY mainclass_id
# 	) as tbl4

# 	ON tbl4.mainclass_id = tbl3.mainclass_id
# 	WHERE intersect = total
# ) as tbl5