import yaml, pyaml, os
from collections import OrderedDict
from task import AbstractTask

import pdf, mturk

from boto.s3.connection import S3Connection

def connect(aws_access_key_id = None,
            aws_secret_access_key = None,
            bucket_name = None,
            sandbox = False):

  mturk_host = "mechanicalturk{0}.amazonaws.com".format(".sandbox" if sandbox else "")
  mturk.connect(host=mturk_host,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key)
  global bucket
  bucket = S3Connection(aws_access_key_id, aws_secret_access_key).get_bucket(bucket_name)

class TranscriptionTask(AbstractTask):

  def __init__(self, name=None, subtasks = [], **kargs):
    self.name = name
    self.subtasks = subtasks

  @classmethod
  def create(cls, pdf_path):
    name = os.path.split(pdf_path)[1].replace(".pdf", "")
    pages = pdf.load(pdf_path).get_pages()
    make_subtask = lambda i, page: TranscriptionTaskPage(pdf_page=page, page_number = i)
    subtasks = [make_subtask(i, page) for (i, page) in enumerate(pages)]
    task = cls(name = name, subtasks = subtasks)
    return task

class TranscriptionTaskPage(AbstractTask):

  def __init__(self, pdf_page=None, page_number=None, subtasks = None, parent=None):
    self.pdf_page = pdf_page
    self.page_number = page_number
    self.subtasks = subtasks
    self.parent = parent

  @property
  def s3_key(self):
    return "{0}/{1}.pdf".format(self.parent.name, self.page_number)

class TranscriptionHIT(AbstractTask):

  def __init__(self, hit_id=None, pdf_url=None, parent=None):
    this.hit_id = hit_id
    this.pdf_url = pdf_url
    this.parent = parent