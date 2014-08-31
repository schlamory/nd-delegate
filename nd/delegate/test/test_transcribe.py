from mock import MagicMock, patch
import unittest
from datetime import datetime, timedelta

from .. import transcribe
from ..transcribe import TranscriptionTask, TranscribePageTask, TranscribePageAttempt

from factories.mturk import (
  RequestFactory,
  BotoHITFactory, HITFactory,
  BotoAssignmentFactory, AssignmentFactory,
  WorkerFactory
  )

from factories.transcribe import (
  TranscriptionTaskFactory,
  TranscribePageTaskFactory,
  TranscribePageAttemptFactory
  )

class TestTranscriptionTask(unittest.TestCase):

  def test_factory(self):
    task = TranscriptionTaskFactory()
    assert task.name
    assert len(task.children) == 5

  def test_create(self):
    mockPdf = MagicMock()
    mockPdf.get_pages = MagicMock(return_value = ["pdf1", "pdf3", "pdf3"])
    mockPageTask = MagicMock()
    with patch.object(transcribe.pdf, 'load', return_value=mockPdf):
      path = "foo/bar/baz.pdf"
      task = TranscriptionTask.create(path)
      assert task.name == "transcribe_baz"
      subtasks = task.children
      assert [subtask.pdf_page for subtask in task.children] == ["pdf1", "pdf3", "pdf3"]
      assert [subtask.page_number for subtask in task.children] == [1, 2, 3]

  def test_submit(self):
    task = TranscriptionTaskFactory()
    with patch.object(transcribe.TranscribePageTask, "submit"):
      task.submit()
      for child in task.children:
        child.submit.assert_called_with()

  def test_serialize(self):
    task = TranscriptionTaskFactory()
    with patch.object(transcribe.TranscribePageTask, "to_dict"):
      with patch.object(transcribe.TranscribePageTask, "from_dict"):
        d = task.to_dict()
        deserialized = TranscriptionTask.from_dict(d)
        assert deserialized.name == task.name
        assert len(deserialized.children) == len(task.children)


class TestTranscribePageTask(unittest.TestCase):

  def test_factory(self):
    task = TranscribePageTaskFactory()
    assert task.page_number is not None
    assert task.parent.name
    assert len(task.children) == 1

  def test_submit(self):
    task = TranscribePageTaskFactory(children = [])
    task.children = []
    with patch.object(transcribe.TranscribePageTask, "post_page"):
      with patch.object(transcribe.TranscribePageAttempt, "submit"):
        task.submit()
        task.post_page.assert_called()
        assert len(task.children) == 1
        task.children[0].submit.assert_called_with()

  def test_post_page(self):
    mock_page = MagicMock()
    mock_annotated_page = MagicMock()
    mock_page.get_annotated_copy = MagicMock(return_value=mock_annotated_page)
    task = TranscribePageTaskFactory(pdf_page = mock_page)
    with patch.object(transcribe, "bucket") as mock_bucket:
      mock_key = MagicMock()
      mock_bucket.new_key = MagicMock(return_value = mock_key)
      task.post_page()
      mock_bucket.new_key.assert_called_with(task.s3_key_name)
      mock_page.get_annotated_copy.assert_called_with(task.validation_code)
      mock_annotated_page.save_to_s3.assert_called_with(mock_key)

  def test_serialize(self):
    task = TranscribePageTaskFactory()
    with patch.object(transcribe.TranscribePageTask, "page_url") as page_url_property:
      with patch.object(transcribe.TranscribePageAttempt, "to_dict"):
        page_url_property.__get__ = MagicMock(return_value="PAGE_URL")
        d = task.to_dict()
        deserialized = TranscribePageTask.from_dict(d)
        assert deserialized.page_number == task.page_number
        assert deserialized.validation_code == task.validation_code
        assert len(deserialized.children) == len(task.children)

class TestTranscribePageAttempt(unittest.TestCase):

  def test_factory(self):
    task = TranscribePageAttemptFactory()
    assert task.hit is not None
    assert task.parent is not None

  def test_submit(self):
    task = TranscribePageAttemptFactory()
    mock_request = MagicMock()
    with patch.object(transcribe.TranscribePageAttempt, "create_mturk_request",
                                                         return_value=mock_request):
      task.submit()
      task.create_mturk_request.assert_called()
      mock_request.submit.assert_called()

  def test_create_mturk_request(self):
    task = TranscribePageAttemptFactory()
    with patch.object(transcribe.TranscribePageTask, "page_url") as page_url_property:
      page_url_property.__get__ = MagicMock(return_value="PAGE_URL")
      request = task.create_mturk_request()
      assert request.title
      assert request.layout_id
      assert request.description
      assert request.keywords
      assert request.reward == 0.35
      assert request.lifetime == timedelta(days=7)
      assert request.duration == timedelta(hours=1)
      assert request.approval_delay == timedelta(days=1)
      assert request.layout_params == {"file_url":"PAGE_URL"}

  def test_serialize(self):
    task = TranscribePageAttemptFactory()
    task.hit = HITFactory(id = task.hit.id)
    d = task.to_dict()
    deserialized = TranscribePageAttempt.from_dict(d)
    assert deserialized.hit.id == task.hit.id

  def test_review(self):
    task = TranscribePageAttemptFactory()
    task.hit = HITFactory(id = task.hit.id, boto_hit = BotoHITFactory(HITStatus="Reviewable"))
    task.hit._assignments = [AssignmentFactory()]
    with patch.object(transcribe.mturk.Assignment, "approve"):
      task.review()
      task.hit.assignments[0].approve.assert_called_with()
