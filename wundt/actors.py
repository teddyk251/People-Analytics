import recordlinkage
import pandas as pd
import numpy as np

import hashlib
import random
import string

class COLUMN_ROLE:
    """ Each column is assigned a semantic role which is used for record linkage between sources """
    IGNORE = 0
    SOURCE_ID = 1
    USERNAME = 2
    FIRST_NAME = 3
    LAST_NAME = 4
    FULL_NAME = 5
    EMAIL = 6

class ActorDetails:
    """ Represent the set of actors from an Action Source """

    def __init__(self, source_label, actors_df, column_types):
        assert len(actors_df.columns) == len(column_types)
        self.source_label = source_label
        self.df = actors_df
        self.column_types = column_types

def new_canon_details():
    col_names =  ['Full Name', 'First Name', 'Last Name', 'Username 1', 'Username 2', 'Email 1', 'Email 2', 'Email 3']
    col_types =  [C.FULL_NAME, C.FIRST_NAME, C.LAST_NAME, C.USERNAME, C.USERNAME, C.EMAIL, C.EMAIL, C.EMAIL]
    canon_df  = pd.DataFrame(columns = col_names)
    canon_details = ActorDetails('canon', canon_df, col_types)
    return canon_details


C = COLUMN_ROLE

def create_hash_id_column(canon_df):
    tmplist = list(set(canon_df['Full Name']))
    print("LIST VALUE: ", tmplist)
    
    #Adding further character to  the content
    mapping1 = {i : ''.join(random.choice(string.hexdigits) for i in range(3)) + str(i) + (''.join(random.choice(string.hexdigits) for i in range(3))) for i in tmplist}
    
    d2 = canon_df.copy()
    d2['newname'] = [mapping1[i] for i in d2['Full Name']]
    d2.to_csv("three.csv", sep='\t', encoding='utf-8')
    d2['hash'] = [hashlib.sha512(str.encode(str(i))).hexdigest() for i in d2['newname']]
    d3 = d2[['Full Name','hash','Username 1','Email 1']].rename(columns={'hash':'Full NameHash'})
    d3.to_csv("two.csv", sep='\t', encoding='utf-8')
    return d3

def dedupe_and_normalise(actor_details):
    deets = actor_details
    df = actor_details.df

    indexer = recordlinkage.Index()
    #user should be indexed with name to avoid tagging two Slack users as one
    indexer.block('name')

    candidate_links = indexer.index(df, df)

    compare_cl = recordlinkage.Compare()

    cols = 0

    for ct_idx, ct in enumerate(deets.column_types):
        column_name = df.columns[ct_idx]
        if ct == C.FULL_NAME:
            compare_cl.string(column_name, column_name,
                    method='jarowinkler', threshold=0.85, label=column_name)
            cols += 1
        elif ct == C.FIRST_NAME:
            compare_cl.string(column_name, column_name,
                    method='jarowinkler', threshold=0.85, label=column_name)
            cols += 1
        elif ct == C.LAST_NAME:
            compare_cl.string(column_name, column_name,
                    method='jarowinkler', threshold=0.85, label=column_name)
            cols += 1
        elif ct == C.USERNAME:
            compare_cl.string(column_name, column_name,
                    method='jarowinkler', threshold=0.85, label=column_name)
            cols += 1

    features = compare_cl.compute(candidate_links, df, df)

    # Create a reference from the original details to the normalised data frame
    # idx
    df['normalised_idx'] = -1
    matches = features[features.sum(axis=1) > cols * 0.5]
    normalised_details = new_canon_details()
    entries_used = set()
    for src_idx in matches.index.get_level_values(0).unique():
        submatches = matches.loc[src_idx]

        row = [np.nan] * len(normalised_details.column_types)
        num_usernames = 0
        num_emails = 0

        ndf = normalised_details.df
        new_idx = len(ndf)

        for i in submatches.index.get_level_values(0).unique():
            sub_idx = i
            if sub_idx in entries_used:
                continue
            for ct_idx, ct in enumerate(deets.column_types):
                column_name = df.columns[ct_idx]
                if ct == C.FULL_NAME:
                    row[0] = df.iloc[sub_idx][column_name]
                elif ct == C.FIRST_NAME:
                    row[1] = df.iloc[sub_idx][column_name]
                elif ct == C.LAST_NAME:
                    row[2] = df.iloc[sub_idx][column_name]
                elif ct == C.USERNAME:
                    if num_usernames < 2:
                        row[3 + num_usernames] = df.iloc[sub_idx][column_name]
                        num_usernames += 1
                elif ct == C.EMAIL:
                    if num_emails < 3:
                        row[5 + num_emails] = df.iloc[sub_idx][column_name]
                        num_emails += 1
                df.at[sub_idx, 'normalised_idx'] = new_idx
            entries_used.add(sub_idx)

        if any(row):
            ndf.loc[new_idx] = row
    return normalised_details


def canon_link(canonical_details, source_normalised_details):
    cd = canonical_details
    nd = source_normalised_details

    indexer = recordlinkage.Index()
    indexer.full()

    candidate_links = indexer.index(cd.df, nd.df)

    compare_cl = recordlinkage.Compare()

    column_name = "Full Name"
    compare_cl.string(column_name, column_name,
        method='levenshtein', threshold=0.85, label=column_name)
    column_name = "First Name"
    compare_cl.string(column_name, column_name,
        method='levenshtein', threshold=0.85, label=column_name)
    column_name = "Last Name"
    compare_cl.string(column_name, column_name,
        method='levenshtein', threshold=0.85, label=column_name)

    compare_cl.string("Username 1", "Username 1",
        method='levenshtein', threshold=0.85, label="Username 1-1")
    compare_cl.string("Username 1", "Username 2",
        method='levenshtein', threshold=0.85, label="Username 1-2")
    compare_cl.string("Username 2", "Username 2",
        method='levenshtein', threshold=0.85, label="Username 2-2")
    # TODO Change this to exact matching
    compare_cl.string("Email 1", "Email 1",
        method='levenshtein', threshold=0.85, label="Email 1-1")
    compare_cl.string("Email 1", "Email 2",
        method='levenshtein', threshold=0.85, label="Email 1-2")
    compare_cl.string("Email 1", "Email 3",
        method='levenshtein', threshold=0.85, label="Email 1-3")
    compare_cl.string("Email 2", "Email 2",
        method='levenshtein', threshold=0.85, label="Email 2-2")
    compare_cl.string("Email 2", "Email 3",
        method='levenshtein', threshold=0.85, label="Email 2-3")
    compare_cl.string("Email 3", "Email 3",
        method='levenshtein', threshold=0.85, label="Email 3-3")

    features = compare_cl.compute(candidate_links, cd.df, nd.df)

    # Create a reference from the original details to the normalised data frame
    # idx
    nd.df['canonical_idx'] = -1
    matches = features[features.sum(axis=1) >= 1]
    #print("matches", matches)

    entries_used = set()
    for src_idx in matches.index.get_level_values(0).unique():
        # matches just for this src_idx
        submatches = matches.loc[src_idx]

        row = [np.nan] * len(cd.column_types)
        num_usernames = 0
        num_emails = 0

        for i in submatches.index.get_level_values(0).unique():
            sub_idx = i
            if sub_idx in entries_used:
                continue
            for ct_idx, ct in enumerate(cd.column_types):
                column_name = cd.df.columns[ct_idx]
                #row[3 + num_usernames] = df.iloc[sub_idx][column_name]
            nd.df.at[sub_idx, 'canonical_idx'] = src_idx
            # Now merge nd row into cd row

            cd_row = cd.df.iloc[src_idx]
            for col in ['Full Name', 'First Name', 'Last Name']:
                if pd.isna(cd_row[col]):
                    # Copy value from normalised into canonical
                    cd.df.at[src_idx, col] = nd.df.at[sub_idx, col]

            usernames = []
            offset = 0
            username_cols = ['Username 1', 'Username 2']

            for col in username_cols:
                if not pd.isna(cd_row[col]):
                    usernames.append(cd_row[col])
                    offset += 1
                    continue
            for col in username_cols:
                if offset > len(username_cols) - 1:
                    continue
                if not pd.isna(nd.df.at[sub_idx, col]):
                    cd.df.at[src_idx, username_cols[offset]] = nd.df.at[sub_idx, col]
                    offset += 1

            emails = []
            offset = 0
            email_cols = ['Email 1', 'Email 2', 'Email 3']

            for col in email_cols:
                if not pd.isna(cd_row[col]):
                    emails.append(cd_row[col])
                    offset += 1
                    continue
            for col in email_cols:
                if offset > len(email_cols) - 1:
                    continue
                if not pd.isna(nd.df.at[sub_idx, col]):
                    cd.df.at[src_idx, email_cols[offset]] = nd.df.at[sub_idx, col]
                    offset += 1

            entries_used.add(sub_idx)

    # Now add everything that wasn't matched to the canonical actor details table
    for i in range(len(nd.df)):
        if i in entries_used:
            # skip matched entries that have been merged
            continue
        c_idx = len(cd.df)
        cd.df.loc[c_idx] = nd.df.iloc[i] 
        nd.df.at[i, 'canonical_idx'] = c_idx

    #print(nd.df)
    #print(cd.df)
    return canonical_details


def link_all(actors_by_source):
    canon_details = None
    normalised_by_source = {}

    for source in actors_by_source:
        # dedupe
        print("Deduping", source)
        normalised_details = dedupe_and_normalise(actors_by_source[source])
        normalised_by_source[source] = normalised_details
        #print(normalised_details.df.to_string())
        # Link with canonical details

        if canon_details is None:
            # initialise our table of canonical actors with the first source's
            # normalised actor table
            canon_details = new_canon_details()
            canon_details.df = normalised_details.df.copy(deep=True)
        else:
            canon_link(canon_details, normalised_details)

    return canon_details, normalised_by_source