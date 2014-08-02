import factory
import datetime
from ... import mturk
import boto.mturk.connection

class RequestFactory(factory.Factory):
  class Meta:
    model = mturk.Request

  layout_id = "HIT_LAYOUT_ID"
  title = "HIT title"
  description = "HIT description"
  keywords = "foo, bar, baz"
  reward = 0.25
  duration = datetime.timedelta(hours=1)
  lifetime = datetime.timedelta(days=7)
  approval_delay = datetime.timedelta(days=1)
  annotation = "HIT Annotation"
  layout_params = {"fooKey":"fooValue"}
  max_assignments = 1
  qualifications=None

class MockBotoHIT(boto.mturk.connection.HIT):
  def __init__(self, **kargs):
    for k, v in kargs.items():
      setattr(self, k, v)

class BotoHITFactory(factory.Factory):
  class Meta:
    model = MockBotoHIT

  Amount =  u'0.35'
  AssignmentDurationInSeconds =  u'3600'
  AutoApprovalDelayInSeconds =  u'86400'
  CreationTime =  u'2014-07-26T23:44:15Z'
  CurrencyCode =  u'USD'
  Description =  u'Transcribe hand-written medical chart note, <250 words'
  Expiration =  u'2014-07-26T23:47:06Z'
  FormattedPrice =  u'$0.35'
  HIT =  ''
  HITGroupId =  u'3T1550FWKJJUQ3XG033O0WT168SXW3'
  HITId =  u'39O6Z4JLX2YG6EZ0SNNI3BQ6SK7XVE'
  HITLayoutId =  u'3RJTKV7BOG0MVPN9LM7OJ2L2JAAD4R'
  HITReviewStatus =  u'NotReviewed'
  HITStatus =  u'Reviewable'
  HITTypeId =  u'3ZODJRR2QPOZVP5LXR86Y1P477RV2I'
  Keywords =  u'write, transcription, english, medical, handwriting'
  MaxAssignments =  u'1'
  NumberOfAssignmentsAvailable =  u'0'
  NumberOfAssignmentsCompleted =  u'1'
  NumberOfAssignmentsPending =  u'0'
  RequesterAnnotation =  u'{"batch_name": "2014_07_21_16_39_45", "page_number": 1, "type": "transcribe_chart"}'
  Reward =  ''
  Title =  u'Transcribe hand-written note (<250 words)'

class HITFactory(factory.Factory):
  class Meta:
    model = mturk.HIT

  boto_hit = factory.SubFactory(BotoHITFactory)
  id = None

# Assignment
class MockBotoAssignment(boto.mturk.connection.Assignment):
  def __init__(self, **kargs):
    for k, v in kargs.items():
      setattr(self, k, v)

class BotoAssignmentFactory(factory.Factory):

  class Meta:
    model = MockBotoAssignment

  AcceptTime =  u'2014-07-26T23:46:48Z'
  ApprovalTime =  u'2014-07-27T00:11:13Z'
  Assignment =  ''
  AssignmentId =  u'3VBEN272MK0SFKLZZLOBTM1NS9MSGU'
  AssignmentStatus =  u'Approved'
  AutoApprovalTime =  u'2014-07-27T23:57:00Z'
  HITId =  u'39O6Z4JLX2YG6EZ0SNNI3BQ6SK7XVE'
  SubmitTime =  u'2014-07-26T23:57:00Z'
  WorkerId =  u'A37AEUHK9BXWJT'

class AssignmentFactory(factory.Factory):

  class Meta:
    model = mturk.Assignment

  hit = factory.SubFactory(HITFactory)
  boto_assignment = factory.SubFactory(BotoAssignmentFactory)

class WorkerFactory(factory.Factory):

  class Meta:
    model = mturk.Worker

  id = factory.Sequence(lambda n: 'worker%d' % n)