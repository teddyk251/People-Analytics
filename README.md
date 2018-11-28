# People Analytics

Tools and technology to gain insight into organizational behaviour.

The core python module is called `wundt`, after Wilhelm Wundt:

> The roots of I/O psychology trace back nearly to the beginning of psychology as a science,
> when Wilhelm Wundt founded one of the first psychological laboratories in 1879 in Leipzig, Germany.
> In the mid 1880s, Wundt trained two psychologists, Hugo Münsterberg and James McKeen Cattell,
> who had a major influence on the emergence of I/O psychology.


## Getting Started

Set up a virtualenv and install requirements:

```
mkvirtualenv --python=/usr/bin/python3.6 people-analytics
pip install -r requirements.txt
```

Run the reporting script:
```
python -m wundt.report --path 
```

Currently this just loads the data in pandas and into a networkx graph, and prints some information.

Eventually it should also generate a bunch of graphs and visuals showing different aspects as described below.

## Normalisation of data

> This is an architectural guide, the current code doesn't match this yet...

The project aims to ingest data from multiple data sources (hereafter called an "ActionSource"), and these could be quite different.

Example of an ActionSource:
- slack
- git commits
- bug/issue trackers
- email

Our canonical representation, at this stage, will be that of an "Action". 
An action is a single record, with a timestamp, representing something a person does. Some examples
are:

- send a slack message
- add an emoji reaction to a slack message
- make a git commit
- send an email

Each of these actions will have different associated metadata, so we should allow for a freeform key/value
attributes for later analysis. Core attributes that all actions have should be:

- **source** - unique key for where the data comes from (e.g. "iCog Slack", "all email for singularitynet.io")
- **source-type** - the importer used (e.g. slack, email, git)
- **source-actor** - an identifier for the user, as used by the original source (e.g. slack user id `U04K91T8E`, email address `joel@singularitynet.io`)
- **source-targets** - actions can be directed at other entities (e.g. a file in a repo, a slack channel) or another user (e.g. the `to:` field in an email).
  This supports multiple targets, each target has a weight as some actions only weakly target other entities (e.g. `cc:` in email is weighted less than `to:`)
- **source-content** - contains the action metadata, mostly unprocessed.
- **timestamp** - milliseconds since the unix epoch

These actions in addition have minor processing to do record linkage with users/entities across different data sources

- **actor** - the canonical user inside our system, initially this 
- **targets** - the canonical users/entities this action is directed at. Each target has a weight associated.

## Data Exploration

> This is an architectural guide to help guide implementation, the current code doesn't do all of this yet...

### Action Frequency

- Track actor action frequency. This may highlight times of high collaboration, or when an actor becomes disengaged from their work or a particular project.
- Track a target's frequency of recieving actions. This should highlight central hubs, common channels or core decision makers being reported to.

### Sentiment Average and Through Time

- Track actor average sentiment or baseline positivity
- Track actor sentiment through time, highlight when people have burnt out, become over stressed, or are reacting adversely to organizational changes (or when things are improving!)
- Track a target's average sentiment, for a slack channel, highlights good and bad team environments.
- Track a target's sentiment through time, either a warning when things are going south, or positive feedback when team dynamics are improving.

### Graph analysis

Place actions into relationship graph between actors.

- Reduce graph to actor relationships, track through time with exponential decay
    - Strength of relationship based on frequency of interaction
    - Sentiment

There is some subtlety around this. In groups like slack channels, the target of an action is not always clear, but we can often infer it from recent actions by other actors in the group.

e.g.
- Actor A performs action X2 in group G, at time T1
- Actor B performs action X2 in group G, at time T2
- If `T2-T1 < T_limit`, then action X2 can be assumed to have Actor A as a primary target (higher weight), whereas everyone else in group G is a secondary target with much less weight.

At other times there is a much clearer signal of the intended recipient. One way is that slack messages can tag users (e.g. `@johndoe`), but even this isn't clear cut,
as the semantics of tagging a user has subtlely different meaning if it is at the start, the middle, or at the end of a message.

Regardless, these interactions can be defined in the ActionSource importer, and where the developer is estimating weights or variables like `T_limit`, these should be clearly
documented and configurable.

### Clustering 

We can cluster on:
- Actions from a specific ActionSource - we should expect that positive and negative actions are grouped together.
- Actors - how do we reduce N Actions by an actor into a representation that can be clustered? Possibly just use the actor label on top of the clustered actions. If an actor
  has different behaviour when interacting in different contexts, then actions in those contexts may end up displayed in distinct clusters. The surrounding actions from other
  actors may give an overall feel for the cluster they are part of.

Breaking it down further, we can tokenise the content of Actions (e.g. the words in an email), use a language model to convert the tokens to word vectors, and then cluster on these.

## Questions we want to be able to answer

TODO, convert from the Google Doc into implementation plan, revise the rest of this README based on those.

## Processing Pipeline

Actions should be able to stream into a live system. To keep this easy to understand, maintain, and scale, we should do as much preprocessing
on individual actions.

- Importer for an ActionSource converts data into Actions. An individual event from an ActionSource may generate 0 or more Actions.
- Link actor and targets in Action to canonical ids, initially from a rudimentary mapping (e.g. email address)
- Sentiment analysis on each Action

Later steps are not per action so need to be calculated in a batch manner.
- Aggregate/summarise each actor's behaviour through time
- Use difference of actor's average behaviour vs each action target to highlight positive/negative relationships between actors.
- ...

