from mock import MagicMock, patch
import pytest
import unittest

from .. import transcribe
from ..transcribe import TranscriptionTask

from mturk_factory import (
                            RequestFactory,
                            BotoHITFactory, HITFactory,
                            BotoAssignmentFactory, AssignmentFactory,
                            WorkerFactory
                          )

class TestTask(unittest.TestCase):

  def test_create(self):
    mockPdf = MagicMock()
    mockPdf.get_pages = MagicMock(return_value = ["pdf1", "pdf3", "pdf3"])
    with patch.object(transcribe.pdf, 'load', return_value=mockPdf) as mock_load:
      path = "foo/bar/baz.pdf"
      task = TranscriptionTask.create(path)
      assert task.name == "baz"
      assert [page.pdf_page for page in task.pages] == ["pdf1", "pdf3", "pdf3"]

  def test_load(self):
    pass

  def test_save(self):
    pass

  def test_submit(self):
    pass

  def test_review(self):
    pass