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
                'reporter': self.person,
            }
            task = Task(**pargs)
            task.put()
            project.task_cntr += 1
            project.save()
            self.redirect('/%s-%s/' % (project.code, task.task_eid))
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
        self.response.out.write('lol')
        
    def post(self):
        self.response.out.write('lol')


class TaskHandler(BaseHandler):
    def get(self, project_code, task_id):
        self.render('project', tvals)
        
    def post(self, project_code):
        self.redirect('/%s/' % project.code)


class MainHandler(BaseHandler):
    def get(self):
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
        self.render('dev', tvals)


app = webapp2.WSGIApplication([
    ('/', MainHandler),  # current tasks, what's up in projects if you're a leader
    ('/([A-Za-z]{2}[A-Za-z]+)/', ProjectHandler),  # project stats, create task
    ('/([A-Za-z]{2}[A-Za-z]+)/edit/', ProjectEditHandler),  # edit project
    ('/([A-Za-z]{2}[A-Za-z]+)\-([0-9]+)/', TaskHandler),  # task, comments, todolist, edit
    ('/p/([A-Za-z0-9]+)/', PersonHandler),  # person stats, tasks
    ('/p/edit/', PersonEditHandler), # edit personal profile, also register for first visit
    ('/f/', FilterHandler), # universal filter with ?lol=123&...
    ('/_ajax/', AjaxHandler), # ajax actions ?lol=123&...
    
], debug=True)
