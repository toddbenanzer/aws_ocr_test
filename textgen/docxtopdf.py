from pdfrw import PdfWriter
import sys
import os
from pdf2image import convert_from_path



def docx_to_pdf(docx_filename):
    cmd = r'''cd "C:\developer\aws_ocr_test\created_docs"'''
    os.system(cmd)
    cmd = '''"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf {0}'''.format(docx_filename)
    os.system(cmd)


def pdf_to_image(pdf_filename, dpi=60):
    output_file = os.path.join(r'C:\developer\aws_ocr_test\created_docs', str(pdf_filename.replace('.pdf', '.png')))
    print(output_file)
    images = convert_from_path(pdf_filename, dpi=dpi, output_folder=None, first_page=None, last_page=None, fmt='png',
                      thread_count=1, userpw=None, use_cropbox=False, strict=False, transparent=False,
                      single_file=False, output_file=output_file,
                      poppler_path=r'C:\developer\aws_ocr_test\poppler\bin', grayscale=False, size=None)
    for i, image in enumerate(images):
        save_file = output_file.replace('.png', '{0:03d}.png'.format(i))
        image.save(save_file)


def docx_to_image(docx_filename):
    docx_to_pdf(docx_filename)
    #pdf_to_image(docx_filename.replace('.docx', '.pdf'), dpi=60)


if __name__ == '__main__':
    os.chdir(r'C:\developer\aws_ocr_test\textgen')
    # print('Creating PDF')
    # docx_to_pdf("text.docx")
    # print('Creating Images')
    # pdf_to_image('text.pdf')
    print('Creating PDF')
    docx_to_image("text.docx")

