import factory
import datetime
from ... import transcribe

class TranscriptionTaskFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscriptionTask

  name = factory.Sequence(lambda n: "task_%d" % n)

  @factory.post_generation
  def children(self, create, extracted, **kwargs):
    if not extracted:
      self.children = [TranscribePageTaskFactory(page_number=i, pdf_page="pdf%i" % i)
                                                                              for i in range(5)]

class TranscribePageTaskFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscribePageTask

  pdf_page = None
  page_number = factory.Sequence(lambda n: n)
  parent = None

  @factory.post_generation
  def parent(self, create, extracted, **kwargs):
    if self.parent is None:
      self.parent = TranscriptionTaskFactory(children = [self])

  @factory.post_generation
  def children(self, create, extracted, **kwargs):
    if not extracted:
      self.children = [TranscribePageAttemptFactory(parent=self)]


class TranscribePageAttemptFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscribePageAttempt

  hit_id = factory.Sequence(lambda n: "hit_%n")
  parent = None

  @factory.post_generation
  def parent(self, create, extracted, **kwargs):
    if not self.parent:
      self.parent = TranscribePageTaskFactory(children = [self])