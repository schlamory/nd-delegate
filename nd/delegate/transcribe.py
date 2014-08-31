from datetime import datetime, timedelta
import yaml, pyaml, os, random, string
from collections import OrderedDict
import tree

import pdf, tree, mturk
from mturk import HIT

from boto.s3.connection import S3Connection

# Status definitions
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
PENDING = "PENDING"
bucket = None

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

class TranscriptionTask(tree.Node):

  def __init__(self, name = None, children = None):
    tree.Node.__init__(self, children = children)
    self.name = name

  @classmethod
  def create(cls, pdf_path):
    name = os.path.split(pdf_path)[1].replace(".pdf", "")
    task = cls(name = name)
    pdf_pages = pdf.load(pdf_path).get_pages()
    subtasks = [TranscribePageTask(pdf_page = page, page_number = i+1) for
                                                                (i, page) in enumerate(pdf_pages)]
    task.children = subtasks
    return task

  def submit(self):
    for child in self.children:
      child.submit()

  def review(self):
    pass

  @property
  def status(self):
    return PENDING

  def to_dict(self):
    d = OrderedDict()
    d["name"] = self.name
    d["status"] = self.status
    d["page_tasks"] = [task.to_dict() for task in self.children]
    return d

  @classmethod
  def from_dict(cls, d):
    children = [TranscribePageTask(dd) for dd in d["page_tasks"]]
    return cls(children=children, name=d["name"])

class TranscribePageTask(tree.Node):

  def __init__(self, pdf_page=None, page_number=None, validation_code=None,
                children = [], parent = None):
    tree.Node.__init__(self, children = children, parent = parent)
    self.pdf_page = pdf_page
    self.page_number = page_number
    self._validation_code = validation_code

  @property
  def s3_key_name(self):
    return "{0}/{1}.pdf".format(self.parent.name, self.page_number)

  @property
  def page_url(self):
    return ("https://s3-" + bucket.get_location() + ".amazonaws.com/" +
                             bucket.name + "/" + self.s3_key_name)

  @property
  def validation_code(self):
    if self._validation_code is None:
      self._validation_code = ''.join(random.choice(string.ascii_uppercase) for _ in range(5))
    return self._validation_code

  def post_page(self):
    key = bucket.new_key(self.s3_key_name)
    key.content_disposition = "inline"
    page = self.pdf_page.get_annotated_copy(self.validation_code)
    page.save_to_s3(key)

  def submit(self):
    self.post_page()
    attempt = TranscribePageAttempt(parent = self)
    self.children = [attempt]
    attempt.submit()

  def review(self):
    # Review attempts
    # If one of the attempts is good, mark success
    # If none of the attempts is good, create another subtask and submit it
    pass

  @property
  def status(self):
    return PENDING


  def to_dict(self):
    d = OrderedDict()
    d["page_number"] = self.page_number
    d["page_url"] = self.page_url
    d["status"] = self.status
    d["validation_code"] = self.validation_code
    d["attempts"] = [attempt.to_dict() for attempt in self.children]
    return d

  @classmethod
  def from_dict(cls, d):
    children = [TranscribePageAttempt(dd) for dd in d["attempts"]]
    return cls(children=children, page_number = d["page_number"],
                validation_code=d["validation_code"])

class TranscribePageAttempt(tree.Node):

  def __init__(self, hit_id=None, parent=None):
    tree.Node.__init__(self, parent = parent)
    self.hit = HIT(id=hit_id) if hit_id is not None else None
    self.parent = parent

  @property
  def hit_id(self):
    if self.hit is not None:
      return self.hit.id

  def create_mturk_request(self):
    request = mturk.Request(
          title = "Transcribe hand-written note (<250 words)",
          layout_id = "3D6J5AH4A4SR81YRLC1BJVMCZB4C3P",
          description = "Transcribe hand-written medical chart note (<250 words)",
          keywords = "write, transcribe, english, medical, handwriting",
          reward = 0.35,
          lifetime = timedelta(days=7),
          duration = timedelta(hours=1),
          approval_delay = timedelta(days=1)
        )
    request.layout_params["file_url"] = self.parent.page_url
    return request

  def submit(self):
    request = self.create_mturk_request()
    self.hit = request.submit()

  def review(self):
    # See if HIT has an assignment.
    # If it does, review it
    # If successful, approve the HIT and mark success
    # If failure, reject the HIT and mark failure
    pass

  @property
  def status(self):
    return self.hit.status

  def to_dict(self):
    d = OrderedDict()
    d["hit_id"] = self.hit.id
    d["status"] = self.status
    return d

  @classmethod
  def from_dict(cls, d):
    return cls(hit_id=d["hit_id"])