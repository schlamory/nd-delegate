import yaml, pyaml, os
from collections import OrderedDict
from task import AbstractTask

import pdf
from mturk import HIT

from boto.s3.connection import S3Connection

# Status definitions
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
PENDING = "PENDING"

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

  @property
  def serializable_attributes(self):
    return ["name", "subtasks", "status"]

  @property
  def subtask_class(self):
    return TranscribePageTask

  @classmethod
  def create(cls, pdf_path):
    name = os.path.split(pdf_path)[1].replace(".pdf", "")
    pages = pdf.load(pdf_path).get_pages()
    subtask_configs = [{"page_number": i, "pdf_page": page} for (i, page) in enumerate(pages)]
    task = cls(name = name, subtasks = subtask_configs)
    return task

  def submit(self):
    # Submit all child tasks
    AbstractTask.submit(self)

  def review(self):
    # Review all child tasks
    AbstractTask.review(self)

  def status(self):
    return PENDING

class TranscribePageTask(AbstractTask):

  def __init__(self, parent=None, pdf_page=None, page_number=None, subtasks = [], **kargs):
    self.pdf_page = pdf_page
    self.page_number = page_number
    self.parent = parent
    self.subtasks = subtasks

  @property
  def serializable_attributes(self):
    return ["page_number", "subtasks", "status"]

  @property
  def subtask_class(self):
    return TranscribePageAttempt

  @property
  def s3_key(self):
    return "{0}/{1}.pdf".format(self.parent.name, self.page_number)

  @property
  def submit(self):
    # Post the PDF
    # Create an attempt task
    # Submit child tasks
    AbstractTask.submit(self)

  def review(self):
    # Review attempts
    AbstractTask.review(self)
    # If one of the attempts is good, mark success
    # If none of the attempts is good, create another subtask and submit it

  @property
  def status(self):
    return PENDING

class TranscribePageAttempt(AbstractTask):

  def __init__(self, hit_id=None, pdf_url=None, parent=None, **kargs):
    self.hit = HIT(id=hit_id) if hit_id is not None else None
    self.pdf_url = pdf_url
    self.parent = parent

  @property
  def serializable_attributes(self):
    return ["hit_id", "status"]

  @property
  def hit_id(self):
    if self.hit is not None:
      return self.hit.id

  def submit(self):
    # Submit request if not HIT
    pass

  def review(self):
    # See if HIT has an assignment.
    # If it does, review it
    # If successful, approve the HIT and mark success
    # If failure, reject the HIT and mark failure
    pass

  @property
  def status(self):
    return PENDING
