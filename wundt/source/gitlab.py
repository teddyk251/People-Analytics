import os
import glob
import json
from pprint import pprint

import pandas as pd


def get_repo_directories(gitlab_dir):
    return [os.path.join(gitlab_dir, x) for x in os.listdir(gitlab_dir) if os.path.isdir(os.path.join(gitlab_dir,x))]


def load_repo_commits(repo_dir):
    files = glob.glob(repo_dir + '/commits_*_master_*.json')
    # exports are *_1.json *_2.json etc, sort to make sure they are loaded into the frame in order
    files.sort()
    commit_data = []
    for commit_file in files:
        with open(commit_file) as f:
            commit_data.extend(json.load(f))
    return commit_data


def parse_commit(c):
    ## When we have details of files modified, these should become the message targets

    actions = [{
        'id': c['id'],
        'type': 'commit',
        'subtype': 'commit',
        'ts': pd.Timestamp(c['authored_date']),
        'channel_id': c['repo'],
        'channel_name': c['repo'],
        'text': c['message'],
        'author_email': c['author_email'],
        'author_name': c['author_name'],
    }]

    return actions


def load_commits(gitlab_dir):
    repo_dirs = get_repo_directories(gitlab_dir)

    # not sure what these directories are about
    ignore_directories = ['project_info', '.pra']
    commit_data = []

    idx = 0

    for directory in repo_dirs:
        repo_name = os.path.basename(directory)
        if repo_name in ignore_directories:
            continue
        commits = load_repo_commits(os.path.join(directory))
        for c in commits:
            c['repo'] = repo_name
            commit_data.extend(parse_commit(c))

    return commit_data


def extract_actors_and_entities(commit_data):
    actors = {}
    entities = {}

    for c in commit_data:
        actors[c['author_email']] = {"id":c['author_email'], "name":c['author_name']}
        ## When we have details of files modified, these should become entities
        entities[c['channel_id']] = {"id":c['channel_id']}

    return list(actors.values()), list(entities.values())
        

def import_gitlab_archive(gitlab_dir, dump_info=False):
    commit_data = load_commits(gitlab_dir)
    print(len(commit_data))

    actors, entities = extract_actors_and_entities(commit_data)
    pprint(actors)
    pprint(entities)

    # Optionally show some summary of what we found in the raw messages
    if dump_info:
        pass

    # Apply these functions to each message
    per_message_augmentors = []

    # Apply these functions to the the whole dataset (they still update individual messages,
    # but use messages with neighbouring context)
    all_message_augmentors = []

    commits_df = pd.DataFrame(commit_data)
    actors_df = pd.DataFrame(actors)
    entities_df = pd.DataFrame(entities)


    return commits_df, actors_df, entities_df