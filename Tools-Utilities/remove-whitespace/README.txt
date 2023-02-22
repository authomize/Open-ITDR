# Remove whitespace utility

#Strips whitepace from right and left of each column on every row. Doesn't remove whitespace inbetween text.

#Example Command with 1 sheet:
python remove_whitespace.py "sample_whitespace_data.xlsx" PrivMembers

#Example Command with all sheets:
python remove_whitespace.py "sample_whitespace_data.xlsx" PrivMembers --sheet2 PrivOwner --sheet3 MemberData --sheet4 GroupOwner --sheet5 EmployeeData
