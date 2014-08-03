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
    assert len(task.subtasks)

  def test_create(self):
    mockPdf = MagicMock()
    mockPdf.get_pages = MagicMock(return_value = ["pdf1", "pdf3", "pdf3"])
    with patch.object(transcribe.pdf, 'load', return_value=mockPdf) as mock_load:
      path = "foo/bar/baz.pdf"
      task = TranscriptionTask.create(path)
      assert task.name == "baz"
      assert [subtask.pdf_page for subtask in task.subtasks] == ["pdf1", "pdf3", "pdf3"]
      assert [subtask.parent for subtask in task.subtasks] == [task, task, task]

class TestTranscribePageTask(unittest.TestCase):

  def test_factory(self):
    task = TranscribePageTaskFactory()
    assert task.page_number is not None
    assert task.parent.name
    assert len(task.subtasks) == 1

class TranscribePageAttempt(unittest.TestCase):

  def test_factory(self):
    task = TranscribePageAttemptFactory()
    assert task.pdf_url is not None
    assert task.hit is not None
    assert task.parent is not None
