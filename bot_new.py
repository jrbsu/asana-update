import asana
from asana.rest import ApiException
import pandas as pd
import re
from tabulate import tabulate
import pyinputplus as pyip
import sys

debug = False

try:
    if sys.argv[1] == "-d":
        debug = True
        print("Running in debug mode")
    else:
        print("Running in regular mode. Use `-d` for debug mode")
except:
    print("Running in regular mode. Use `-d` for debug mode")

# pip3 install asana==4.0.4
# pip3 install asana==3.2.1

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

project_id = "748177369902207"
base_url = "https://app.asana.com/0/748177369902207/"
base_profile_url = "https://app.asana.com/0/profile/"

configuration = asana.Configuration()
configuration.access_token = '1/133691726476243:8807d10bc974d545b852cd9dbf7668ec'
api_client = asana.ApiClient(configuration)

tasks_call = asana.TasksApi(api_client)
tasks_call_opts = ["name","assignee.name","completed","memberships.section.name"]
tasks_data = tasks_call.get_tasks_for_project(project_id, opt_fields=tasks_call_opts)
tasks_data = tasks_data.data

def delta(lw, tw):
    if lw == tw:
        return "±0"
    elif lw > tw:
        return "-" + str(lw - tw)
    elif tw > lw:
        return "+" + str(tw - lw)
    
def compare_comments(i, lw, tw):
    case_name = full_table.loc[i, 'case_name']
    if debug == True:
        print(f"Running in debug mode. Using existing comment for {case_name}")
        return f'<ul><li>{x["case_comment_x"]}</li></ul></ul>'
    else:
        total_cases = len(full_table.index)
        print(f'\nYou need to choose a comment for "{case_name}" (case {i + 1} of {total_cases})')
        table = [[lw, tw]]
        print(tabulate(table, headers=["1: Existing comment", "2: New comment"], tablefmt="grid", maxcolwidths=[70, 70]))
        comment_choice = pyip.inputInt(prompt="Which would you like to use? (enter '1' or '2', or '0' for a new comment) — ", greaterThan=-1, lessThan=3)
        if comment_choice == 1:
            print("Using existing comment")
            return f'<ul><li>{x["case_comment_x"]}</li></ul></ul>'
        elif comment_choice == 2:
            print("Using new comment")
            return f'<ul><li>{x["case_comment_y"]}</li></ul></ul>'
        elif comment_choice == 0:
            comment = input(f'Please provide a comment for the update: ')
            comment = f'<ul><li>{comment}</li></ul></ul>'
            return comment

def new_case_comment(i):
    case_name = full_table.loc[i, 'case_name']
    new_case_comment = input(f'\n"{case_name}" seems to be new. Please provide a comment for the update: ')
    return new_case_comment
    
        
def assignee(id):
    if id == "no assignment":
        return "no assignment"
    else:
        return f'<a data-asana-gid="{id}"/>'

def task_link(id):
    return f'<a data-asana-gid="{id}"/>'

def plural(number):
    if number == 1:
        return f'{number} case'
    else:
        return f'{number} cases'

# Get last week's update...
print("Getting last week's update ...")

updates_call = asana.StatusUpdatesApi(api_client)
updates_call_opts = ["status_type","text","title"]
updates_data = updates_call.get_statuses_for_object(project_id, opt_fields=updates_call_opts)
updates_data = updates_data.data

for c, x in enumerate(updates_data):
    if c == 0:
        update_text = x.text
        update_title = x.title
print(f"Using {update_title}")

f = open("pulled-update.txt", "w")
f.write(update_text)
print("Written update text to `pulled-update.txt`\n")
f.close()

print("Parsing update text in `pulled-update.txt` ...")
update_lines = []
lw_dict = {
    "total_cases": 0,
    "new_cases": 0,
    "completed_cases": 0,
    "with_tns": 0,
    "with_legal": 0,
    "stalled": 0
}
tw_dict = {
    "total_cases": 0,
    "new_cases": 0,
    "completed_cases": 0,
    "with_tns": 0,
    "with_legal": 0,
    "stalled": 0
}

with_legal_array = ["with Legal", "done, Legal to inform reporter", "with Legal (with Fellow)"]
stalled_array = ["stalled on community", "stalled on reporter", "monitoring for change", "with outside counsel", "with Legal (with Fellow)", "on hold"]

section_dict = {
    "unknown": 0,
    "with T&S": 1,
    "with Legal": 2,
    "done, Legal to inform reporter": 3,
    "stalled on community": 4,
    "stalled on reporter": 5,
    "monitoring for change": 6,
    "with outside counsel": 7,
    "with Legal (with Fellow)": 8,
    "on hold": 9,
    "nothing happening": 10
}

assignees_dict = {
    'nan': "no assignment",
    'Brian Choo': "1193273825956789",
    'Phil Bradley-Schmieg': "1202324842233437",
    'Kabir Darshan Singh Choudhary': "1200531633942360",
    'Rachel Stallman': "775259890833058",
    'Joe Sutherland': "133691726476247",
    'Aeryn Palmer': "775259890833039"
}

lw_df = pd.DataFrame({"case_id": [], "case_section": [], "case_comment": []})
tw_df = pd.DataFrame({"case_name": [], "case_section": [], "case_section_id": [], "case_comment": [], "case_assignee": [],"case_assignee_id": [], "case_id": []})

with open("pulled-update.txt", "r") as f:
    for line in f:
        line = re.sub(r'^[\t\s]+', '', line)
        update_lines.append(line)

for c, x in enumerate(update_lines):
    if re.search(r'^Total cases', x):
        p = re.compile("Total cases: (\d+) \(.\d+ on last update\)")
        lw_dict["total_cases"] = int(p.search(x).group(1))
    if re.search(r'^New:', x):
        p = re.compile("New: (\d+) cases? \(..+\)")
        lw_dict["new_cases"] = int(p.search(x).group(1))
    if re.search(r'^Completed:', x):
        p = re.compile("Completed: (\d+) cases? \(..+\)")
        lw_dict["completed_cases"] = int(p.search(x).group(1))
    if re.search(r'^With T&S:', x):
        p = re.compile("With T&S: (\d+) cases? \(..+\)")
        lw_dict["with_tns"] = int(p.search(x).group(1))
    if re.search(r'^With Legal:', x):
        p = re.compile("With Legal: (\d+) cases? \(..+\)")
        lw_dict["with_legal"] = int(p.search(x).group(1))
    if re.search(r'^Stalled:', x):
        p = re.compile("Stalled: (\d+) cases? \(..+\)")
        lw_dict["stalled"] = int(p.search(x).group(1))

    # Adding cases
    if re.search(r'^.*\(.*\-\s(http|no).*\)', x):
        p = re.compile(r"^(.*?)\s\((.*→\s)?(.*)\s\-\s(http|no).*\)$")
        case_url = p.search(x).group(1)
        case_id = re.sub(base_url, '', case_url)
        case_section = p.search(x).group(3)
        case_comment = update_lines[c + 1]
        case_comment = re.sub('\n','',case_comment) # This will hopefully prevent as many false "duplicates" showing up

        case_info = [case_id, case_section, case_comment]
        
        lw_df.loc[len(lw_df.index)] = case_info

print(f"Done. Found {len(lw_df.index)} cases.\n")

print("Gathering data from Asana API ...")

for c, x in enumerate(tasks_data):
    if x.completed == False and x.memberships[0].section.name != "non-case items": #i.e. this is an active task and not a non-case item
        tw_case_name = x.name
        # This next bit is a hack and I hate it
        tw_case_section = x.memberships[0].section.name
        if tw_case_section == "Legal cases":
            tw_case_section = x.memberships[1].section.name
        # end hack. This should loop or something instead.
        if re.search(r'with T&S', tw_case_section):
            tw_case_section = "with T&S"
        try:
            assignee_name = x.assignee.name
            assignee_gid = x.assignee.gid
        except:
            assignee_name = "no assignment"
            assignee_gid = 0
        tw_case_id = x.gid
        tw_case_section_id = section_dict[tw_case_section]
        tw_case_info = [tw_case_name, tw_case_section, tw_case_section_id, "", assignee_name, assignee_gid, tw_case_id]
        
        tw_df.loc[len(tw_df.index)] = tw_case_info

full_table = pd.merge(lw_df, tw_df, on = 'case_id', how = 'outer')
full_table = full_table.sort_values(by = ['case_section_id', 'case_name'], ascending = [True, True], na_position = 'last', ignore_index=True)

new_cases = ""
changed_cases = ""
unchanged_cases = ""

print(f"Done. There are {len(full_table.index)} total cases.\n\nPulling comments ...")

# Pulling the new comments from Asana
for i, x in full_table.iterrows():
    try:
        stories_call = asana.StoriesApi(api_client)
        stories_call_opts = ["type","text"]
        stories_data = stories_call.get_stories_for_task(x["case_id"], opt_fields=stories_call_opts)
        stories_data = stories_data.data
        comments_array = []
        for a in stories_data:
            if a.type == "comment":
                comments_array.append(a.text)
        most_recent_comment = comments_array[len(comments_array) - 1]
        most_recent_comment = re.sub(r'\n', '', most_recent_comment)
        full_table.at[i, "case_comment_y"] = most_recent_comment
    except:
        print(f'Couldn\'t pull comment for "{x["case_name"]}" — likely this case was completed or is brand new')
        continue

current_section = ""

for i, x in full_table.iterrows():
    #url = base_url + str(x["case_id"])
    case_id = str(x["case_id"])
    case_name = str(x["case_name"])
    
    if x["case_section_y"] in with_legal_array:
        tw_dict["with_legal"] += 1
    elif x["case_section_y"] in stalled_array:
        tw_dict["stalled"] += 1
    elif x["case_section_y"] == "with T&S":
        tw_dict["with_tns"] += 1
    tw_dict['total_cases'] = tw_dict["with_tns"] + tw_dict["with_legal"] + tw_dict["stalled"]

    try:
        assignee_id = assignees_dict[x["case_assignee"]]
        assignee_name = x["case_assignee"]
    except:
        assignee_id = "no assignment"
    if isinstance(x["case_section_x"], float): # Not in last week's update so probably a new case
        section = x["case_section_y"]
        if current_section != section and current_section != "":
            new_cases += "\n"
        new_cases += f'<ul><li>{task_link(case_id)} ({section} - {assignee(assignee_id)})</li>'
        new_cases += f'<ul><li>{new_case_comment(i)}</li></ul></ul>'
        tw_dict['new_cases'] += 1
    elif isinstance(x["case_section_y"], float): # Not in this week's update so probably completed
        tw_dict["completed_cases"] += 1
    elif x["case_section_x"] != x["case_section_y"]: # Moved cases
        section = f'{x["case_section_x"]} → {x["case_section_y"]}'
        if current_section != x["case_section_y"] and current_section != "":
            changed_cases += "\n"
        changed_cases += f'<ul><li>{task_link(case_id)} ({section} - {assignee(assignee_id)})</li>'

        if x["case_comment_x"] != x["case_comment_y"]:
            changed_cases += compare_comments(i, x["case_comment_x"], x["case_comment_y"])
        else:
            changed_cases += f'<ul><li>{x["case_comment_y"]}</li></ul></ul>'

    else:
        section = x["case_section_y"] # Unchanged cases
        if current_section != x["case_section_y"] and current_section != "":
            unchanged_cases += "\n"
        unchanged_cases += f'<ul><li>{task_link(case_id)} ({section} - {assignee(assignee_id)})</li>'

        if x["case_comment_x"] != x["case_comment_y"]:
            unchanged_cases += compare_comments(i, x["case_comment_x"], x["case_comment_y"])
        else:
            unchanged_cases += f'<ul><li>{x["case_comment_y"]}</li></ul></ul>'

    current_section = x["case_section_y"]
    
if len(new_cases) == 0:
    new_cases = "<em>none</em>"

output = "<body><strong>Overall stats</strong><ul>"
output += f"<li>Total cases: <strong>{str(tw_dict['total_cases'])}</strong> ({delta(lw_dict['total_cases'], tw_dict['total_cases'])} on last update)</li>"
output += f"<li>New cases: <strong>{str(plural(tw_dict['new_cases']))}</strong> ({delta(lw_dict['new_cases'], tw_dict['new_cases'])})</li>"
output += f"<li>Completed cases: <strong>{str(plural(tw_dict['completed_cases']))}</strong> ({delta(lw_dict['completed_cases'], tw_dict['completed_cases'])})</li></ul>\n"
output += f"<ul><li>With T&S: <strong>{str(plural(tw_dict['with_tns']))}</strong> ({delta(lw_dict['with_tns'], tw_dict['with_tns'])})</li>"
output += f"<li>With Legal: <strong>{str(plural(tw_dict['with_legal']))}</strong> ({delta(lw_dict['with_legal'], tw_dict['with_legal'])})</li>"
output += f"<li>Stalled: <strong>{str(plural(tw_dict['stalled']))}</strong> ({delta(lw_dict['stalled'], tw_dict['stalled'])})</li></ul>"

output += f"\n<strong>New cases</strong>{new_cases}\n<strong>Changed cases</strong>{changed_cases}\n<strong>Unchanged cases</strong>{unchanged_cases}</body>"

print("Done!\n")

f = open("output.html", "w")
f.write(output)
print("Written output to `output.html`")
f.close()

print(full_table)

print("Posting status update ...")
if debug == True:
    project_id = "1205304831498642"
    print("In debug mode. Will use the test project at https://app.asana.com/0/1205304831498642")

# Create a status update
post_call = asana.StatusUpdatesApi(api_client)
body = asana.StatusUpdatesBody({"html_text": output, "parent": project_id, "status_type": "on_track",})
opt_fields = ["author","author.name","created_at","created_by","created_by.name","hearted","hearts","hearts.user","hearts.user.name","html_text","liked","likes","likes.user","likes.user.name","modified_at","num_hearts","num_likes","parent","parent.name","resource_subtype","status_type","text","title"]

really_run = input("Type 'Y' to really post this status. ")
if really_run == "Y":
    try:
        api_response = post_call.create_status_for_object(body, opt_fields=opt_fields)
        print(f"Written status update to https://app.asana.com/0/0/{api_response.data.gid}")
    except ApiException as e:
        print("Exception when calling StatusUpdatesApi->create_status_for_object: %s\n" % e)
else:
    print("Will not post.")