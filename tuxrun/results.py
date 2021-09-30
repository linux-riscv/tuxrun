from tuxrun.yaml import yaml_load


class Results:
    def __init__(self):
        self.__ret__ = 0

    def parse(self, line):
        data = yaml_load(line)
        if data is None:
            return
        if data["lvl"] != "results":
            return
        test = data["msg"]
        if test["result"] == "fail":
            self.__ret__ = 1

    def ret(self):
        return self.__ret__
