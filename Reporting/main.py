import arcpy
import os
import logging_code
import csv
import time
import sys
from multiprocessing import Pool, Manager

'''
Modules needed for this program (in same dir):
1: __init__.py
2: ESRI_PROD.sde
3: logging_code.py
'''

# Welcome
print("Please wait for configuration to set...")

# Set logger
logger = logging_code.log_your_stuff('LeakSurvey.log')

# Set New env & workspace
env_var = os.getcwd() + "/" + "ESRI_PROD.sde"
arcpy.env.workspace = env_var
arcpy.env.overwriteOutput = True

# Set up ESRI DB Feature Classes
gas_district_sde = "ESRI_PROD.DBO.GasDistribution/ESRI_PROD.DBO.pse_gas_district"
grid_sde = "ESRI_PROD.DBO.GasDistribution/ESRI_PROD.DBO.gd_map_grid"
svc_sde = "ESRI_PROD.DBO.GasDistribution/ESRI_PROD.DBO.gd_service"
main_sde = "ESRI_PROD.DBO.GasDistribution/ESRI_PROD.DBO.gd_main"
riser_sde = "ESRI_PROD.DBO.GasDistribution/ESRI_PROD.DBO.gd_service_riser"
wssap_sde = r"O:\Casings\2019\ArcGISPro\LeakSurvey\LeakSurvey.gdb/WSSAP_2019_1"

# Make Feature Layer from ESRI DB Feature Classes
gas_dist = arcpy.MakeFeatureLayer_management(gas_district_sde)
service_stub = arcpy.MakeFeatureLayer_management(svc_sde,where_clause="status = 'Existing' And route_world_id = 0 "
                                                                      "And pse_classification = 'Stub' "
                                                                      "And actual_length >= 3")
main = arcpy.MakeFeatureLayer_management(main_sde, where_clause="status = 'Existing' And route_world_id = 0 "
                                                                "And mop IS NULL")
supply = arcpy.MakeFeatureLayer_management(main, where_clause="pressure = 'HP'")
s250 = arcpy.MakeFeatureLayer_management(main_sde, where_clause="status = 'Existing' And route_world_id = 0 "
                                                                "And mop >= 250 And pressure = 'HP'")
wssap = arcpy.MakeFeatureLayer_management(wssap_sde)
riser = arcpy.MakeFeatureLayer_management(riser_sde, where_clause="status = 'Existing' And location_world_id = 0")


def get_count(in_fc, sel_fc, sel_type="NEW_SELECTION"):

    arcpy.SelectLayerByLocation_management(in_layer=in_fc, overlap_type="INTERSECT",
                                           select_features=sel_fc, selection_type=sel_type)
    num = int(arcpy.GetCount_management(in_fc)[0])

    return num


def clip_data(in_fc, sel_clip_fc, out_fc):
    num = 0

    arcpy.SelectLayerByLocation_management(in_fc, overlap_type="INTERSECT",
                                           select_features=sel_clip_fc, selection_type='NEW_SELECTION')

    arcpy.Clip_analysis(in_features=in_fc, clip_features=sel_clip_fc,
                        out_feature_class=out_fc)
    with arcpy.da.SearchCursor(out_fc, ['SHAPE@LENGTH']) as cursor:
        for item in cursor:
            num += item[0]

    return int(num)


def add_map(table, map_type, dictionary):
    try:
        quicklist = []

        with arcpy.da.SearchCursor(table, [map_type]) as mapcur:
            for item in mapcur:
                if item[0] != '':
                    quicklist.append(item[0])

            dictionary[map_type] = quicklist
    except arcpy.ExecuteError:
        print(arcpy.GetMessages())


def map_report(mapname, list):

    # Set New env & workspace
    env_var = os.getcwd() + "/" + "ESRI_PROD.sde"
    arcpy.env.workspace = env_var
    arcpy.env.overwriteOutput = True

    # Store dict values
    DataDict = {}
    DataDict['Map Name'] = mapname

    # Create FC for each Map Grid
    map = arcpy.MakeFeatureLayer_management(in_features=grid_sde, out_layer='MapGrid',
                                      where_clause="map_name = '{}'".format(mapname))

    # Clip BD within Plat
    arcpy.SelectLayerByLocation_management(in_layer=gas_dist, overlap_type="INTERSECT",
                                           select_features=map, selection_type="NEW_SELECTION")
    arcpy.Clip_analysis(in_features=gas_dist, clip_features=map,
                        out_feature_class='in_memory\BDClipped')

    # BD Count
    BD_Count = int(arcpy.GetCount_management('in_memory\BDClipped')[0])

    # Svc Stub Count
    Svc_Stub_Count = get_count(in_fc=service_stub, sel_fc=map)

    # BD Svc Stub Count
    BD_Svc_Stub_Count = get_count(in_fc=service_stub, sel_fc='in_memory\BDClipped',
                                  sel_type="SUBSET_SELECTION")

    # Supply within Plat
    Supply_withinPlat = clip_data(in_fc=supply, sel_clip_fc='MapGrid',
                                  out_fc='in_memory\SupplyClipped')
    # Supply BD
    Supply_withinBD = clip_data(in_fc='in_memory\SupplyClipped', sel_clip_fc='in_memory\BDClipped',
                                out_fc='in_memory\SupplyBDClipped')

    # s250 within Plat
    s250_withinPlat = clip_data(in_fc=s250, sel_clip_fc=map,
                                out_fc='in_memory\s250Clipped')

    # PRB Main total (All Main (no filter on pressure) within BD)
    PRB_Main_Total = clip_data(in_fc=main, sel_clip_fc='in_memory\BDClipped',
                               out_fc='in_memory\PRBMain')

    # Plat Main Total (All Main (no filter) within Plat
    PlatMainTotal = clip_data(in_fc=main, sel_clip_fc=map,
                              out_fc='in_memory\PlatMain')

    # Plat Main minus PRB Main
    PlatMinPRB = PlatMainTotal - PRB_Main_Total

    # STW2 count
    arcpy.SelectLayerByAttribute_management(wssap, where_clause="CATEGORY = 'PR' Or CATEGORY = 'SR'")
    stw2 = get_count(wssap, map, sel_type="SUBSET_SELECTION")

    # STW count
    arcpy.SelectLayerByAttribute_management(wssap, where_clause="CATEGORY = 'ILS'")
    stw = get_count(wssap, map, sel_type="SUBSET_SELECTION")

    # Svc Riser within Plat Count
    svc_riser_ct = get_count(in_fc=riser, sel_fc=map)

    # BD Svc Riser Count ( all svc risers within the bd within the plat)
    bd_svc_riser = get_count(in_fc=riser, sel_fc='in_memory\BDClipped', sel_type="SUBSET_SELECTION")

    DataDict['BD Count'] = BD_Count
    DataDict['BD Svc Stub Count'] = BD_Svc_Stub_Count
    DataDict['BD Svc Riser Count'] = bd_svc_riser
    DataDict['Supply BD'] = Supply_withinBD
    DataDict['S250 within Plat'] = s250_withinPlat
    DataDict['PRB Main Total'] = PRB_Main_Total
    DataDict['Plat Main Total'] = PlatMainTotal
    DataDict['Plat Main minus PRB Main'] = PlatMinPRB
    DataDict['Supply within Plat'] = Supply_withinPlat
    DataDict['Svc Stub Count'] = Svc_Stub_Count
    DataDict['Svc Riser Count'] = svc_riser_ct
    DataDict['STW2 Count'] = stw2
    DataDict['STW Count'] = stw

    print(DataDict)
    list.append(DataDict)
    return DataDict


def secondary_report(mapname, list):

    # Store dict values
    DataDict = {}

    # Create FC for each Map Grid
    map = arcpy.MakeFeatureLayer_management(in_features=grid_sde, out_layer='MapGrid',
                                      where_clause="map_name = '{}'".format(mapname))

    # Get Count for STW2
    # STW2 count
    arcpy.SelectLayerByAttribute_management(wssap, where_clause="CATEGORY = 'PR' Or CATEGORY = 'SR'")
    stw2 = get_count(wssap, map, sel_type="SUBSET_SELECTION")

    DataDict['Map Name'] = mapname
    DataDict['STW2 Count'] = stw2

    print(DataDict)

    list.append(DataDict)


def multi_processor(maptype, return_list):
    try:
        p = Pool(processes=15)
        for item in mapDict[maptype]:
            # for item in maptest:
            logger.info(f"starting {item}")
            p.apply_async(map_report, args=(item, return_list))
        p.close()
        p.join()

    except:
        logger.info("issue with multiprocessor...")


def dict_to_csv(reportname, return_list):

    with open(reportname, 'w', newline='') as w:

        fieldnames = ['Map Name',
                      'BD Count',
                      'BD Svc Stub Count',
                      'BD Svc Riser Count',
                      'Supply BD',
                      'S250 within Plat',
                      'PRB Main Total',
                      'Plat Main Total',
                      'Plat Main minus PRB Main',
                      'Supply within Plat',
                      'Svc Stub Count',
                      'Svc Riser Count',
                      'STW2 Count',
                      'STW Count',
                      ]

        writer = csv.DictWriter(w, fieldnames)
        writer.writeheader()
        for item in return_list:
            print(item)
            writer.writerow(item)


def secondary_dict_to_csv(reportname, return_list):

    with open(reportname, 'w', newline='') as w:

        fieldnames = ['Map Name',
                      'STW2 Count',
                      ]

        writer = csv.DictWriter(w, fieldnames)
        writer.writeheader()
        for item in return_list:
            # print(item)
            writer.writerow(item)


if __name__ == "__main__":

    # Welcome
    print("Welcome to the Leak Survey Map Production Program!")

    # Start Clock
    start = time.time()
    # logger.info("Start Time.")

    # Map Types
    primary = 'Primary'
    primary_detail = 'Primary_Detail'
    secondary = 'Secondary'
    transmission = 'Transmission'
    jp_transmission = 'JPTransmission'
    other = 'Other'
    maptypes = [primary, primary_detail, secondary, jp_transmission, other]

    # Set New env & workspace
    env_var = os.getcwd() + "/" + "ESRI_PROD.sde"
    arcpy.env.workspace = env_var
    arcpy.env.overwriteOutput = True

    # Map Order Table Set-up
    leaksurvey_gdb = r"O:\Casings\ArcGISPro\LeakSurveyMapping.gdb"
    ExcelMapOrder = r"O:\Casings\2019\MapOrder_Dynamic\MapOrder.xlsx"
    MapOrderTable = os.path.join(leaksurvey_gdb, "MapOrderTable")

    # Map Order to Dict
    mapDict = {}
    for item in maptypes:
        add_map(MapOrderTable, item, mapDict)
    # logger.info("Map Dict Creation complete.")

    # Store dict values
    MapListofDics = []

    # Processing User Request
    while True:
        UserResponse = int(input("Which Report(s) do you want to run? Enter your request based on the following: \n"
                                 "1: JPTransmission \n"
                                 "2: Primary & Primary Detail \n"
                                 "3: Secondary \n"
                                 "4: Other \n"
                                 "5: exit \n"))
        if UserResponse == 1:
            manager = Manager()
            return_list = manager.list()
            multi_processor(jp_transmission, return_list)
            dict_to_csv(f'{jp_transmission}_Report.csv', return_list)
            logger.info('Report Generated.')
            continue
        elif UserResponse == 2:
            manager = Manager()
            return_list = manager.list()
            multi_processor(primary, return_list)
            multi_processor(primary_detail, return_list)
            dict_to_csv(f'{primary}_Report.csv', return_list)
            logger.info('Report Generated.')
            continue
        elif UserResponse == 3:
            list = []
            for item in mapDict['Secondary']:
                secondary_report(item, list)
            secondary_dict_to_csv(f'{secondary}_Report.csv', list)
            logger.info('Report Generated.')
            continue
        elif UserResponse == 4:
            manager = Manager()
            return_list = manager.list()
            multi_processor(other, return_list)
            dict_to_csv(f'{other}_Report.csv', return_list)
            logger.info('Report Generated.')
            continue
        elif UserResponse == 5:
            logger.info('Thank you for using the Report Program.')
            sys.exit()
        else:
            logger.info('Please enter a valid number.')

        end = time.time()
        logger.info(f"Total Generating Time: {(end - start)/60} Minutes")
