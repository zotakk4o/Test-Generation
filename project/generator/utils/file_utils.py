from xml.etree.cElementTree import XML
import PyPDF2
import zipfile


class FileUtils:
    @staticmethod
    def get_docx_text(path):
        schemas = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        para = schemas + 'p'
        text = schemas + 't'
        """
        Take the path of a docx file as argument, return the text in unicode.
        """
        document = zipfile.ZipFile(path)
        xml_content = document.read('word/document.xml')
        document.close()
        tree = XML(xml_content)
        paragraphs = []
        for paragraph in tree.iter(para):
            texts = [node.text
                     for node in paragraph.iter(text)
                     if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)

    @staticmethod
    def read_file(path):
        with open(path, 'r') as f:
            return f.read()

    @staticmethod
    def get_file_config(file_storage):
        file_extension = file_storage.filename.split('.')[-1]
        file_name = 'temp.' + file_extension

        return file_name, file_extension

    @staticmethod
    def get_pdf_text(path):
        text = ""
        pdf = PyPDF2.PdfFileReader(open(path, 'rb'))
        for i in range(0, pdf.getNumPages()):
            text += pdf.getPage(i).extractText()
        text = text.replace("\xa0", " ").strip()
        return text
