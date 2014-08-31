from mock import MagicMock, patch
import pytest
import unittest

from .. import transcribe
from ..transcribe import TranscriptionTask, TranscribePageTask

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
      assert task.name == "baz"
      subtasks = task.children
      assert [subtask.pdf_page for subtask in task.children] == ["pdf1", "pdf3", "pdf3"]
      assert [subtask.page_number for subtask in task.children] == [1, 2, 3]

  def test_submit(self):
    task = TranscriptionTaskFactory()
    with patch.object(transcribe.TranscribePageTask, "submit"):
      task.submit()
      for child in task.children:
        child.submit.assert_called_with()

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
    task = TranscribePageTaskFactory(pdf_page = mock_page)
    with patch.object(transcribe, "bucket") as mock_bucket:
      mock_key = MagicMock()
      mock_bucket.new_key = MagicMock(return_value = mock_key)
      task.post_page()
      mock_bucket.new_key.assert_called_with(task.s3_key_name)
      mock_page.save_to_s3.assert_called_with(mock_key)



class TranscribePageAttempt(unittest.TestCase):

  def test_factory(self):
    task = TranscribePageAttemptFactory()
    assert task.hit is not None
    assert task.parent is not None
