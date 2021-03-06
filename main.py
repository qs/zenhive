import webapp2
import jinja2
import os
from cgi import escape
from datetime import datetime
import json
from google.appengine.api import users
from models import *
from config import *


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        user = users.get_current_user()
        self.person = Person.get_or_insert(user.email(), user=user, name=user.nickname())

    def render(self, tpl_file, tvals={}):
        tvals['person'] = self.person
        tvals['logout'] = users.create_logout_url("/")
        tpl = jinja_environment.get_template('templates/' + tpl_file + '.html')
        self.response.out.write(tpl.render(tvals))

    def write_json(self, data):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(data))

    def get_tag(self, t):
        t = escape(t).lower()
        tag = Tag.gql("WHERE name = :1", t).get()
        return tag
    
    def get_project(self, project_code):
        project_code = escape(project_code)
        project = Project.gql("WHERE code = :1", project_code).get()
        return project

    def get_person(self, name):
        name = escape(name)
        person = Person.gql("WHERE name = :1", name).get()
        return person

    def get_task(self, task_eid, project_code):
        task_eid = int(escape(task_eid))
        project = self.get_project(project_code)
        task = Task.gql("WHERE task_eid = :1 AND project = :2", task_eid, project.key()).get()
        return task

    def update_tags(self, tags, obj):
        st = set()
        for t in tags:
            tag = self.get_tag(t)
            if tag:
                st.add(tag.key())
            else:
                t = escape(t).lower()
                tag = Tag(name=t)
                tag.save()
                st.add(tag.key())
        obj.tags = list(st)
        obj.save()



class ProjectHandler(BaseHandler):
    def get(self, project_code):
        project = self.get_project(project_code)
        tvals = {'project': project}
        self.render('project', tvals)
        
    def post(self, project_code):
        if self.request.get('sm-newtask'):
            project = self.get_project(project_code)
            pargs = {
                'project': self.get_project(project_code),
                'task_eid': project.task_cntr,
                'title': escape(self.request.get('title')),
                'content': escape(self.request.get('content')),
                'reporter': self.person,
            }
            task = Task(**pargs)
            task.update_meta()
            task.put()
            project.task_cntr += 1
            project.save()
            self.redirect('/%s-%s/' % (project.code, task.task_eid))
        else:
        	self.redirect('/%s/' % project.code)


class ProjectEditHandler(BaseHandler):
    def get(self, project_code):
        project = self.get_project(project_code)
        tvals = {'project': project}
        self.render('project-edit', tvals)
        
    def post(self, project_code):
        if self.request.get('sm-project-edit'):
            project = self.get_project(project_code)
            # update project stats
        self.redirect('/%s/' % project.code)


class PersonHandler(BaseHandler):
    def get(self, person_name):
        person = self.get_person(person_name)
        tvals = {'person': person}
        self.render('person', tvals)
        

class PersonEditHandler(BaseHandler):
    def get(self):
        self.render('person-edit')
        
    def post(self):
        if self.request.get('sm-person-edit'):
            # self.person
            # update person stats
            pass
        self.redirect('/p/%s/' % self.person.name)


class FilterHandler(BaseHandler):
    def get(self):
        if self.request.arguments():
            self.response.out.write(self.request.arguments())
            self.response.out.write('<br />')
            for i in self.request.arguments():
                self.response.out.write(self.request.get(i))
                self.response.out.write('<br />')
        #self.render('results', tvals)


class AjaxHandler(BaseHandler):
    def get(self):
        if self.request.get('action') == 'get_persons': 
            persons = [p.name for p in Person.all() if p.name.find(self.request.get('q')) > -1]
            self.write_json({'availableTags': persons})
        elif self.request.get('action') == 'get_tags':
            tags = [t.name for t in Tag.all() if t.name.find(self.request.get('q')) > -1]
            self.write_json({'availableTags': tags})
    def post(self):
        if self.request.get('action') == 'set_persons' and self.request.get('project'):
            # project members
            project = self.get_project(self.request.get('project'))
            st = set([self.get_person(p).key() for p in self.request.get_all('tags[]')])
            project.members = list(st)
            project.save()
        elif self.request.get('action') == 'set_persons' and self.request.get('task'):
            # task cc
            project_code, task_eid = self.request.get('task').split('-')
            task = self.get_task(task_eid, project_code)
            st = set([self.get_person(p).key() for p in self.request.get_all('tags[]')])
            task.cc_persons = list(st)
            task.save()
        elif self.request.get('action') == 'set_tags' and self.request.get('project'):
            # project tags
            project = self.get_project(self.request.get('project'))
            self.update_tags(self.request.get_all('tags[]'), project)
        elif self.request.get('action') == 'set_tags' and self.request.get('task'):
            # task tags
            project_code, task_eid = self.request.get('task').split('-')
            task = self.get_task(task_eid, project_code)
            self.update_tags(self.request.get_all('tags[]'), task)

class TaskHandler(BaseHandler):
    def get(self, project_code, task_eid):
        task = self.get_task(task_eid, project_code)
        tvals = {'task': task}
        self.render('task', tvals)
        
    def post(self, project_code):
        self.redirect('/%s/' % project.code)


class MainHandler(BaseHandler):
    def get(self):
        #tvals = {'projects': self.person.get_membered(), }
        self.render('main')

    def post(self):
        if self.request.get('sm-project-new'):  # new project
            get_agrs = ['title', 'code', 'mission', 'content']
            pargs = {}
            for arg in get_agrs:
                pargs[arg] = escape(self.request.get(arg))
            pargs['leader'] = self.person
            project = Project(**pargs)
            if project.is_valid():
                project.put()
                self.redirect('/%s/' % project.code)
        else:
            self.redirect('/')


class DevHandler(BaseHandler):
    def get(self):
        p = self.get_person('g43wevg4')
        self.response.out.write(p)
        self.response.out.write(p.key())
        '''
        pargs = {
            'code': 'LOL',
            'title': 'The title',
            'leader': self.person,
            'mission': 'to be',
        }
        project = Project(**pargs)
        project.put()
        
        for i in range(5):
            pargs = {
                'project': project,
                'reporter': self.person,
                'title': 'Task first wave # %s' % i,
            }
            task = Task(**pargs)
            task.put()
        
        for i in range(3):
            pargs = {
                'project': project,
                'reporter': self.person,
                'title': 'Task second wave # %s' % i,
                'mention_tasks': [task.key(),],
            }
            stask = Task(**pargs)
            stask.put()
            
        tvals = {'project': project}
        self.render('dev', tvals)'''


app = webapp2.WSGIApplication([
    ('/', MainHandler),  # current tasks, what's up in projects if you're a leader
    ('/([A-Za-z]{2}[A-Za-z]+)/', ProjectHandler),  # project stats, create task
    ('/([A-Za-z]{2}[A-Za-z]+)/edit/', ProjectEditHandler),  # edit project
    ('/([A-Za-z]{2}[A-Za-z]+)\-([0-9]+)/', TaskHandler),  # task, comments, todolist, edit
    ('/p/([A-Za-z0-9]+)/', PersonHandler),  # person stats, tasks
    ('/p/edit/', PersonEditHandler), # edit personal profile, also register for first visit
    ('/f/', FilterHandler), # universal filter with ?lol=123&...
    ('/_ajax/', AjaxHandler), # ajax actions ?lol=123&...
    ('/_dev/', DevHandler), # ajax actions ?lol=123&...
    
], debug=True)
