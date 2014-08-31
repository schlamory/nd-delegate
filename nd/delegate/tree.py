class Node(object):

  def __init__(self, parent = None, children = []):
    self._children = children
    self.parent = parent

  @property
  def children(self):
    return self._children

  @children.setter
  def children(self, values):
    for child in values:
      child.parent = self
    self._children = values
