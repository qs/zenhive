from google.appengine.ext import db
import re
from datetime import date, timedelta
from config import *



class Person(db.Model):
    user = db.UserProperty(required=True)
    name = db.StringProperty(required=True)
    dt = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Key)

    def get_tags(self):
        return Tag.gql("WHERE __key__ IN :1 ORDER BY name", self.tags)

    def get_membered(self):
        return Project.gql("WHERE members = :1 ORDER BY title", self.key())

    def get_lead(self):
        return Project.gql("WHERE leader = :1 ORDER BY title", self)

    def get_reported(self):
        return Task.gql("WHERE reporter = :1 AND finish_dt = NULL ORDER BY dt DESC", self.key())

    def get_assigned(self):
        return Task.gql("WHERE assigner = :1 AND finish_dt = NULL ORDER BY dt DESC", self.key())

    
class Project(db.Model):
    title = db.StringProperty(required=True)
    code = db.StringProperty(required=True)
    dt = db.DateTimeProperty(auto_now_add=True)
    leader = db.ReferenceProperty(Person, required=True, collection_name='leader')
    mission = db.StringProperty(required=True)
    task_cntr = db.IntegerProperty(default=1)
    default_due_dt = db.IntegerProperty(default=7)
    default_assigner = db.ReferenceProperty(Person, collection_name='def_ass')
    content = db.TextProperty()
    members = db.ListProperty(db.Key)
    tags = db.ListProperty(db.Key)

    def is_valid(self):
        self.code = self.code.upper()
        if not re.match(r'^[A-Z]+$', self.code):
            raise Exception('Project code must be ^[A-Z]+$')
        entity = Project.all(keys_only=True).filter('code', self.code).get()
        if entity:
            raise Exception('Project code must be unique')
        return True
    
    @property
    def tasks(self):
        return Task.gql("WHERE project = :1", self)

    def get_members(self):
        return Person.gql("WHERE __key__ IN :1 ORDER BY name", self.members)

    def get_tags(self):
        return Tag.gql("WHERE __key__ IN :1 ORDER BY name", self.tags)

    def get_unassigned(self):
        return Task.gql("WHERE project = :1 AND assigner = NULL", self)

    def get_overdue(self, due_delay=3):
        dt = date.today() + timedelta(days=due_delay)
        return Task.gql("WHERE project = :1 AND due_dt < :2 AND finish_dt != NULL", self, dt)

    
class Task(db.Model):
    task_eid = db.IntegerProperty(required=True)
    project = db.ReferenceProperty(Project, required=True)
    reporter = db.ReferenceProperty(Person, required=True, collection_name='reporter')
    assigner = db.ReferenceProperty(Person, collection_name='assigner')
    title = db.StringProperty(required=True)
    content = db.TextProperty()
    dt = db.DateTimeProperty(auto_now_add=True)
    due_dt = db.DateTimeProperty()
    finish_dt = db.DateTimeProperty()
    mention_tasks = db.ListProperty(db.Key)
    cc_persons = db.ListProperty(db.Key)
    tags = db.ListProperty(db.Key)

    def get_tags(self):
        return Tag.gql("WHERE __key__ IN :1 ORDER BY name", self.tags)
        
    def get_comments(self):
        return Comment.gql("WHERE task = :1 ORDER BY dt", self)

    def get_cc_persons(self):
        return Person.gql("WHERE __key__ IN :1", self.cc_persons)

    def get_mentions(self):
        return Task.gql("WHERE __key__ IN :1", self.mention_tasks)

    def get_mentioned(self):
        return Task.gql("WHERE mention_tasks = :1", self)
        
    def update_meta(self):
        mens = re.findall(ur'([A-Z]+)\-([0-9]+)', self.content)
        for pcode, eid in mens:
            project = Project.gql("WHERE code = :1", pcode)
            task_id = db.GqlQuery("""SELECT __key__ FROM Task 
                    WHERE task_eid = :task_eid
                    AND project = :project""", task_eid=eid, project=project).get()
            if task_id not in self.mention_tasks:
                self.mention_tasks.append(task_id)
        
        
        
class Tag(db.Model):
    name = db.StringProperty(required=True)
    content = db.TextProperty()
