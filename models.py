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
        return Projects.gql("WHERE members IN :1 OR leader = :2 ORDER BY title", self.key(), self)

    def get_reported(self):
        return Task.gql("WHERE reporter IN :1 ORDER BY dt DESC", self.key())

    def get_assigned(self):
        return Task.gql("WHERE assigner IN :1 ORDER BY dt DESC", self.key())

    
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
        
    def save_task(self):
        mens = re.findall(ur'[A-Z]+\-([0-9]+)', self.content)
        tasks = Task.get(db.Key.from_path('Task', [int(i) for i in mens]))
        
        
class Tag(db.Model):
    name = db.StringProperty(required=True)
    content = db.TextProperty()
