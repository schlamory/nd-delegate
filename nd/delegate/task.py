import yaml, pyaml, os
from collections import OrderedDict

class AbstractTask(object):

  def __init__(self, name=None, subtasks=[]):
    self.name = name
    self._subtasks = None
    self.subtasks = subtasks

  @property
  def subtasks(self):
    return self._subtasks

  @subtasks.setter
  def subtasks(self, values):
    if values is None:
      self._subtasks = None
    else:
      self._subtasks = [self.subtask_class(**v) if isinstance(v, dict) else v for v in values]

  @property
  def subtask_class(self):
    return self.__class__

  def serializable_attributes(self):
    return ["name", "subtasks"]

  @property
  def serializable_dict(self):
    serialize = lambda ob: ob.serializable_dict if hasattr(ob, "serializable_dict") else ob
    d = OrderedDict()
    for k in self.serializable_attributes():
      v = getattr(self, k)
      if hasattr(v, '__iter__'):
        v = [serialize(vv) for vv in v]
      d[k] = serialize(v)
    return d

  @property
  def to_yaml(self):
    return pyaml.dump(self.serializable_dict)

  def save(self, yaml_path):
    f = open(yaml_path, "w")
    f.write(self.to_yaml)
    f.close()

  @classmethod
  def load(cls, yaml_path):
    f = open(yaml_path)
    d = yaml.safe_load(f.read())
    f.close()
    return cls(**d)

  def submit(self):
    for task in self.subtasks:
      task.submit()

  def review(self):
    for task in self.subtasks:
      task.review()
