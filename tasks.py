from enum import Enum


class TaskStatus(Enum):
    BLOCKED = 0
    TODO = 1
    INPROGRESS = 2
    DONE = 3


class Task:
    def __init__(self, _id: int, subj: str, status: TaskStatus):
        """[summary]

        Arguments:
            _id {int} -- [description]
            subj {str} -- [description]
            status {TaskStatus} -- [description]
        """
        self.id = _id
        self.subject = subj
        self.status = status


if __name__ == "__main__":
    import pdb
    pdb.set_trace()
    t = Task(111, 'demo', TaskStatus.TODO.value)
    print(t)
