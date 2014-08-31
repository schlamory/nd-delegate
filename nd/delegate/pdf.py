from pyPdf.pdf import PdfFileWriter, PdfFileReader, PageObject
import StringIO, os, uuid
from reportlab.pdfgen import canvas


def load(file_path):
  return PdfFileReader(open(file_path, "r"))

# PdfFileReader patches
def get_pdf_pages(pdf):
  return [pdf.getPage(i) for i in range(pdf.getNumPages())]

PdfFileReader.get_pages = get_pdf_pages

# PageObject patches
def save_page(page, file_path):
  output = PdfFileWriter()
  output.addPage(page)
  f = open(file_path, "wb")
  output.write(f)
  f.close()

def save_page_to_s3_key(page, s3_key):
  name = str(uuid.uuid1()) + ".pdf"
  page.save(name)
  s3_key.set_contents_from_filename(name)
  os.unlink(name)

def add_annotation_to_page(pdf_page, annotation, fontsize=24, margin=20):
  # Adds an annotation at bottom-left of the page
  width = pdf_page.mediaBox.getWidth()
  height = pdf_page.mediaBox.getHeight()

  # Create background with annotation a lower-left
  io = StringIO.StringIO()
  can = canvas.Canvas(io)
  can.setPageSize([width, height + fontsize + margin])
  can.setFontSize(fontsize)
  can.drawString(margin, margin, annotation)
  can.save()

  io.seek(0) #move to the beginning of the StringIO buffer
  page_background = PdfFileReader(io).getPage(0)

  page_background.mergeTranslatedPage(pdf_page, ty=margin+fontsize, tx=0)

  return page_background

PageObject.save = save_page
PageObject.add_annotation = add_annotation_to_page
PageObject.save_to_s3 = save_page_to_s3_key
