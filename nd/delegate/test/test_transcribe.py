from mock import MagicMock, patch
import pytest
import unittest

from .. import transcribe
from ..transcribe import TranscriptionTask

from factories.mturk import (
  RequestFactory,
  BotoHITFactory, HITFactory,
  BotoAssignmentFactory, AssignmentFactory,
  WorkerFactory
  )

from factories.transcribe import (
  TranscriptionTaskFactory
  )

class TestTask(unittest.TestCase):

  def test_create(self):
    mockPdf = MagicMock()
    mockPdf.get_pages = MagicMock(return_value = ["pdf1", "pdf3", "pdf3"])
    with patch.object(transcribe.pdf, 'load', return_value=mockPdf) as mock_load:
      path = "foo/bar/baz.pdf"
      task = TranscriptionTask.create(path)
      assert task.name == "baz"
      assert [subtask.pdf_page for subtask in task.subtasks] == ["pdf1", "pdf3", "pdf3"]

