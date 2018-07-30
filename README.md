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
/njr-django/app/views.py
/njr-django/njr/import_mongo_v2.py

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
nix-copy-closure isn't working
