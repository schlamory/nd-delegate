from datetime import datetime, timedelta
import yaml, pyaml, os, random, string, re
from collections import OrderedDict

import pdf, tree, mturk
from mturk import HIT

from boto.s3.connection import S3Connection

# Status definitions
FINISHED = "FINISHED"
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
    name = "transcribe_" + os.path.split(pdf_path)[1].replace(".pdf", "")
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
    for child in self.children:
      child.review()

  @property
  def status(self):
    if any([child.status == PENDING for child in self.children]):
      return PENDING
    else:
      return FINISHED

  def to_dict(self):
    d = OrderedDict()
    d["name"] = self.name
    d["status"] = self.status
    d["page_tasks"] = [task.to_dict() for task in self.children]
    return d

  @classmethod
  def from_dict(cls, d):
    children = [TranscribePageTask.from_dict(dd) for dd in d["page_tasks"]]
    return cls(children=children, name=d["name"])

  def save(self, file_path):
    f = open(file_path, "w")
    f.write(pyaml.dump(self.to_dict()))
    f.close()

  @classmethod
  def load(cls, file_path):
    return cls.from_dict(yaml.load(open(file_path)))

  def get_charts(self):
    charts = []
    for child in self.children:
      attempt = child.get_latest_attempt()
      if attempt.name:
        charts.append(Chart(attempt))
      charts[-1].add_attempt(attempt)
    return charts

class TranscribePageTask(tree.Node):

  def __init__(self, pdf_page=None, page_number=None, validation_code=None,
                children = [], parent = None, page_url=None):
    tree.Node.__init__(self, children = children, parent = parent)
    self.pdf_page = pdf_page
    self.page_number = page_number
    self._validation_code = validation_code
    self._page_url = page_url

  @property
  def s3_key_name(self):
    return "{0}/{1}.pdf".format(self.parent.name, self.page_number)

  @property
  def page_url(self):
    if self._page_url is None:
      self._page_url = "https://s3-" + bucket.get_location() + ".amazonaws.com/"
      self._page_url += bucket.name + "/" + self.s3_key_name
    return self._page_url

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
    for child in self.children:
      child.review()

  def get_latest_attempt(self):
    return self.children[-1]

  @property
  def status(self):
    if any([child.status == "Approved" for child in self.children]):
      return FINISHED
    else:
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
    children = [TranscribePageAttempt.from_dict(dd) for dd in d["attempts"]]
    return cls(children=children, page_number = d["page_number"], page_url = d["page_url"],
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

  @property
  def assignment(self):
    if len(self.hit.assignments) > 0:
      return self.hit.assignments[-1]

  def review(self):
    if self.assignment and self.assignment != "Approved":
      self.assignment.approve()
      self.hit.refresh()

  @property
  def status(self):
    if len(self.hit.assignments):
      return self.hit.assignments[0].status
    else:
      return self.hit.status

  def to_dict(self):
    d = OrderedDict()
    d["hit_id"] = self.hit.id
    d["status"] = self.status
    return d

  @classmethod
  def from_dict(cls, d):
    return cls(hit_id=d["hit_id"])

  @property
  def name(self):
    name = self.assignment.answers_dict["name"].upper().strip()
    if name == "NONAME" or name == "LAURA FIGOSKI":
      return None
    else:
      return re.sub("[^A-Z]", "_", name)

  @property
  def date(self):
    date = self.assignment.answers_dict["date"].upper().strip()
    return None if date == "NODATE" else re.sub("[^\w]","_",date).strip()

  @property
  def validation_code(self):
    return self.answers_dict["validation_code"].upper().strip()

  @property
  def note(self):
    note = self.assignment.answers_dict["note"]
    note = re.sub(r"\n\s*\-[\s\-]*","\n- ", "\n" +  note)  # Normalize leading dashes
    note = note.replace("\r\n","\n")
    return note

  @property
  def validation_code(self):
    return self.assignment.answers_dict["validation_code"]

class Chart(object):

  def __init__(self, assignment):
    self.name = assignment.name
    self.date = assignment.date
    self.note = ""

  @property
  def file_name(self):
    return "{0}_{1}.md".format( self.name, self.date)

  def add_attempt(self, attempt):
    self.note += "<!-- \n{0}\nHIT ID:{1}\n -->".format(attempt.parent.page_url, attempt.hit.id)
    self.note += attempt.note + "\n\n "

  def write(self, output_dir):
    path = os.path.join(output_dir, self.file_name)
    f = open(path, "w")
    f.write(self.note.encode('ascii','ignore'))
    f.close()
