import yaml, pyaml, os
from collections import OrderedDict

import pdf

class TranscriptionTask(object):

  def __init__(self, name=None, pages = []):
    self.name = name
    self.pages = pages

  @classmethod
  def create(cls, pdf_path):
    name = os.path.split(pdf_path)[1].replace(".pdf", "")
    pages = [TranscriptionTaskPage(pdf_page=page) for page in pdf.load(pdf_path).get_pages()]
    task = cls(name = name, pages = pages)
    return task

  @classmethod
  def load(cls, yaml_path):
    pass

  def save(self, path):
    pass

  def submit(self):
    for (page_number, page_task) in enumerate(self.pages):
      page_task.submit(bucket_key="{0}/{1}.pdf".format(self.name, page_number))

  def review(self):
    pass

  @property
  def serializable_dict(self):
    pass

class TranscriptionTaskPage(object):

  def __init__(self, pdf_page=None, hit_id=None, bucket_key=None):
    self.pdf_page = pdf_page
    self.hit_id = None
    self.bucket_key = None