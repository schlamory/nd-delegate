import factory
import datetime
from ... import transcribe

class TranscriptionTaskPageFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscriptionTaskPage

  pdf_page = None
  hit_id = factory.Sequence(lambda n: "hit_%d" % n)
  bucket_key = factory.Sequence(lambda n: "bucket_key_%d.pdf" % n)

class TranscriptionTaskFactory(factory.Factory):
  class Meta:
    model = transcribe.TranscriptionTask

  name = factory.Sequence(lambda n: "task_%d" % n)

  @factory.post_generation
  def pages(self, create, extracted, **kwargs):
    PageFactory = TranscriptionTaskPageFactory
    if not extracted:
      self.pages = [PageFactory(bucket_key=self.name + "/%d.pdf" % i) for i in range(5)]
