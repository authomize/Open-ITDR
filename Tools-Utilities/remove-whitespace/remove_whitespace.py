
import pandas as pd
import sys
import argparse

parser = argparse.ArgumentParser(description='Removes whitespace from left and right side of every column and row including headers')

parser.add_argument('file', nargs='+', help='Required: filename.xlsx')
parser.add_argument('sheet1', nargs='+', help='Required: Name of sheet')
parser.add_argument('--sheet2', nargs='?', help='Name of sheet')
parser.add_argument('--sheet3', nargs='?', help='Name of sheet')
parser.add_argument('--sheet4', nargs='?', help='Name of sheet')
parser.add_argument('--sheet5', nargs='?', help='Name of sheet')


args = parser.parse_args()
print(args)
doc_path = args.file[0]
sheet1 = args.sheet1[0]

doc1 = pd.read_excel(doc_path, sheet_name=sheet1)

if (parser.parse_args().sheet2 != None):
    doc2 = pd.read_excel(doc_path, sheet_name = parser.parse_args().sheet2)
else:
    doc2 = pd.DataFrame()

if (parser.parse_args().sheet3 != None):
    doc3 = pd.read_excel(doc_path, sheet_name = parser.parse_args().sheet3)
else:
    doc3 = pd.DataFrame()

if (parser.parse_args().sheet4 != None):
    doc4 = pd.read_excel(doc_path, sheet_name = parser.parse_args().sheet4)
else:
    doc4 = pd.DataFrame()

if (parser.parse_args().sheet5 != None):
    doc5 = pd.read_excel(doc_path, sheet_name = parser.parse_args().sheet5)
else:
    doc5 = pd.DataFrame()

#strips every column header whitespace from front and end

doc1.columns = doc1.columns.str.strip()

if(parser.parse_args().sheet2 == None):
    pass
else:
    doc2.columns = doc2.columns.str.strip()

if(parser.parse_args().sheet3 == None):
    pass
else:
    doc3.columns = doc3.columns.str.strip()

if(parser.parse_args().sheet4 == None):
    pass
else:
    doc4.columns = doc4.columns.str.strip()
    
if(parser.parse_args().sheet5 == None):
    pass
else:
    doc5.columns = doc5.columns.str.strip()

#remove whitespace on both ends of every column and row
if(doc1.empty):
    pass
else:
    doc1 = doc1.applymap(lambda x: x.strip() if isinstance(x, str) else x)

if(doc2.empty):
    pass
else:
    doc2 = doc2.applymap(lambda x: x.strip() if isinstance(x, str) else x)

if(doc3.empty):
    pass
else:
    doc3 = doc3.applymap(lambda x: x.strip() if isinstance(x, str) else x)

if(doc4.empty):
    pass
else:
    doc4 = doc4.applymap(lambda x: x.strip() if isinstance(x, str) else x)

if(doc5.empty):
    pass
else:
    doc5 = doc5.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# save to Excel (xlsx) and overwrite any excisting removed_whitespace.xlsx
with pd.ExcelWriter("removed_whitespace.xlsx", mode = 'w') as writer:

# save to Excel (xlsx) and write sheets
    if(sheet1 != None):
        doc1.to_excel(writer, sheet_name = sheet1, index = False)
    if(parser.parse_args().sheet2 != None):
        doc2.to_excel(writer, sheet_name = parser.parse_args().sheet2, index = False)
    if(parser.parse_args().sheet3 != None):
        doc3.to_excel(writer, sheet_name = parser.parse_args().sheet3, index = False)
    if(parser.parse_args().sheet4 != None):
        doc4.to_excel(writer, sheet_name = parser.parse_args().sheet4, index = False)
    if(parser.parse_args().sheet5 != None):
        doc5.to_excel(writer, sheet_name = parser.parse_args().sheet5, index = False)