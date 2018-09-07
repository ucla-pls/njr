from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from app.models import Job, Tool
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import uuid
from rest_framework.test import APIClient
import json
import subprocess
from job import *
from django.db import connection

"""
Executes a command as if it were in the shell
"""
def run_cmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = process.communicate()
    out = out.decode("utf-8") 
    err = err.decode("utf-8") 
    return out, err

"""
Make a dummy job that prints a random string
"""
def make_dummy_job():
    job = Job(
        complete = False,
        error = False,
        visited = datetime.now(),
        buildid = 'buildid',
        timing = 0.0,
        script = """
        with import <nixpkgs> {};
        stdenv.mkDerivation {
        name = "example";
            phases = "installPhase";
            installPhase = ''
            echo "Random String: """ + uuid.uuid4().hex + """\";
            mkdir $out
            touch $out/hello
            '';
        }
        """
    )
    job.save()

"""
URL to delete all jobs
"""
def delete_dummy_jobs(request):
    Job.objects.all().delete()

    #return success
    obj = {}
    obj['data'] = None
    obj['message'] = 'success'
    return JsonResponse(obj) 

"""
URL to make 10 dummy jobs for testing
"""
def make_dummy_jobs(request):
    for i in range(10):
        make_dummy_job()

    #return success
    obj = {}
    obj['data'] = None
    obj['message'] = 'success'
    return JsonResponse(obj)   


def q_count_reachable(**args):
    return """
    SELECT mainclass_id,method_count FROM reachable_method_count
    WHERE tool_id = {tool_id} AND method_count >= {start!s} AND method_count < {end!s}
    """.format(**args)

"""
Base URL to just show hello world
"""
def index(request):
    res = None
    if request.method == "GET":
        req = dict(
            tool_id=int(request.GET.get('tool_id', 2)),
            start=int(request.GET.get('start', 100)),
            end=int(request.GET.get('end', 200))
        )

        with connection.cursor() as cursor:
            query = """
            SELECT raw_project.name, class.name, count.method_count FROM ({} LIMIT 10) count
            INNER JOIN class ON count.mainclass_id = class.class_id
            INNER JOIN processed_project ON class.processed_project_id = processed_project.processed_project_id
            INNER JOIN raw_project ON processed_project.raw_project_id = raw_project.raw_project_id
            """.format(q_count_reachable(**req))
            cursor.execute(query)
            res = cursor.fetchall()

            cursor.execute("""
            SELECT COUNT(*) FROM ({}) a
            """.format(q_count_reachable(**req)))
            total = cursor.fetchone()

    tools = Tool.objects.all()
    return render(request, "app/index.html", dict(results=res, tools=tools, page="q1", total=total[0], **req))

"""
Display basic information about a project
"""
def project(request, project_name=None):

    project = {
        "name" : project_name
      }
    with connection.cursor() as cursor:
        query = """
        SELECT name, path, processed_project.processed_project_id FROM raw_project
        INNER JOIN processed_project
          ON processed_project.raw_project_id = raw_project.raw_project_id
        WHERE name = "{}"
        """.format(project_name)
        print (query)
        cursor.execute(query)
        (name, path, ppid) = cursor.fetchone()

        project["path"] = path

        query = """
        SELECT DISTINCT name FROM class
        WHERE processed_project_id = "{}"
            AND is_mainclass IS NULL
        ORDER BY name
        """.format(ppid)
        cursor.execute(query)
        project["classes"] = cursor.fetchall()

        query = """
        SELECT DISTINCT name FROM class
        WHERE processed_project_id = "{}"
            AND is_mainclass is not NULL
        ORDER BY name
        """.format(ppid)
        cursor.execute(query)
        project["mainclasses"] = cursor.fetchall()

    return render(request, "app/project.html", dict(page="project", project=project))

def query2(request):
    res = None
    if request.method == "POST":
        with connection.cursor() as cursor:
            query = """
            SELECT raw_program.name as name, iCount / uCount as jaccard FROM
            (
                SELECT mainclass_id, COUNT(*) AS uCount FROM 
                (
                    SELECT method_id, mainclass_id FROM njr_v2.reachable_method WHERE tool_id = """ + request.POST['tool_id1'] + """
                    UNION 
                    SELECT method_id, mainclass_id FROM njr_v2.reachable_method WHERE tool_id = """ + request.POST['tool_id2'] + """
                ) as u
                GROUP BY mainclass_id
            ) AS uTbl

            INNER JOIN

            (
                SELECT mainclass_id, COUNT(*) AS iCount FROM 
                (
                    SELECT method_id, mainclass_id FROM njr_v2.reachable_method as rmi1 WHERE tool_id = """ + request.POST['tool_id1'] + """
                    AND EXISTS 
                    (
                        SELECT * FROM 
                        njr_v2.reachable_method as rmi2 
                        WHERE tool_id = """ + request.POST['tool_id2'] + """
                        AND rmi1.method_id = rmi2.method_id
                        AND rmi1.mainclass_id = rmi2.mainclass_id
                    )
                ) as i
                GROUP BY mainclass_id
            ) AS iTbl

            ON uTbl.mainclass_id = iTbl.mainclass_id

            INNER JOIN njr_v2.raw_program ON uTbl.mainclass_id = raw_program.mainclass_id
            WHERE iCount / uCount <= """ + request.POST['jaccard'] + """
            LIMIT 10"""
            cursor.execute(query)
            res = cursor.fetchall()

    tools = Tool.objects.all()
    return render(request, "app/query2.html", {"results": res, "tools": tools, "page" : "q2" })

def query3(request):
    res = None
    if request.method == "POST":
        with connection.cursor() as cursor:
            query = """
            SELECT tbl3.mainclass_id FROM 
            (
                SELECT tbl1.mainclass_id, COUNT(tbl1.mainclass_id) as intersect FROM
                (
                    SELECT mainclass_id, method_id, tool_id FROM njr_v2.reachable_method 
                    WHERE tool_id = """ + request.POST['tool_id1'] + """
                ) as tbl1
                INNER JOIN 
                (
                    SELECT mainclass_id, method_id, tool_id FROM njr_v2.reachable_method 
                    WHERE tool_id = """ + request.POST['tool_id2'] + """
                ) as tbl2
                ON tbl1.mainclass_id = tbl2.mainclass_id AND tbl1.method_id = tbl2.method_id
                GROUP BY tbl1.mainclass_id
            ) as tbl3

            INNER JOIN

            (
                SELECT mainclass_id, COUNT(mainclass_id) as total FROM njr_v2.reachable_method 
                WHERE tool_id = """ + request.POST['tool_id1'] + """
                GROUP BY mainclass_id
            ) as tbl4

            ON tbl4.mainclass_id = tbl3.mainclass_id
            WHERE intersect <> total
            LIMIT 10"""
            cursor.execute(query)
            res = cursor.fetchall()

    tools = Tool.objects.all()
        
    return render(request, "app/query3.html", {"results": res, "tools": tools, "page" : "q3" })

def query4(request):
    res = None
    if request.method == "POST":
        with connection.cursor() as cursor:
            query = """
            SELECT raw_program.name, COUNT(raw_program_id) FROM njr_v2.reachable_method 
            INNER JOIN njr_v2.raw_program ON reachable_method.mainclass_id = raw_program.mainclass_id
            WHERE reachable_method.tool_id = """ + request.POST['tool_id'] + """
            GROUP BY raw_program.raw_program_id, raw_program.name
            HAVING COUNT(raw_program_id) > """ + request.POST['start'] + """ AND COUNT(raw_program_id) < """ + request.POST['end'] + """
            LIMIT 10"""
            cursor.execute(query)
            res = cursor.fetchall()

    tools = Tool.objects.all()
        
    return render(request, "app/query4.html", {"results": res, "tools": tools, "page" : "q4" })


# def get_derivation():
#     #out, err = run_cmd("vagrant ssh -c 'ls'")
#     return None

# def make_derivation():
#     return None

# def put_in_nix_store():
#     return None

# def from_folder():
#     return None

"""
Get a single random job or mark a job as complete
"""
@csrf_exempt
def job(request):

    #gets a job
    if request.method == 'GET':

        #get a random job
        job_object = Job.objects.filter(complete = False)
        if job_object:
            job_object = job_object[0]

            #return it as json
            obj = {}
            obj['job_id'] = job_object.job_id
            obj['filename'] = "default.nix"
            obj['drv'] = job_object.script
            obj['message'] = 'success'
        else:
            obj = {}
            obj['message'] = 'empty'
        return JsonResponse(obj)


    elif request.method == 'POST':

        #get the post data
        data = json.loads(request.body)
        job_id = data['job_id']
        on_machine = data['on_machine']
        result_folder = data['result_folder']

        #expose data from client
        #make sure result folder is visible to server
        #out, err = run_cmd("vagrant ssh -c 'nix-copy-closure --from vagrant@127.0.0.1:" + on_machine + " " + result_folder + "'")

        #return error
        #if err:
        #    obj = {}
        #    obj['data'] = None
        #    obj['message'] = err
        #    return JsonResponse(obj)

        job = Job.objects.get(job_id=job_id)
        job.complete = True
        job.save()

        #return success
        obj = {}
        obj['data'] = None
        obj['message'] = 'success'
        return JsonResponse(obj)
    else:
        return HttpResponseNotFound()

