from tuxrun.yaml import yaml_load


class Results:
    def __init__(self):
        self.__data__ = {}
        self.__ret__ = 0

    def parse(self, line):
        data = yaml_load(line)
        if data is None:
            return
        if data["lvl"] != "results":
            return
        test = data["msg"]
        definition = test["definition"]
        case = test["case"]
        del test["definition"]
        del test["case"]
        self.__data__.setdefault(definition, {})[case] = test
        if test["result"] == "fail":
            self.__ret__ = 1

    @property
    def data(self):
        return self.__data__

    def ret(self):
        return self.__ret__
