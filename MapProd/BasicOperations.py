import arcpy
import os
import logging_code

# Set logger
logger = logging_code.log_your_stuff('LeakSurveyMapping.log')


def refresh_table(gdb, excel, table):
    '''
    Any Updates that happen to the xlsx file are then translated into a overwritten table 'MapOrderTable'
    That is configured and joined within the ArcGIS Pro Project.
    '''

    # Create table from Excel File (First update from map order)
    # logger.info("Refreshing table...")
    arcpy.ExcelToTable_conversion(excel,
                                  os.path.join(gdb, table))
    # logger.info("Table Refresh Complete. ")


def LeakSurvey_ExportToPDF(project, month, year, mapName, export_path):

    # Layouts & Maps
    mapLayout = project.listLayouts(f'{mapName}')[0]
    ProMap = project.listMaps(f'{mapName}')[0]

    # Refresh mapSeries
    mapLayout.mapSeries.refresh()

    try:
        # Transmission Settings
        if mapName == 'Transmission':
            for item in mapLayout.listElements('TEXT_ELEMENT'):
                if item.name == 'MapTitle':
                    item.text = f'Leak Survey & Patrol'
        # Primary/Primary Detail Settings
        elif mapName == 'Primary' or mapName == 'Primary Detail':
            for item in mapLayout.listElements('TEXT_ELEMENT'):
                if item.name == 'MapTitle':
                    item.text = f'{month} Leak Survey {year}'
            for layer in ProMap.listLayers():
                if layer.isFeatureLayer:
                    if layer.name == 'Gas District Border' or layer.name == 'Gas District Fill':
                        layer.definitionQuery = f"survey_month = '{month}'"
        # Secondary/Secondary Detail Settings
        elif mapName == 'Secondary' or mapName == 'Secondary Detail':
            for item in mapLayout.listElements('TEXT_ELEMENT'):
                if item.name == 'MapTitle':
                    item.text = f'{month} Leak Survey {year}'
        # Other Settings
        elif mapName == 'Other':
            # Mapping Questions
            whattitle = input("Would you like to specify a different title than usual? (Y/N)")
            whatsetting = int(input("What map-type setting would you like? \n"
                                    "1: Primary \n"
                                    "2: Secondary \n"))
            wssapQ = int(input("Would you like the WSSAP layer on or off? \n"
                               "1: On \n"
                               "2: Off \n"))
            whatbusdists = int(input("Show all bds or just for the month? \n"
                                     "1: all \n"
                                     "2: month \n"))

            # Add answers to Mapping Schema
            for item in mapLayout.listElements('TEXT_ELEMENT'):
                if item.name == 'MapTitle':
                    if whattitle.lower() == 'n':
                        item.text = f'{month} Leak Survey {year}'
                    elif whattitle.lower() == 'y':
                        newtitle = input("Please type new title...")
                        item.text = f'{newtitle}'
            for layer in ProMap.listLayers():
                if layer.name == 'Gas District Border' or layer.name == 'Gas District Fill':
                    if whatsetting == 1:
                        if whatbusdists == 1:
                            layer.definitionQuery = "survey_month IS NOT NULL"
                        elif whatbusdists == 2:
                            layer.definitionQuery = f"survey_month = '{month}'"
                    elif whatsetting == 2:
                        layer.visible = False
                elif layer.name == 'WSSAP':
                    if wssapQ == 2:
                        layer.visible = False

        else:
            print("Not a valid mapName...")

    except arcpy.ExecuteError:
        logger.error(arcpy.GetMessages())

    # Set map series location and export
    print(f"Initiating Map Series to pdf for {mapName}...")
    try:
        pdfExportType = int(input("All maps in one Single or Multiple PDF's? \n"
                                      "1: Single PDF \n"
                                      "2: Multiple PDF's \n"))
        s_or_m = ''
        if pdfExportType == 1:
            s_or_m = 'PDF_SINGLE_FILE'
        if pdfExportType == 2:
            s_or_m = 'PDF_MULTIPLE_FILES_PAGE_NAME'

        pagesPDF = os.path.join(export_path, f"{mapName}.pdf")
        mapLayout.mapSeries.exportToPDF(out_pdf=pagesPDF,
                                        page_range_type="ALL",
                                        resolution=350,
                                        image_quality="BEST",
                                        embed_fonts=True,
                                        multiple_files=s_or_m)
    except Exception as e:
        print(e)
    except arcpy.ExecuteError:
        logger.error(arcpy.GetMessages())

    print("pdf creation complete!")
    print(f"Maps exported here: \n"
          f"{export_path}")

