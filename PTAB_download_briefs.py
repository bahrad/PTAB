# pip install pdfplumber -q

import pandas as pd
import itertools
from pandas import DataFrame
import requests
import io
import pdfplumber
import sys

# sys.argv[0] is script name
infile = sys.argv[1]    # should be one column with a header
outfile = sys.argv[2]
startind = int(sys.argv[3])  # first index in Proceedings to process
endind = int(sys.argv[4])    # last index in Proceedings (if -1 go to end)
try:
    onlydo = sys.argv[5]    # 'Petitions', 'Responses', or 'Decisions'
except:                     # if only doing one kind
    onlydo = False

Proceedings = pd.read_csv(infile)
if endind == 0:
    Proceedings = Proceedings[Proceedings.columns[0]].to_list()[startind:]
else:
    Proceedings = Proceedings[Proceedings.columns[0]].to_list()[startind:endind+1]


def extractPDFText(pdfFile):
    # Find the first page with a numeric page number
    numpages = len(pdfFile.pages)
    if numpages < 11:
        start_page = 0
        end_page = min(10, numpages-1)
    elif numpages < 24:
        start_page = 0
        end_page = min(23, numpages-1)
    else:
        start_page = 0
        end_page = min(30, numpages-1)
    textr = ''
    for page in range(start_page,end_page+1):
        try:
            text = (pdfFile.pages[page]).extract_text()
            textr += text if text else ''
        except:
            pass

    return textr.replace('\n','')

Petitions = {}
Responses = {}
Decisions = {}
Petitions_json = {}
Responses_json = {}
Decisions_json = {}

for procnum in Proceedings:
    print('Processing', procnum)

    if (onlydo == 'Petitions') or (onlydo is False):
        rdoc = requests.get(f"https://developer.uspto.gov/ptab-api/documents?documentTypeName=Petition&proceedingNumber={procnum}")
        Petitions_json[procnum] = rdoc.json()['results']
        if rdoc.json()['recordTotalQuantity'] == 0:
            num_records = 0
            Petitions[procnum] = 'ERROR_NO_RECORDS_FOUND'
        else:
            doc_id = [result['documentIdentifier'] \
                      for result in Petitions_json[procnum] \
                      if result['documentTypeName']=='Petition']
            num_records = len(doc_id)
            if num_records == 0:
                doc_id = [result['documentIdentifier'] \
                          for result in Petitions_json[procnum] \
                          if ('Petition' in result['documentTitleText'] \
                              and not 'Rehear' in result['documentTitleText'])]
                num_records = len(doc_id)
            if num_records > 1:
                doc_id = [result['documentIdentifier']
                          for result in Petitions_json[procnum]
                          if result['documentTypeName']=='Petition' and
                          'Petition' in result['documentTitleText']]
                num_records = len(doc_id)
            if num_records == 1:
                doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                Petitions[procnum] = extractPDFText(pdfFile)
            elif num_records > 1:
                doc_id = [result['documentIdentifier']
                          for result in Petitions_json[procnum]
                          if (result['documentTypeName']=='Petition') \
                          and ('Petition' in result['documentTitleText']) \
                          and ('Corrected' in result['documentTitleText'])]
                num_records = len(doc_id)
                if num_records == 0:
                    doc_id = [result['documentIdentifier'] \
                              for result in Petitions_json[procnum] \
                              if ('Petition' in result['documentTitleText'] \
                                  and 'Corrected' in result['documentTitleText'])]
                num_records = len(doc_id)
                if num_records == 1:
                    doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                    pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                    Petitions[procnum] = extractPDFText(pdfFile)                
                else:
                    Petitions[procnum] = f'ERROR_TOO_MANY_RECORDS_RETURNED_{num_records}'
            elif num_records == 0:
                Petitions[procnum] = 'ERROR_NO_RECORD_RETURNED'

    if (onlydo == 'Responses') or (onlydo is False):
        rdoc1 = requests.get(f"https://developer.uspto.gov/ptab-api/documents?documentTypeName=Response&proceedingNumber={procnum}")
        rdoc2 = requests.get(f"https://developer.uspto.gov/ptab-api/documents?documentTypeName=Opposition&proceedingNumber={procnum}")
        Responses_json[procnum] = rdoc1.json()['results'] + rdoc2.json()['results']
        if (rdoc1.json()['recordTotalQuantity'] == 0) and (rdoc2.json()['recordTotalQuantity'] == 0):
            num_records = 0
            Responses[procnum] = 'ERROR_NO_RECORDS_FOUND'
        else:
            doc_id = [result['documentIdentifier']
                      for result in Responses_json[procnum] \
                      if 'Preliminary Response' in result['documentTypeName']]
            num_records = len(doc_id)
            if num_records == 0:
                doc_id = [result['documentIdentifier']
                          for result in Responses_json[procnum]
                          if ('Response' in result['documentTypeName'] or 'Opposition' in result['documentTypeName'] \
                          or result['documentTypeName']=='Notice') \
                          and ('Preliminary Response' in result['documentTitleText']) \
                          and ('Motion' not in result['documentTitleText'])]
                num_records = len(doc_id)
            if num_records == 1:
                doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                Responses[procnum] = extractPDFText(pdfFile)
            elif num_records > 1:
                doc_id = [result['documentIdentifier']
                          for result in Responses_json[procnum] \
                          if (result['documentTypeName']=='Response' or result['documentTypeName']=='Opposition') \
                          and ('Preliminary Response' in result['documentTitleText'] \
                               and 'Motion' not in result['documentTitleText'] \
                               and 'Exhibit' not in result['documentTitleText'])]
                num_records = len(doc_id)
                if num_records == 1:
                    doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                    pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                    Responses[procnum] = extractPDFText(pdfFile),
                elif num_records > 1:
                    doc_id = [result['documentIdentifier'] \
                              for result in Responses_json[procnum] \
                              if ('Preliminary Response' in result['documentTitleText']) \
                              and ('Corrected' in result['documentTitleText'])]
                    num_records = len(doc_id)
                    if num_records > 1:
                        Responses[procnum] = f'WARNING_TOO_MANY_RECORDS_RETURNED_{num_records}_'
                        doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                        pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                        Responses[procnum] += extractPDFText(pdfFile)
                elif num_records == 0:
                    doc_id = [result['documentIdentifier'] \
                              for result in Responses_json[procnum] \
                              if 'Preliminary Response' in result['documentTitleText']]
                    num_records = len(doc_id)
                    if num_records == 0:
                        doc_id = [result['documentIdentifier'] \
                                  for result in Responses_json[procnum] \
                                  if ('Response' in result['documentTypeName']) \
                                  and ('Motion' not in result['documentTitleText']) \
                                  and ('Exhibit' not in result['documentTitleText'])]
                        num_records = len(doc_id)
                        if num_records > 1:
                            doc_id = [result['documentIdentifier'] \
                                      for result in Responses_json[procnum] \
                                      if ('Response' in result['documentTypeName']) \
                                      and ('Response' in result['documentTitleText']) \
                                      and ('Exhibit' not in result['documentTitleText'])]
                            num_records = len(doc_id)
                    if num_records == 1:
                        doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                        pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                        Responses[procnum] = extractPDFText(pdfFile)
                    elif num_records == 0:
                        Responses[procnum] = 'ERROR_NO_RECORD_RETURNED'
                    elif num_records > 1:
                        doc_id = [result['documentIdentifier'] \
                                  for result in Responses_json[procnum] \
                                  if ('Preliminary Response' in result['documentTitleText']) \
                                  and ('Corrected' in result['documentTitleText'])]
                        num_records = len(doc_id)
                        if num_records == 0:
                            doc_id = [result['documentIdentifier'] \
                                      for result in Responses_json[procnum] \
                                      if ('Response' in result['documentTypeName']) \
                                      and ('Response' in result['documentTitleText']) \
                                      and ('Exhibit' not in result['documentTitleText'])]
                            num_records = len(doc_id)
                        if num_records > 1:
                            Responses[procnum] = f'WARNING_TOO_MANY_RECORDS_RETURNED_{num_records}_'
                            doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                            pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                            Responses[procnum] += extractPDFText(pdfFile)
                        if num_records == 1:
                            doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                            pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                            Responses[procnum] = extractPDFText(pdfFile)
                        
            elif num_records == 0:
                Responses[procnum] = 'ERROR_NO_RECORD_RETURNED'

    if (onlydo == 'Decisions') or (onlydo is False):
        rdoc = requests.get(f"https://developer.uspto.gov/ptab-api/documents?documentTypeName=Decision&proceedingNumber={procnum}")
        Decisions_json[procnum] = rdoc.json()['results']
        if rdoc.json()['recordTotalQuantity'] == 0:
            num_records = 0
            rdoc = requests.get(f"https://developer.uspto.gov/ptab-api/documents?documentTypeName=Notice&proceedingNumber={procnum}")
            doc_id = [result['documentIndentifier'] for result in rdoc \
                      if ('Institution' in result['documentTitleText'] \
                      and 'Decision' in result['documentTitleText']) \
                      and ('Denying Rehearing' not in result['documentTitleText'] \
                           or 'Seal' not in result['documentTitleText'] \
                           or 'Motion' not in result['documentTitleText'])]
            num_records = len(doc_id)
            if (num_records == 0) or (num_records > 1):
                Decisions[procnum] = 'ERROR_NO_RECORDS_FOUND'
            else:
                doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                Decisions[procnum] = extractPDFText(pdfFile)
        else:
            doc_id = [result['documentIdentifier']
                      for result in Decisions_json[procnum]
                      if result['documentTypeName']=='Institution Decision']
            num_records = len(doc_id)
            if num_records > 1:
                doc_id = [result['documentIdentifier']
                          for result in Decisions_json[procnum]
                          if (result['documentTypeName']=='Institution Decision' \
                              or result['documentTypeName']=='Decision Granting Institution' \
                              or result['documentTypeName']=='Decision Denying Institution') \
                          and ('Decision' in result['documentTitleText'])]
                num_records = len(doc_id)
                if num_records > 1:
                    doc_id = [result['documentIdentifier']
                              for result in Decisions_json[procnum]
                              if (result['documentTypeName']=='Institution Decision' \
                                  or result['documentTypeName']=='Decision Granting Institution' \
                                  or result['documentTypeName']=='Decision Denying Institution') \
                              and ('Decision' in result['documentTitleText'] and not 'Rehearing' in result['documentTitleText'])]
                    num_records = len(doc_id)
            if num_records == 1:
                doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                Decisions[procnum] = extractPDFText(pdfFile)
            elif num_records > 1:
                Decisions[procnum] = f'ERROR_TOO_MANY_RECORDS_RETURNED_{num_records}'
            elif num_records == 0:
                doc_id = [result['documentIdentifier'] \
                          for result in Decisions_json[procnum] \
                          if ('Decision' in result['documentTitleText']) \
                          and ('Institution' in result['documentTitleText'])]
                num_records = len(doc_id)
                if num_records == 0:
                    Decisions[procnum] = 'ERROR_NO_RECORD_RETURNED'
                elif num_records == 1:
                    doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                    pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                    Decisions[procnum] = extractPDFText(pdfFile)                
                elif num_records > 1:
                    doc_id = [result['documentIdentifier'] \
                              for result in Decisions_json[procnum] \
                              if ('Decision' in result['documentTitleText']) \
                              and ('Institution' in result['documentTitleText']) \
                              and ('Rehearing' not in result['documentTitleText'])]
                    num_records = len(doc_id)
                    if num_records == 1:
                        doc = requests.get(f"https://developer.uspto.gov/ptab-api/documents/{doc_id[0]}/download",stream=True)
                        pdfFile = pdfplumber.open(io.BytesIO(doc.content))
                        Decisions[procnum] = extractPDFText(pdfFile)
                    else:
                        Decisions[procnum] = f'ERROR_TOO_MANY_RECORDS_RETURNED_{num_records}'
                
if onlydo == 'Petitions':
    ResultsDF = DataFrame.from_dict({key:[Petitions[key]]
                                     for key in Proceedings},
                                    orient='index',
                                    columns=['Petitions'])
elif onlydo == 'Responses':
    ResultsDF = DataFrame.from_dict({key:[Responses[key]]
                                     for key in Responses},
                                    orient='index',
                                    columns=['Responses'])
elif onlydo == 'Decisions':
    ResultsDF = DataFrame.from_dict({key:[Decisions[key]]
                                     for key in Proceedings},
                                    orient='index',
                                    columns=['Decisions'])
else:
    ResultsDF = DataFrame.from_dict({key:[Petitions[key], Responses[key], Decisions[key]]
                                     for key in Proceedings},
                                    orient='index',
                                    columns=['Petitions','Responses','Decisions'])

ResultsDF = ResultsDF.reset_index().rename(columns={'index':'Proceeding'})

ResultsDF.to_csv(outfile, sep='\t', index=False)
