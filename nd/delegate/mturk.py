import boto
from datetime import datetime, timedelta
from boto.mturk.layoutparam import LayoutParameter, LayoutParameters
from boto.mturk.connection import MTurkConnection, Price

TURK_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

def connect(host = None, aws_access_key_id = None, aws_secret_access_key = None):
  global connection
  connection = MTurkConnection(host=host, aws_secret_access_key = aws_secret_access_key, aws_access_key_id = aws_access_key_id)

class Request(object):

  def __init__(self, layout_id, title, description, keywords, reward,
                duration = timedelta(hours=1),
                lifetime = timedelta(days=7),
                approval_delay = timedelta(days=1),
                annotation = None,
                layout_params = {},
                max_assignments = 1,
                qualifications=None):

    self.layout_id = layout_id
    self.title = title
    self.description = description
    self.keywords = keywords
    self.reward = reward
    self.lifetime = lifetime
    self.duration = duration
    self.approval_delay = approval_delay
    self.annotation = annotation
    self.layout_params = layout_params
    self.max_assignments = max_assignments
    self.qualifications = qualifications

  def submit(self):
    connection.create_hit(
      hit_layout = self.layout_id,
      lifetime = self.lifetime,
      max_assignments = self.max_assignments,
      title = self.title,
      description = self.description,
      keywords = self.keywords,
      reward = self.reward,
      duration = self.duration,
      approval_delay = self.approval_delay,
      annotation = self.annotation,
      qualifications = self.qualifications,
      layout_params = self.get_boto_layout_params()
    )

  def get_boto_layout_params(self):
    params = LayoutParameters()
    for k, v in self.layout_params.items():
      params.add(LayoutParameter(k, v))

class HIT(object):

  def __init__(self, id=None, boto_hit=None):
    if boto_hit:
      self._boto_hit = boto_hit
      self._id = boto_hit.HITId
    else:
      self._id = id
      self._boto_hit = None
    self._boto_assignments = None
    self._assignments = None

  def refresh(self):
    self._boto_hit = connection.get_hit(self.id)

  def expire(self):
    connection.expire_hit(self.id)
    self.refresh()

  def destroy(self):
    connection.dispose_hit(self.id)
    self.refresh()

  @property
  def id(self):
    return self._id

  @property
  def boto_hit(self):
    if self._boto_hit is None:
      self.refresh()
    return self._boto_hit

  def _boto_hit_attr(self, attr):
    if hasattr(self.boto_hit, attr):
      return getattr(self.boto_hit, attr)
    else:
      return None

  @property
  def boto_assignments(self):
    if self._boto_assignments is None:
      self._boto_assignments = connection.get_assignments(self.id)
    return self._boto_assignments

  @property
  def layout_id(self):
    return self._boto_hit_attr("HITLayoutId")

  @property
  def reward(self):
    amount = self._boto_hit_attr("Amount")
    if not amount is None:
      return float(amount)

  @property
  def status(self):
    return self._boto_hit_attr("HITStatus")

  @property
  def creation_time(self):
    datestring = self._boto_hit_attr("CreationTime")
    return datetime.strptime(datestring, TURK_DATE_FORMAT)

  @property
  def assignments(self):
    if self._assignments is None:
      self._assignments = [Assignment(hit=self, boto_assignment = assign) for
                            assign in connection.get_assignments(self.id)]
    return self._assignments

  @property
  def annotation(self):
    return self.boto_hit.RequesterAnnotation

  @property
  def completion_time(self):
    pass

  @property
  def complete(self):
    pass


class Assignment(object):

  def __init__(self, hit=None, boto_assignment=None):
    self._hit = hit
    self._boto_assignment = boto_assignment

  def refresh(self):
    self._boto_assignment = connection.get_assignment(self.id)

  def approve(self, message=None):
    if self.status == "Rejected":
      connection.approve_rejected_assignment(self.id, feedback=message)
    else:
      connection.approve_assignment(self.id, feedback=message)
    self.refresh()

  def reject(self, message):
    connection.reject_assignment(self.id, feedback=message)
    self.refresh()

  def grant_bonus(self, amount, reason):
    connection.grant_bonus(
      assignment_id = self.id,
      worker_id = self.worker.id,
      bonus_price = Price(amount, "USD"),
      reason = reason
    )

  @property
  def id(self):
    return self._boto_assignment.AssignmentId

  @property
  def hit(self):
    return self._hit

  @property
  def status(self):
    return self._boto_assignment.AssignmentStatus

  @property
  def worker(self):
    return Worker(self._boto_assignment.WorkerId)

  @property
  def submit_time(self):
    return datetime.strptime(self._boto_assignment.SubmitTime, TURK_DATE_FORMAT)

class Worker(object):

  def __init__(self, id):
    self._id = id

  @property
  def id(self):
    return self._id

  def send_message(self, subject, message):
    connection.notify_workers(worker_ids=[self.id], subject=subject, message_text = message)
