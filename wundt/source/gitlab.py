import os
import glob
import json
from pprint import pprint

import pandas as pd
from wundt.actors import ActorDetails, COLUMN_ROLE as C, create_hash_id_column, get_keys


def get_repo_directories(gitlab_dir):
    return [os.path.join(gitlab_dir, x) for x in os.listdir(gitlab_dir) if os.path.isdir(os.path.join(gitlab_dir,x))]


def load_repo_commits(repo_dir):
    # exports are *_1.json *_2.json etc
    files = glob.glob(repo_dir + '/commits_*.json')
    commits_data = {}
    # store commits by hash id, because we are merging from multiple branches and there
    # may be duplicates
    for commit_file in files:
        with open(commit_file) as f:
            for commit in json.load(f):
                commits_data[commit['id']] = commit
    return commits_data.values()


def load_file_changes(repo_dir):
    files = glob.glob(repo_dir + '/commitsfiles_*.json')
    assert len(files) == 1
    with open(files[0]) as f:
        file_change_data = json.load(f)
    return file_change_data


def parse_commit(c):
    # We won't currently track a file getting renamed, just treat each filename
    # as a unique target
    targets = [f['new_path'] for f in c['files']]
    targets.append(c['repo'])

    actions = [{
        'id': c['id'],
        'source-type': 'gitlab',
        'source-content': {
            'type': 'commit',
            # change to add/remove/edit
            'subtype': 'commit',
            'message': c['message'],
            'repo': c['repo'],
            'author_email': c['author_email'],
            'author_name': c['author_name'],
            'files': c['files']
        },
        'ts': pd.Timestamp(c['authored_date']),
        'source-actor': c['author_email'],
        'source-targets': targets,

        # These should come from post-import record linking
        #'targets': c['repo'],
        #'actor': c['author_email'],
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
        file_changes = load_file_changes(os.path.join(directory))
        for c in commits:
            c['repo'] = repo_name
            c['files'] = file_changes[c['id']]

            commit_data.extend(parse_commit(c))

    return commit_data


def extract_actors_and_entities(commit_data):
    actors = {}
    entities = {}

    for c in commit_data:
        actors[c['source-actor']] = {
                "id": c['source-actor'],
                "email": c['source-actor'],
                "name":c['source-content']['author_name']
            }

    for c in commit_data:
        for target in c['source-targets']:
            # gitlab doesn't explicitly have actors that can be targets,
            # but another action source may need this differentiation
            if target not in actors:
                entities[target] = {"id": target}

    return list(actors.values()), list(entities.values())
        

def import_gitlab_archive(gitlab_dir, dump_info=False):
    git_hashed_data = {}
    commit_data = load_commits(gitlab_dir)
    print("Number of commits loaded", len(commit_data))

    actors, entities = extract_actors_and_entities(commit_data)

    # Optionally show some summary of what we found in the raw messages
    if dump_info:
        pprint(actors)
        pprint(entities)

    # Apply these functions to each message
    per_message_augmentors = []

    # Apply these functions to the the whole dataset (they still update individual messages,
    # but use messages with neighbouring context)
    all_message_augmentors = []

    for ma in per_message_augmentors:
        for msg in commit_data:
            ma(msg)

    for ma in all_message_augmentors:
        ma(commit_data)

    actors_df = pd.DataFrame(actors)
    
    # Hashing Git action data
    col_names = ['email', 'id', 'name']
    git_hashed_data, actors_df = create_hash_id_column(col_names, actors_df)
    
    commits_df = pd.DataFrame(commit_data)
    col_names = ['source-actor']

    # Hashing source-actor data
    #commits_df = get_keys(data, col_names, commits_df)
    data, commits_df = create_hash_id_column(col_names, commits_df)
    git_hashed_data.update(data)

    entities_df = pd.DataFrame(entities)
    actor_details = ActorDetails('gitlab', actors_df, [
        C.EMAIL,
        C.SOURCE_ID,
        C.FULL_NAME
    ]
    )

    return git_hashed_data, commits_df, actor_details, entities_df