from abc import abstractmethod


class BaseClass:
    @classmethod
    @abstractmethod
    def show(cls):
        print(cls.__name__)


class ChildClass(BaseClass):
    @classmethod
    def show(cls):
        super().show()


ChildClass.show()
