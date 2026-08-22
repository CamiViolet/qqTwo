@rem Script: update_files.bat
@rem Description: This scripts updates the qqOne knowledge base kb0.
@rem
@rem Parameters:
@rem    <pattern> : specifies the PDF file to be taken from Downloads.

set base_dir=%~dp0

@rem Copy exported PDF from the Downloads folder to .\pdf.
python %base_dir%copy_pdf_from_downloads.py %1

@rem Export PDF files to text.
python %base_dir%pdf_to_text.py

@rem Get definition of synonyms from the manual comments
python %base_dir%\in_text_keywords.py

@rem @rem Update the Activities (.\activities folder)
@rem call %base_dir%create_topics.bat
call C:\Dev_Analisys\kb0\activities\manual_comments\run.bat

@rem Copy the Polarion export files from qpDoc .\polarion_exports to the qqOne knowledge base kb0.
python %base_dir%copy_polarion_exports.py

@rem Create a summary of all the activities of the knowledge base.
python %base_dir%activities_summary.py
