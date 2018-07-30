#!/bin/bash

#get rid of existing jobs
curl 10.0.2.2:8000/delete_dummy_jobs

#make 10 dummy jobs that print a random string
curl 10.0.2.2:8000/make_dummy_jobs

#loop until all jobs are complete
while true
do

    #get a job
    JSON="$(curl 10.0.2.2:8000/job)"

    #parse the json to see if a job was retrieved
    MSG="$(echo "${JSON}" | jq -r '.message')"
    if [ "$MSG" = "empty" ]; then
        break
    fi

    JOB_ID="$(echo "${JSON}" | jq -r '.job_id')"
    DRV="$(echo "${JSON}" | jq -r '.drv')"

    #put nix script in file
    echo "${DRV}" > default.nix

    #instantiate and realise
    nix-instantiate --add-root /vagrant_data/instantiate --indirect default.nix
    nix-store --realise /vagrant_data/instantiate --add-root /vagrant_data/realise --indirect --substituters ssh://vagrant@127.0.0.1:2222

    #mark job as complete
    curl -d '{"job_id":"'"$JOB_ID"'", "on_machine":"2200", "result_folder":"../vagrant_client/vagrant_shared/realise"}' -H "Content-Type: application/json" -X POST 10.0.2.2:8000/job

done