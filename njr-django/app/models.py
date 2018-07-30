# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django_mysql.models import NullBit1BooleanField


class Class(models.Model):
    class_id = models.AutoField(primary_key=True)
    processed_project = models.ForeignKey('ProcessedProject', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    is_mainclass = NullBit1BooleanField(blank=True, null=True)  # This field type is a guess.
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'class'


class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    complete = NullBit1BooleanField(blank=True, null=True)  # This field type is a guess.
    error = NullBit1BooleanField(blank=True, null=True)  # This field type is a guess.
    visited = models.DateTimeField(blank=True, null=True)
    buildid = models.CharField(max_length=255, blank=True, null=True)
    timing = models.DecimalField(max_digits=32, decimal_places=16, blank=True, null=True)
    script = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'job'


class ProcessedProgram(models.Model):
    processed_program_id = models.AutoField(primary_key=True)
    raw_program = models.ForeignKey('RawProgram', models.DO_NOTHING, blank=True, null=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'processed_program'


class ProcessedProject(models.Model):
    processed_project_id = models.AutoField(primary_key=True)
    raw_project = models.ForeignKey('RawProject', models.DO_NOTHING, blank=True, null=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=True, null=True)
    sha256 = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    buildwith = models.CharField(max_length=255, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'processed_project'


class ProcessedRepo(models.Model):
    processed_repo_id = models.AutoField(primary_key=True)
    raw_repo = models.ForeignKey('RawRepo', models.DO_NOTHING, blank=True, null=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=True, null=True)
    sha256 = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'processed_repo'


class ProcessedRun(models.Model):
    processed_run_id = models.AutoField(primary_key=True)
    raw_run = models.ForeignKey('RawRun', models.DO_NOTHING, blank=True, null=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    analysis = models.CharField(max_length=255, blank=True, null=True)
    world = models.IntegerField(blank=True, null=True)
    upper = models.IntegerField(blank=True, null=True)
    path = models.TextField(blank=True, null=True)
    lower = models.IntegerField(blank=True, null=True)
    difference = models.IntegerField(blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'processed_run'


class RawProgram(models.Model):
    raw_program_id = models.AutoField(primary_key=True)
    mainclass = models.ForeignKey(Class, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_program'


class RawProject(models.Model):
    raw_project_id = models.AutoField(primary_key=True)
    processed_repo = models.ForeignKey(ProcessedRepo, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=245, blank=True, null=True)
    subfolder = models.CharField(max_length=255, blank=True, null=True)
    javaversion = models.CharField(max_length=255, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_project'


class RawRepo(models.Model):
    raw_repo_id = models.AutoField(primary_key=True)
    field_cls = models.CharField(db_column='_cls', max_length=255, blank=True, null=True)  # Field renamed because it started with '_'.
    name = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    rev = models.CharField(max_length=255, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_repo'


class RawRun(models.Model):
    raw_run_id = models.AutoField(primary_key=True)
    processed_program = models.ForeignKey(ProcessedProgram, models.DO_NOTHING, blank=True, null=True)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    args = models.CharField(max_length=255, blank=True, null=True)
    stdin = models.CharField(max_length=255, blank=True, null=True)
    mongo_id = models.CharField(max_length=45, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_run'
