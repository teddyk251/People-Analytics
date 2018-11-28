import os


def get_path(slack_dir, fn):
    return os.path.join(slack_dir, fn)


class ActionData(object):

    def __init__(self):
        pass

    def entities(self):
        pass

    def messages(self):
        pass

    def users(self):
        pass
    