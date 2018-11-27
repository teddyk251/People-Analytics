import re
import networkx as nx


def parse_file_comment_text(text):
    from_user = None
    to_user = None
    comment = None
    m = re.match(r"<@(U\w+)> commented on <@(U\w+)>.s file <.+\|.+>:(.*)$", text)
    if m:
        from_user = m[1]
        to_user = m[2]
        comment = m[3]

    return from_user, to_user, comment


def build_action_graph(messages, users_df, channels_df):
    G=nx.DiGraph()
    G.add_nodes_from(users_df.id)
    G.add_nodes_from(channels_df.id)
    default_subtypes = ['chat', 'reply_broadcast', 'thread_broadcast', 'channel_join', 'channel_name', 'channel_purpose', 'channel_topic', 'channel_archive', 'channel_unarchive', 'pinned_item', 'channel_leave']
    for m in messages:
        if 'bot' in m['subtype']:
            # bots are not people
            pass
        elif m['user'] and m['channel_id']:
            if m['type'] != 'reaction' and m['subtype'] not in default_subtypes:
                print("not a chat: ", m)
            m = dict(m)
            G.add_edge(m['user'], m['channel_id'], attr_dict=m)
        elif m['subtype'] == 'file_comment':
            # should this also add an edge to the channel?
            a,b,c = parse_file_comment_text(m['text'])
            if a:
                m = dict(m)
                m['text'] = c
                G.add_edge(a, b, attr_dict={'text': c})
        else:
            print(m)
            input()
    return G

def collapse_sentiment(period='monthly'):
    pass
