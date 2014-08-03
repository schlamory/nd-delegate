import factory
import datetime
from ... import transcribe

class TranscriptionTaskFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscriptionTask

  name = factory.Sequence(lambda n: "task_%d" % n)

  @factory.post_generation
  def subtasks(self, create, extracted, **kwargs):
    if not extracted:
      self.subtasks = [TranscribePageTaskFactory(parent=self, page_number=i) for i in range(5)]


class TranscribePageTaskFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscribePageTask

  pdf_page = None
  page_number = factory.Sequence(lambda n: n)
  parent = None

  @factory.post_generation
  def parent(self, create, extracted, **kwargs):
    if self.parent is None:
      self.parent = TranscriptionTaskFactory(subtasks = [self])

  @factory.post_generation
  def subtasks(self, create, extracted, **kwargs):
    if not extracted:
      pdf_url = "bucket/task_name/{0}.pdf".format(self.page_number)
      self.subtasks = [TranscribePageAttemptFactory(parent=self, pdf_url=pdf_url)]


class TranscribePageAttemptFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscribePageAttempt

  hit_id = factory.Sequence(lambda n: "hit_%n")
  pdf_url = "http://www.foo.com"
  parent = None

  @factory.post_generation
  def parent(self, create, extracted, **kwargs):
    if not self.parent:
      self.parent = TranscribePageTaskFactory(subtasks = [self])