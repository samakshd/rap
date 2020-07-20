#!/usr/bin/python3

#import sys
import os
import csv
import string
import functools

PANEL_SIZE = 4
##################################################################################
def read_contents(fileName):
  if(not os.path.isfile(fileName)):
    print(fileName + ": file does not exist.")
    raise FileNotExistsError(fileName)
  ifile  = open(fileName, "r")
  csvContents = csv.reader(ifile)
  trimmedContents = []
  for row in csvContents:
    trimmedRow = [cell for cell in row if cell is not ""]
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
This procedure computes the review panels from the given faculty application mapping.
'''
def calculate_review_panels(fac_apps):
  def second(t):
    _, b = t
    return b

  faculty_score, application_score, topic_score = calculate_scores(all_fac_apps)
  review_panels = {}
  for app in application_score:
    app_fac_list = []
    for fac in faculty_score:
      for f, a, ts in fac_apps:
        if f == fac and a == app:
          topic_weight = sum([1.0 / topic_score[t] for t in ts])
          match_score = topic_weight / faculty_score[fac]
          app_fac_list.append((fac, match_score))

    app_fac_list.sort(key=second, reverse=True)
    review_panels[app] = app_fac_list
  return review_panels
##################################################################################

##################################################################################
'''
Given the review panels, this procedure calculates the load on each faculty member.
'''
def calculate_faculty_load(review_panels):
  def first(t):
    a, _ = t
    return a

  faculty_score, application_score, topic_score = calculate_scores(all_fac_apps)
  faculty_load = {}
  for fac in faculty_score:
    faculty_load[fac] = []
    for app in review_panels:
      panel = map(first, (review_panels[app])[:PANEL_SIZE])
      if fac in panel:
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
  fout = open("data/output/faculty-application" + fname + ".csv", "w")
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
  fout = open("data/output/referrals/review-panels.txt", "w")
  for app in review_panels:
    fout.write("\n***************************************************")
    fout.write("\n" + app)
    panel = functools.reduce(lambda x, y: x + "\n\t" + y[0], review_panels[app][:PANEL_SIZE], "\n")
    fout.write(panel)
    fout.write("\n***************************************************")
  fout.close()
##################################################################################


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
  faculty_topics = get_faculty_topics(read_contents("data/topics.csv"))
  application_topics = get_application_topics(read_contents("data/research-applications-may-2019.csv"))
   
  all_fac_apps = []
  for f in faculty_topics:
    fac_apps = get_faculty_applications(f, faculty_topics, application_topics)
    all_fac_apps.extend(fac_apps)
  review_panels = calculate_review_panels(all_fac_apps)
  faculty_load = calculate_faculty_load(review_panels)
  print_review_panels_to_file(review_panels)
  for fac in faculty_load:
    print_referral_to_file(fac, faculty_load[fac])
##################################################################################
