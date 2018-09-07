# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

from django_mysql.models import NullBit1BooleanField

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Class(models.Model):
    class_id = models.AutoField(primary_key=True)
    processed_project = models.ForeignKey('ProcessedProject', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    is_mainclass = NullBit1BooleanField(blank=True, null=True)  # This field type is a guess.
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'class'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


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


class Method(models.Model):
    method_id = models.AutoField(primary_key=True)
    class_field = models.ForeignKey(Class, models.DO_NOTHING, db_column='class_id', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    name = models.TextField(blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'method'


class MethodAnalysisProperty1(models.Model):
    method_analysis_property1_id = models.AutoField(primary_key=True)
    method = models.ForeignKey(Method, models.DO_NOTHING, blank=True, null=True)
    result = models.IntegerField(blank=True, null=True)
    tool = models.ForeignKey('Tool', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'method_analysis_property1'


class MethodAnalysisProperty2(models.Model):
    method_analysis_property1_id = models.AutoField(primary_key=True)
    method = models.ForeignKey(Method, models.DO_NOTHING, blank=True, null=True)
    result = models.IntegerField(blank=True, null=True)
    tool = models.ForeignKey('Tool', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'method_analysis_property2'


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


class ReachableMethod(models.Model):
    reachable_methods_id = models.AutoField(primary_key=True)
    method = models.ForeignKey(Method, models.DO_NOTHING, blank=True, null=True)
    tool = models.ForeignKey('Tool', models.DO_NOTHING, blank=True, null=True)
    mainclass = models.ForeignKey(Class, models.DO_NOTHING, blank=True, null=True)
    uuid = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reachable_method'


class Tool(models.Model):
    tool_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tool'
