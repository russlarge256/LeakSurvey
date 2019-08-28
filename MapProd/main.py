import arcpy
import time
import sys
from BasicOperations import refresh_table
from BasicOperations import LeakSurvey_ExportToPDF

'''
Modules needed for this program:
1: __init__.py
2: BasicOperations.py
3: logging_code.py
'''


if __name__ == "__main__":

    print("Welcome to the Leak Survey Map Production Program.")
    print("Refreshing Modified Excel Table...")

    # Set env & workspace
    leaksurvey_gdb = r"O:\Casings\ArcGISPro\LeakSurveyMapping.gdb"
    arcpy.env.workspace = leaksurvey_gdb
    project = arcpy.mp.ArcGISProject(r"O:\Casings\ArcGISPro\LeakSurveyMapping.aprx")
    arcpy.env.overwriteOutput = True

    # Refresh Map order table from spreadsheet
    ExcelMapOrder = r"O:\Casings\2019\MapOrder_Dynamic\MapOrder.xlsx"
    MapOrderTable = "MapOrderTable"
    try:
        refresh_table(leaksurvey_gdb, ExcelMapOrder, MapOrderTable)
    except arcpy.ExecuteError:
        print("ERROR: Exclusive schema lock. please close other ESRI applications and restart this application.")
        sys.exit()

    # Layout names
    primary = 'Primary'
    prim_detail = 'Primary Detail'
    secondary = 'Secondary'
    sec_detail = 'Secondary Detail'
    transmission = 'Transmission'
    MapList = [primary, prim_detail, secondary, sec_detail, transmission]

    # Other
    other = 'Other'

    # variables
    whatmonth = input('Which Month is this for?')
    whatyear = '2019'
    export_path = input("Where do you want the maps exported to?")

    while True:
        UserResponse = int(input("Which Maps do you want to produce? Enter your request based on the following: \n"
                                 "1: Primary \n"
                                 "2: Primary Detail \n"
                                 "3: Secondary \n"
                                 "4: Secondary Detail \n"
                                 "5: Transmission \n"
                                 "6: All \n"
                                 "7: Other \n"
                                 "8: Exit Program \n"))

        if UserResponse == 1:
            LeakSurvey_ExportToPDF(project, whatmonth, whatyear, primary, export_path)
            continue
        elif UserResponse == 2:
            LeakSurvey_ExportToPDF(project, whatmonth, whatyear, prim_detail, export_path)
            continue
        elif UserResponse == 3:
            LeakSurvey_ExportToPDF(project, whatmonth, whatyear, secondary, export_path)
            continue
        elif UserResponse == 4:
            LeakSurvey_ExportToPDF(project, whatmonth, whatyear, sec_detail, export_path)
            continue
        elif UserResponse == 5:
            LeakSurvey_ExportToPDF(project, whatmonth, whatyear, transmission, export_path)
            continue
        elif UserResponse == 6:
            for item in MapList:
                LeakSurvey_ExportToPDF(project, whatmonth, whatyear, item, export_path)
            continue
        elif UserResponse == 7:
            LeakSurvey_ExportToPDF(project, whatmonth, whatyear, other, export_path)
            continue
        elif UserResponse == 8:
            print('Thank you for using the Leak Survey Map Production Program.')
            sys.exit()
        else:
            print('Please enter a valid number.')
