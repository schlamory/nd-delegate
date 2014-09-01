from mock import MagicMock, patch
import unittest

import boto.mturk.connection
from datetime import datetime

from .. import mturk
from factories.mturk import (
                            RequestFactory,
                            BotoHITFactory, HITFactory,
                            BotoAssignmentFactory, AssignmentFactory,
                            WorkerFactory
                          )

class MockBotoConnection(mturk.MTurkConnection):

  def __init__(self, **kwargs):
    pass

mturk.MTurkConnection = MockBotoConnection
mturk.connect()

def test_connect_makes_conection():
  assert mturk.connection

class RequestTests(unittest.TestCase):

  def test_submit(self):
    mturk.connection.create_hit = MagicMock()
    request = RequestFactory()
    request.get_boto_layout_params = MagicMock(return_value="LAYOUT_PARAMS")
    request.submit()
    mturk.connection.create_hit.assert_called_with(
      hit_layout = request.layout_id,
      lifetime = request.lifetime,
      max_assignments = request.max_assignments,
      title = request.title,
      description = request.description,
      keywords = request.keywords,
      reward = request.reward,
      duration = request.duration,
      approval_delay = request.approval_delay,
      annotation = request.annotation,
      qualifications = request.qualifications,
      layout_params = "LAYOUT_PARAMS"
    )

class HITTests(unittest.TestCase):

  def test_boto_hit(self):
    boto_hit = BotoHITFactory()
    assert HITFactory(boto_hit = boto_hit).boto_hit == boto_hit

  def test_layout_id(self):
    assert HITFactory(boto_hit__HITLayoutId = "123").layout_id == "123"

  def test_reward(self):
    assert HITFactory(boto_hit__Amount = "0.25").reward == 0.25

  def test_status(self):
    assert HITFactory(boto_hit__HITStatus="The Status").status == "The Status"

  def test_annotation(self):
    assert HITFactory(boto_hit__RequesterAnnotation="The Annotation").annotation == "The Annotation"

  def test_creation_time(self):
    boto_hit = BotoHITFactory(CreationTime =  u'2014-07-26T23:44:15Z')
    time = datetime(year=2014, month=7, day = 26, hour= 23, minute = 44, second=15)
    assert HITFactory(boto_hit = boto_hit).creation_time == time

  def test_id_from_boto_hit(self):
    assert HITFactory(boto_hit__HITId="theID").id == "theID"

  def test_lazy_boto_hit(self):
    boto_hit = BotoHITFactory(HITId="remote_id")
    mturk.connection.get_hit = MagicMock(return_value=[boto_hit])
    hit = mturk.HIT(id="remote_id")
    assert hit.boto_hit == boto_hit
    mturk.connection.get_hit.assert_called_with(hit.id)

  def test_assignments_accessor(self):
    boto_assignment = BotoAssignmentFactory(AssignmentStatus="BRAND NEW")
    get_assignments = mturk.connection.get_assignments = MagicMock(return_value=[boto_assignment])
    hit = HITFactory()
    assert len(hit.assignments) == 1
    assert hit.assignments[0].status == "BRAND NEW"
    get_assignments.assert_called_once_with(hit.id)

  # Actions
  def test_refresh(self):
    boto_hit = BotoHITFactory(HITStatus="UPDATED")
    mturk.connection.get_hit = MagicMock(return_value=[boto_hit])
    hit = HITFactory()
    hit._boto_assignments = []
    hit._assignments = []
    hit.refresh()
    assert hit.status == "UPDATED"
    assert hit._assignments == None
    assert hit._boto_assignments == None
    mturk.connection.get_hit.assert_called_once_with(hit.id)

  def test_expire(self):
    expire_hit = mturk.connection.expire_hit = MagicMock()
    hit = HITFactory()
    hit.refresh = MagicMock()
    hit.expire()
    expire_hit.assert_called_once_with(hit.id)
    assert hit.refresh.called

  def test_destroy(self):
    dispose_hit = mturk.connection.dispose_hit = MagicMock()
    hit = HITFactory()
    hit.refresh = MagicMock()
    hit.destroy()
    dispose_hit.assert_called_once_with(hit.id)
    assert hit.refresh.called


class AssignmentTests(unittest.TestCase):

  def test_id(self):
    assert AssignmentFactory(boto_assignment__AssignmentId="theID").id == "theID"

  def test_hit(self):
    assert AssignmentFactory(hit="the hit").hit == "the hit"

  def test_status(self):
    assert AssignmentFactory(boto_assignment__AssignmentStatus="foo").status == "foo"

  def test_submit_time(self):
    boto_assignment = BotoAssignmentFactory(SubmitTime =  u'2014-07-26T23:44:15Z')
    time = datetime(year=2014, month=7, day = 26, hour= 23, minute = 44, second=15)
    assert AssignmentFactory(boto_assignment = boto_assignment).submit_time == time

  def test_worker(self):
    assert AssignmentFactory(boto_assignment__WorkerId=222).worker.id == 222

  # actions
  def setForUpApproveReject(self, assignment):
    self.reject = mturk.connection.reject_assignment = MagicMock()
    self.refresh = assignment.refresh = MagicMock()
    self.approve = mturk.connection.approve_assignment = MagicMock()
    self.approve_rejected = mturk.connection.approve_rejected_assignment = MagicMock()

  def test_approve_reviewable(self):
    assignment = AssignmentFactory(boto_assignment__AssignmentStatus="Reviewable")
    self.setForUpApproveReject(assignment)
    assignment.approve("good job")
    self.approve.assert_called_with(assignment.id, feedback="good job")
    assert assignment.refresh.called

  def test_approve_rejected(self):
    assignment = AssignmentFactory(boto_assignment__AssignmentStatus="Rejected")
    self.setForUpApproveReject(assignment)
    assignment.approve("thanks")
    self.approve_rejected.assert_called_with(assignment.id, feedback="thanks")
    assert assignment.refresh.called

  def test_reject_reviewable(self):
    assignment = AssignmentFactory(boto_assignment__AssignmentStatus="Reviewable")
    self.setForUpApproveReject(assignment)
    assignment.reject("no good")
    self.reject.assert_called_with(assignment.id, feedback="no good")
    assert assignment.refresh.called

  def test_refresh(self):
    new_boto_assignment = BotoAssignmentFactory(AssignmentStatus="NEW STATUS")
    get_assignment = mturk.connection.get_assignment = MagicMock(return_value=[new_boto_assignment])
    assignment = AssignmentFactory(boto_assignment__AssignmentId="theID")
    assignment.refresh()
    get_assignment.assert_called_with("theID")
    assert assignment.status == "NEW STATUS"

  def test_grant_bonus(self):
    grant_bonus = mturk.connection.grant_bonus = MagicMock()
    Price = mturk.Price = MagicMock(side_effect=lambda a, c: "{0}{1}".format(a, c))
    assignment = AssignmentFactory()
    assignment.grant_bonus(0.25, "the reason")
    Price.assert_called_with(0.25, "USD")
    grant_bonus.assert_called_with(
      assignment_id=assignment.id,
      worker_id=assignment.worker.id,
      bonus_price = "0.25USD",
      reason = "the reason"
    )

class WorkerTests(unittest.TestCase):

  def test_id(self):
    assert WorkerFactory(id="theID").id == "theID"

  def test_send_message(self):
    notify = mturk.connection.notify_workers = MagicMock()
    worker = WorkerFactory()
    worker.send_message("the subject", "the message")
    notify.assert_called_with(worker_ids=[worker.id], subject = "the subject",
                              message_text="the message")

# # Worker
# @pytest.fixture
# def worker(boto_assignment):
#   return mturk.Worker(boto_assignment.WorkerId)