FROM python:3.6

ENV PYTHONUNBUFFERED 1

ARG PROJECT=njr
ARG PROJECT_DIR=/var/www/${PROJECT}

RUN mkdir -p $PROJECT_DIR
WORKDIR $PROJECT_DIR

RUN apt-get -y -f install default-libmysqlclient-dev

ADD requirements.txt $PROJECT_DIR
RUN pip install -r requirements.txt
ADD . $PROJECT_DIR
