

class ActorDetails:
    """ Represent the set of actors from an Action Source """

    class COLUMN_ROLE:
        """ Each column is assigned a semantic role which is used for record linkage between sources """
        SOURCE_ID = 0
        USERNAME = 1
        FIRST_NAME = 2
        LAST_NAME = 3
        FULL_NAME = 4
        EMAIL = 5

    def __init__(self, source_label, actors_df, column_types):
        self.source_label = source_label
        self.df = actors_df
        self.column_types = column_types

    

def link_users(actors1, actors2):
    """ Take two ActorDetails, and return a new merged ActorDetails based on heuristics """
    # TODO - just implement basic matching on username and email
    # Later use a graph optimisation strategy, and provide suggestions that can be validated by
    # a human.
    pass