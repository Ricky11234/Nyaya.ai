import os
os.environ["USER_AGENT"]="Mozilla/5.0"
from langchain_community.document_loaders import (TextLoader,PyMuPDFLoader,WebBaseLoader,CSVLoader)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document 
from pathlib import Path

class docuprocessor:
    def __init__(self,chunk_size=500,chunk_overlap=50):
        self.chunk_size=chunk_size
        self.chunk_overlap=chunk_overlap

    # URL loader
    def urlloader(self,urls:str)->list[Document]:
        try:
            loader=WebBaseLoader(urls)
            docu=loader.load()
            return docu
        except Exception as e:
            print(f"Error loading URL {urls}: {e}")
            return []

    # PDF loader
    def pdfloader(self,pdfs:str)->list[Document]:
        try:
            loader=PyMuPDFLoader(pdfs)
            doc=loader.load()
            return doc
        except Exception as e:
            print(f"Error loading PDF {pdfs}: {e}")
            return []

    # TXT loader
    def txtloader(self,txts:str)->list[Document]:
        try:
            loader=TextLoader(txts)
            doc=loader.load()
            return doc
        except Exception as e:
            print(f"Error loading TXT {txts}: {e}")
            return []

    # CSV loader
    def csvloader(self,csvs:str)->list[Document]:
        try:
            loader=CSVLoader(file_path=csvs)
            doc=loader.load()
            return doc
        except Exception as e:
            print(f"Error loading CSV {csvs}: {e}")
            return []

    # Load all documents
    def document_loader(self,srcs:list[str])->list[Document]:
        docs:list[Document]=[]

        for src in srcs:
            try:
                src=src.strip()

                if(src.startswith("https://") or src.startswith("http://")):
                    docs.extend(self.urlloader(src))

                else:
                    ext=Path(src).suffix.lower()

                    if(ext=='.pdf'):
                        docs.extend(self.pdfloader(src))

                    elif(ext==".txt"):
                        docs.extend(self.txtloader(src))

                    elif(ext==".csv"):
                        docs.extend(self.csvloader(src))

                    else:
                        raise ValueError(f"file type not supported:{src}")

            except Exception as e:
                print(f"Error processing source {src}: {e}")

        return docs

    # Split documents
    def docu_splitter(self,srcs:list[Document])->list[Document]:
        try:
            splitter=RecursiveCharacterTextSplitter(chunk_size=self.chunk_size,chunk_overlap=self.chunk_overlap)
            return splitter.split_documents(srcs)
        except Exception as e:
            print(f"Error splitting documents: {e}")
            return []

    # Complete processing pipeline
    def process(self,srcs:list[str])->list[Document]:
        try:
            docs=self.document_loader(srcs)
            return self.docu_splitter(docs)
        except Exception as e:
            print(f"Error in processing pipeline: {e}")
            return []