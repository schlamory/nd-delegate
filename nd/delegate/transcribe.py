import pyaml
import pdf
from collections import OrderedDict

class TranscriptionTask(object):

  def __init__(self, name=None, hits=[], pdf_page_keys=[]):
    self.name = name
    self.hits = hits
    self.pdf_page_keys = pdf_page_keys

  @classmethod
  def create(cls, pdf_path):
    pass

  @classmethod
  def load(cls, yaml_path):
    pass

  def save(self, path):
    pass

  def submit(self):
    pass

  def review(self):
    pass
