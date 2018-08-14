from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from app.models import Job
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import uuid
from rest_framework.test import APIClient
import json
import subprocess
from job import *

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

"""
Base URL to just show hello world
"""
def index(request):
    print_hi()
    return render(request, "app/index.html")


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

