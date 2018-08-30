# QUESTIONS

* what is the method name? what is init?
* need json that parses

# SETUP

After downloading git repo...

MySQL needs to be installed.
Additionally, MySQL Workbench is nice.
Make sure server's root user has password 'supersecretpassword' or else you have to change it in Django's settings.py file.
In MySQL Workbench --> server --> Data Import... Choose folder 'mysql dump'.

In terminal from root dir...

```
source virtualenv/virtualenv/bin/activate 
cd njr-django
python manage.py runserver 
```

go to http://127.0.0.1:8000/

most interesting code in:
```
/njr-django/app/views.py
/njr-django/njr/import_mongo_v2.py
```

To simulate jobs

In terminal from root dir...

```
cd vagrant-client
vagrant up
vagrant ssh
cd /vagrant_data
source client.sh
```

client.sh is a shell script that first deletes all existing jobs, then makes 10 jobs that contain nix scripts to print a random string. It then builds the scripts and marks the jobs as complete on the server side. When all jobs are complete it stops. 

# TODOS

* get a sandbox 

* get nix-copy-closure to work

* determine relevant queries and update index.html

* fill in stubbed functions in jobs.py (these will be run by the client but for now will live server side)
  * how I imagine the workflow
    * clients are constantly pulling jobs
    * jobs are generic and can be any of the 5 types below
    * each job has json data that contains all the relevant info to be run 
    * first, the client determines the type, then runs the appropriate function

  * init_repo
    * function to load data into database from repos on the web
    * raw repo is empty
    * add a raw repo to the database
    * at the same time, add a job for a client to pick up to process the raw repo
  
  * process_repo
    * client pull a raw repo job 
    * process it
    * add processed repo and raw projects 
    * add job for each raw project
    
  * process_project
    * client pull a raw project job
    * process it, add processed project
    * classes and raw programs
    * add job for each raw program
    
  * process_program
    * client pull a raw program job
    * process it
    * add processed program and raw run
    * add a job for each raw run
    
  * process_run
    * client pull a raw run job
    * process it
    * add procesed run 
