#!/usr/bin/python3

#import sys
import os
import csv
import string
import functools
import min_cost_max_flow as MinCostMaxFlow

PANEL_SIZE = 3
MAX_PANELS_PER_FACULTY = 150
##################################################################################
def read_contents(fileName):
  if(not os.path.isfile(fileName)):
    print(fileName + ": file does not exist.")
    raise FileNotFoundError(fileName)
  ifile  = open(fileName, "r")
  csvContents = csv.reader(ifile)
  trimmedContents = []
  for row in csvContents:
    trimmedRow = [cell for cell in row if cell != ""]
    if(len(trimmedRow) != 0):
      trimmedContents.append(trimmedRow)
    else:
      trimmedContents.append(None)
  return trimmedContents
##################################################################################

##################################################################################
def print_container(l):
  for e in l:
    print(e)
##################################################################################

##################################################################################
'''
Inputs:
  contents: CSV table containing faculty data.
    column 0     - faculty name
    column 1 ... - Topics

  This procedure transforms the given CSV table into a dictionary.
  key  : faculty name
  value: set of topics
'''


def get_faculty_topics(contents):
  faculty = set(row[0] for row in contents)
  faculty_topics = {}
  for f in faculty:
    ftopics = set([row[1].lower()for row in contents if row[0] == f])
    faculty_topics[f] = ftopics
  return faculty_topics
##################################################################################

##################################################################################
'''
Inputs:
  contents: CSV table containing application data.
    column 0     - applicant name
    column 1     - email id
    column 2 ... - Topics

  This procedure transforms the given CSV table into a dictionary.
  key  : application (email id)
  value: set of topics
'''
def get_application_topics(contents):
  applications = [row[1] for row in contents]

  all_app_topics = [[t for t in row[1:] if not '@' in t] for row in contents] # hack to remove email ID in topic lists (unknown reason)
  application_topics = {}
  for i in range(len(applications)):
    app = applications[i]
    app_topics = all_app_topics[i]
    if not app in application_topics:
      application_topics[app] = set()
    for t in app_topics:
      application_topics[app].add(t.lower())
  return application_topics
##################################################################################

##################################################################################
'''
This procedure computes the list of applications against a faculty member fac.
Inputs:
  fac: Faculty member
  ft : Faculty to topic map
  at : Application to topic map
'''
def get_faculty_applications(fac, ft, at):
  def my_lambda(fao):
    f, a, o = fao
    return len(o)

  fac_app = []
  for app in at:
    overlap = ft[fac].intersection(at[app])
    if(len(overlap) != 0):
      fac_app.append((fac, app, overlap))
  fac_app.sort(key = my_lambda, reverse = True)
  return fac_app
##################################################################################

##################################################################################
'''
This procedure computes the scores of faculty members, applications and topics 
based on the number of times they appear in match entries.
'''
def calculate_scores(fac_apps):
  faculty = set([f for f, a, t in fac_apps])
  applications = set([a for _, a, _ in fac_apps])
  topics = set()
  for _, _, ts in fac_apps:
    topics = topics.union(ts)
  faculty_score = {}
  application_score = {}
  topic_score = {}

  for f, a, ts in fac_apps:
    if not f in faculty_score:
      faculty_score[f] = 0
    faculty_score[f] += 1
    if not a in application_score:
      application_score[a] = 0
    application_score[a] += 1
    for t in ts:
      if not t in topic_score:
        topic_score[t] = 0
      topic_score[t] += 1
  return faculty_score, application_score, topic_score
##################################################################################

##################################################################################

'''
Calculates the Mapping of match scores to corresponding faculty-canditate pair

(faculty, application) ---> Match Score

'''

def get_scores_map(fac_apps,faculty_score, application_score, topic_score):

  score_map = {}
  for fac,app,topic_list in fac_apps:
# common topic score + Rare topic will get more importance
      topic_weight = sum([1/topic_score[t] for t in topic_list])
# Rare faculty will get more importance       
      match_score = topic_weight/(faculty_score[fac]*application_score[app])
      score_map[(fac,app)] = match_score

  return score_map

##################################################################################

##################################################################################

'''
This procedure computes the review panels from the given faculty application mapping.
'''
def calculate_review_panels(fac_apps):

  faculty_score, application_score, topic_score = calculate_scores(fac_apps)

  index = 1
  
  faculty_list = []
  fac_to_index = {}
  for fac in faculty_score:
    faculty_list.append(fac)
    fac_to_index[fac] = index
    index+=1

  fac_size = len(faculty_list)

  application_list = []
  app_to_index = {}
  for app in application_score:
    application_list.append(app)
    app_to_index[app] = index
    index+=1

  app_size = len(application_list)

  num_of_nodes = fac_size + app_size + 2

  source = 0
  sink = num_of_nodes -1

  start_nodes = [0]*fac_size
  end_nodes = [fac_to_index[fac] for fac in fac_to_index]
  capacities = [MAX_PANELS_PER_FACULTY]*fac_size
  costs = [0]*fac_size

  score_map = get_scores_map(fac_apps,faculty_score, application_score, topic_score)

  for (fac,app) in score_map:

    match_score = score_map[(fac,app)]
    start_nodes.append(fac_to_index[fac])
    end_nodes.append(app_to_index[app])
    capacities.append(1)
    costs.append(1-match_score)

  start_nodes += [app_to_index[app] for app in app_to_index]
  end_nodes += [sink]*app_size
  capacities += [PANEL_SIZE]*app_size
  costs += [0]*app_size

  edges = []
  # Add each arc.
  for i in range(len(start_nodes)):
    edge = (start_nodes[i],end_nodes[i],capacities[i],costs[i])
    edges.append(edge)

  FlowNetwork,TotalCost = MinCostMaxFlow.SolveMinCostMaxFlow(num_of_nodes,edges,source,sink)

  review_panels = {}

  for fac in fac_to_index:
    for app in app_to_index:

      NetFlow = FlowNetwork[fac_to_index[fac]][app_to_index[app]] - FlowNetwork[app_to_index[app]][fac_to_index[fac]]
      if(NetFlow == 1):
        if(app not in review_panels):
          review_panels[app] = []

        review_panels[app].append((fac,score_map[(fac,app)]))


  return review_panels


##################################################################################

##################################################################################
'''
Given the review panels, this procedure calculates the load on each faculty member.
'''
def calculate_faculty_load(review_panels):

  faculty_load = {}

  for app in review_panels:
    for (fac,score) in review_panels[app]:
      if(fac not in faculty_load):
        faculty_load[fac] = []
      faculty_load[fac].append(app)

  return faculty_load
##################################################################################

##################################################################################
def string_of_list(lst):
  return functools.reduce(lambda x, y: x + ", " + y, lst, "")
##################################################################################

##################################################################################
def string_of_fac_apps(fac_apps):
  ao = [a +  " " + string_of_list(o) for _, a, o in fac_apps]
  return functools.reduce(lambda x, y: x + "\n" + y, ao, "")
##################################################################################

##################################################################################
'''
Procedure to print the applications for a given faculty into its corresponding file.
Input:
  f : faculty name
  fac_app : Applications corresponding to the faculty member.
'''

def print_fac_app_to_file(f, fac_app):
  fname = f.replace(" ", "_")
  fout = open("data/output/faculty-application/" + fname + ".csv", "w")
  fout.write(string_of_fac_apps(fac_apps))
  fout.close()
##################################################################################

##################################################################################
def print_referral_to_file(f, apps):
  fname = f.replace(" ", "_")
  fout = open("data/output/referrals/" + fname + ".txt", "w")
  fout.write(functools.reduce(lambda x, y: x + "\n" + y, apps, ""))
  fout.close()
##################################################################################

##################################################################################
def print_review_panels_to_file(review_panels):
  fout = open("data/output/panel/review-panels.txt", "w")
  count=0
  for app in review_panels:
    fout.write("\n***************************************************")
    count+=1
    fout.write("\nInterview-panel : "+str(count))
    fout.write("\n" + app)
    panel = functools.reduce(lambda x, y: x + "\n\t" + y[0], review_panels[app][:PANEL_SIZE], "\n")
    fout.write(panel)
    fout.write("\n***************************************************")
  fout.close()
##################################################################################

##################################################################################
def create_review_panels_to_file(review_panels):
  fout = open("data/output/panel/review-panels.csv", "w")
  count=0
  for app in review_panels:
    count+=1
    fout.write(str(app)+",")
    panel = functools.reduce(lambda x, y: x + y[0] + ",",review_panels[app],"")

    k=str(panel)
    fout.write(k[:-1])
    fout.write("\n")
  fout.close()


def create_manual_review_panels_to_file(manual_review_panels):
  data = []
  for app in manual_review_panels:
    row = []
    row.append(app)
    for fac in manual_review_panels[app]:
      row.append(fac)
    data.append(row)

  with open("data/output/panel/manual-review-panels.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(data)

##################################################################################

def get_manual_review_panels(contents,application_list):
  apps_init = [row[0] for row in contents]
  facs_init = [row[1] for row in contents]
  apps = []
  facs = []


  
  for i in range(len(apps_init)):
    if(apps_init[i] in application_list):
      apps.append(apps_init[i])
      facs.append(facs_init[i])
  

  manual_review_panels = {}
  for i in range(len(apps)):
    if(apps[i] not in manual_review_panels):
      manual_review_panels[apps[i]] = []
    manual_review_panels[apps[i]].append(facs[i])
  
  return manual_review_panels

##################################################################################
def get_candidate_relevance_index(review_panels):

  candidate_relevance_index = {}
  for app in review_panels:
    relevance_scores = sum(score for (fac,score) in review_panels[app])
    panel_size = len(review_panels[app])
    candidate_relevance_index[app] = relevance_scores/panel_size

  return candidate_relevance_index

##################################################################################

def get_total_match_score(review_panels):

  total_score = 0
  for app in review_panels:
    for (fac,score) in review_panels[app]:
      total_score += score

  return total_score

def get_total_manual_match_score(fac_apps,review_panels):

  faculty_score, application_score, topic_score = calculate_scores(fac_apps)
  scores_map = get_scores_map(fac_apps,faculty_score, application_score, topic_score)


  total_score = 0
  for app in review_panels:
    for fac in review_panels[app]:
      if((fac,app) in scores_map):
        total_score += scores_map[(fac,app)]

  return total_score


##################################################################################

def get_faculty_relevance_index(fac_apps,faculty_load):

  faculty_score, application_score, topic_score = calculate_scores(fac_apps)
  scores_map = get_scores_map(fac_apps,faculty_score, application_score, topic_score)

  faculty_relevance_index = {}

  for fac in faculty_load:
    relevance_scores = sum(scores_map[(fac,app)] for app in faculty_load[fac])
    num_of_applicants = len(faculty_load[fac])
    faculty_relevance_index[fac] = relevance_scores/num_of_applicants

  return faculty_relevance_index

'''
SOME NOTES (29 June 2019)
-------------------------
We have already extracted the matches from the application files. The output of this
process is a list of triples:
- Faculty
- Application ID
- Common topics

From the survey, we have a similar of triples. However, there the applications are
identified by email IDs. We need to replace the email IDs by application numbers here.

We can do this by mapping the email IDs to application numbers. How?
- First get all the email IDs.
- Search for each email ID in the application files. Create a map: application ID -> email ID.
- Invert this map: email ID -> application ID
- Use this map to replace email IDs with application IDs in the above list of triples.

Once both the lists of triples are in terms of the application IDs, we merge them.
That is, for every matching faculty and application ID, we merge (i.e. union) their topic sets.
This will give us the final list of triples (faculty, application ID, common topics).

Computing Interview Panels
--------------------------
We filter the above list to have only short listed applications.
We use the same algorithm as used to compute review panels to also calculate interview
panels.
 
'''
##################################################################################
if __name__ == "__main__":
  faculty_topics = get_faculty_topics(read_contents("data/input/faculty-topics-21.csv"))
  application_topics = get_application_topics(read_contents("data/input/research-applications-21.csv"))


  all_fac_apps = []
  for f in faculty_topics:
    fac_apps = get_faculty_applications(f, faculty_topics, application_topics)
    print_fac_app_to_file(f, fac_apps)
    all_fac_apps.extend(fac_apps)

  review_panels = calculate_review_panels(all_fac_apps)
  faculty_load = calculate_faculty_load(review_panels)
  print_review_panels_to_file(review_panels)
  create_review_panels_to_file(review_panels)
  for fac in faculty_load:
    print_referral_to_file(fac, faculty_load[fac])

  manual_review_panels = get_manual_review_panels(read_contents("data/input/manualData.csv"),application_topics)
  create_manual_review_panels_to_file(manual_review_panels)

  print(get_total_manual_match_score(all_fac_apps,manual_review_panels))
  print(get_total_match_score(review_panels))

  candidate_relevance_index = get_candidate_relevance_index(review_panels)
  faculty_relevance_index = get_faculty_relevance_index(all_fac_apps,faculty_load)

##################################################################################
