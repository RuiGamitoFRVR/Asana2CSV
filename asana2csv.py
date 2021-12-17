import asana
import csv
import argparse

outputdir = ''
outputfilename = 'asana-export.csv'

parser = argparse.ArgumentParser(description='Export Asana tasks to CSV format.')
parser.add_argument('--project', default=None, type=str, help="The project to retrieve tasks from. Omit for all projects")
parser.add_argument('--onlyopen', action="store_true", help="Fecth only open tasks. Omit for all tasks")
parser.add_argument('--onlycomplete', action="store_true", help="Fecth only complete tasks. Omit for all tasks")

parser.add_argument('access_token', type=str)

args = parser.parse_args()

personal_access_token = args.access_token

client = asana.Client.access_token(personal_access_token) #start session
me = client.users.me() #get user info
workspace = me['workspaces'][0] #set main workspace
print('Initialising Asana session for ' + me['name'] + ' in workspace: ' + workspace['name'])
 #find projects within workspace
tasklist = []

def getProjectTasks(project, onlyopen, onlycomplete):
    offset = None
    tasklist = []

    while True:
        tasks = client.tasks.find_by_project(project['gid'], {"opt_expand":"name, \
            gid, resource_type, resource_subtype, assignee, assignee_status, created_at, completed, \
            completed_at, custom_fields, dependencies, dependents, due_on, \
            followers, liked, likes, memberships, modified_at, \
            notes, html_notes, num_likes, num_subtasks, parent, projects, start_on, workspace, tags"}, iterator_type="items", offset=offset)

            # "opt_expand":"name, \
            # projects, workspace, gid, due_on, created_at, modified_at, completed, \
            # completed_at, assignee, parent, notes, tags"
        

        for task in tasks:
            if onlyopen and task['completed'] == onlyopen: #build list of only open tasks
                continue
            if onlycomplete and task['completed'] != onlycomplete: #build list of only open tasks
                continue
            
            #Truncate notes if needed
            #if len(task['notes']) > 80:
                #task['notes'] = task['notes'][:79]

            #Loop through tags applied to each task, extract from json and turn into comma separated string
            tags = task['tags']         
            if task['tags'] is not None:
                tagname=''
                i=0
                for tag in tags:
                    if i==0:
                        tagname = tag['name']
                    else:
                        tagname = tagname + ', ' + tag['name']
                    i=i+1
            
            #deal with assignee being blank
            assignee = task['assignee']['name'] if task['assignee'] is not None else ''

            #cleaning up the dates so they're readable
            created_at = task['created_at'][0:10] + ' ' + task['created_at'][11:16] if \
                    task['created_at'] is not None else None
            modified_at = task['modified_at'][0:10] + ' ' + task['modified_at'][11:16] if \
                    task['modified_at'] is not None else None
            completed_at = task['completed_at'][0:10] + ' ' + task['completed_at'][11:16] if \
                task['completed_at'] is not None else None
            #build row
            row = [task['name'], task['gid'], project['name'], task['resource_type'], task['resource_subtype'], assignee, task['assignee_status'], created_at, 
                   task['completed'], completed_at, task['custom_fields'], task['dependencies'], task['dependents'], task['due_on'], task['followers'], task['liked'], 
                   task['likes'], task['memberships'], modified_at, task['notes'], task['html_notes'], task['num_likes'], task['num_subtasks'], task['parent'],
                   task['projects'], task['start_on'], task['workspace'], tagname]
            row = ['' if s is None else s for s in row]
            tasklist.append(row)
            
        if 'next_page' in tasks:
            offset = tasks['next_page']['offset']
        else:
            break

    print("Found %d tasks for project %s" % (len(tasklist), project['name']))
    return tasklist


# print('\nLooping through all the tasks within the projects...\n')

projects = client.projects.find_by_workspace(workspace['gid'], iterator_type=None)
if args.project is not None:
    found = False
    for project in projects:
        # print(">"+project['name']+"< >" + args.project + "<")
        if project['name'] == args.project:
            projects = [project]
            found = True
            break
        
    if not found:
        print("Project not found")
        projects = []
    

for project in projects:
    print("Processing tasks for project '%s'" % project['name'])
    tasklist = getProjectTasks(project, args.onlyopen, args.onlycomplete)

print('\nExporting to csv file: ' + outputdir + outputfilename + '...') 
csvheader = ['Task', 'Task ID', 'Project', 'Resource Type', 'Resource Subtype', 'Assignee', 'Assignee Status' , 'Created At', 'Completed', \
            'Completed At', 'Custom Fields', 'Dependencies', 'Dependents', 'Due On', \
            'Followers', 'Liked', 'Likes', 'Memberships', 'Modified At', \
            'Notes', 'HTML Notes', 'Num Likes', 'Num Subtasks', 'Parent', 'Projects', 'Start On', 'Workspace','Tags']
with open(outputdir + outputfilename, 'w', encoding='utf8') as csvfile:
    csvwriter = csv.writer(csvfile, lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(csvheader)
    for item in tasklist:
        csvwriter.writerow(item)

print('\nFinished!')
