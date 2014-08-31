import unittest
from mock import MagicMock, patch

from ..tree import Node

class TestNode(unittest.TestCase):

  def test_init(self):
    node = Node()
    assert node.children == []
    assert node.parent == None

  def test_children_setter(self):
    parent = Node()
    child = Node()
    parent.children = [child]
    assert child.parent == parent
    assert parent.children == [child]
