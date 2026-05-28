# Import Python Libraries

import os
import sys
import csv

import arcpy

from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")


print("Python libraries imported.")
print("Spatial Analyst enabled.")

# Import custom Python toolboxes
# Update this path before running locally.

base_folder = r"<BASE_ARCGIS_FOLDER>"
toolbox_folder = os.path.join(base_folder, "Toolboxes")

arcpy.ImportToolbox(os.path.join(toolbox_folder, "Raster_Tools.pyt"), "raster_tools")

print("Custom Python toolboxes imported.")
print("Raster tools : raster_tools")

# Import custom Python toolboxes
base_folder    = r"C:\Users\Alexandra\Documents\ArcGIS"
toolbox_folder = os.path.join(base_folder, "Toolboxes")

arcpy.ImportToolbox(os.path.join(toolbox_folder, "Raster_Tools.pyt"), "raster_tools")

print("Custom Python toolboxes imported.")
print("Raster tools : raster_tools")

# Define project paths
project_name = "Queen_Usquepaug"
project_folder = os.path.join(base_folder, "Projects", project_name)

# Define geodatabases
project_gdb = os.path.join(project_folder, f"{project_name}.gdb")
temp_gdb    = os.path.join(project_folder, "Temp.gdb")

# Define output folders
outputs_folder = os.path.join(project_folder, "Outputs")
tables_folder  = os.path.join(outputs_folder, "Tables")
charts_folder  = os.path.join(outputs_folder, "Charts")

print("Project paths defined.")
print(f"Project folder : {project_folder}")
print(f"Project GDB    : {project_gdb}")
print(f"Temp GDB       : {temp_gdb}")
print(f"Tables folder  : {tables_folder}")
print(f"Charts folder  : {charts_folder}")

# Confirm Existing Project Infrastructure

required_project_items = {
    "Project Folder": project_folder,
    "Project GDB": project_gdb,
    "Temp GDB": temp_gdb,
    "Outputs Folder": outputs_folder,
    "Tables Folder": tables_folder,
    "Charts Folder": charts_folder}

missing_project_items = []

print("Project infrastructure QA:")
for name, path in required_project_items.items():
    exists = (
        arcpy.Exists(path)
        if path.endswith(".gdb")
        else os.path.exists(path))

    print(f"{name:<18}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_project_items.append(name)

if missing_project_items:
    raise FileNotFoundError(f"Missing project infrastructure: {missing_project_items}")

print("")
print("Project infrastructure QA: PASS")

# Set workspace and coordinate system

arcpy.env.overwriteOutput = True

arcpy.env.workspace = temp_gdb
arcpy.env.scratchWorkspace = temp_gdb

ri_stateplane_meters = arcpy.SpatialReference(32130)
arcpy.env.outputCoordinateSystem = ri_stateplane_meters

print("ArcPy environment configured.")
print(f"Workspace          : {arcpy.env.workspace}")
print(f"Scratch workspace  : {arcpy.env.scratchWorkspace}")
print(f"Output CRS WKID    : {ri_stateplane_meters.factoryCode}")
print(f"Overwrite enabled  : {arcpy.env.overwriteOutput}")

# Define Project Constants

study_area_name = "Queen_Usquepaug"

stream_threshold = 35000
swat_cell_size = 10

sq_m_to_acres = 0.000247105

print("Shared constants defined.")
print(f"Study area       : {study_area_name}")
print(f"Stream threshold : {stream_threshold}")
print(f"SWAT cell size   : {swat_cell_size} m")

# Define Watershed and Terrain Inputs from Notebook 1
study_area   = os.path.join(project_gdb, f"{study_area_name}_StudyArea")
dem_hydro    = os.path.join(project_gdb, "DEM_HydroConditioned")
flow_dir     = os.path.join(project_gdb, "Flow_Direction")
flow_acc     = os.path.join(project_gdb, "Flow_Accumulation")

# Define stream and subbasin inputs from Notebook 1
stream_links      = os.path.join(project_gdb, f"StreamLinks_T{stream_threshold}")
stream_network    = os.path.join(project_gdb, f"StreamNetwork_T{stream_threshold}")
subbasin_raster   = os.path.join(project_gdb, f"SubbasinRaster_T{stream_threshold}")
subbasin_polygons = os.path.join(project_gdb, f"SubbasinPolygons_T{stream_threshold}")

# Define SWAT spatial inputs from Notebook 1
soils_projected  = os.path.join(project_gdb, "Soils_Projected")
lulc_projected   = os.path.join(project_gdb, "LULC_Projected")

print("Notebook 1 inputs defined.")

# Check required Notebook 1 handoff outputs

notebook_1_inputs = {
    "Study Area": study_area,
    "Hydro-Conditioned DEM": dem_hydro,
    "Flow Direction": flow_dir,
    "Flow Accumulation": flow_acc,
    "Stream Links": stream_links,
    "Stream Network": stream_network,
    "Subbasin Raster": subbasin_raster,
    "Subbasin Polygons": subbasin_polygons,
    "Projected Soils": soils_projected,
    "Projected LULC": lulc_projected}

missing_inputs = []

print("Notebook 1 input QA:")

for name, path in notebook_1_inputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<26}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_inputs.append(name)

if missing_inputs:
    raise FileNotFoundError(f"Missing Notebook 1 input(s): {missing_inputs}")

print("")
print("Notebook 1 input QA: PASS")

# Set Raster Environment from Active DEM

dem = dem_hydro

arcpy.env.snapRaster = dem
arcpy.env.cellSize = dem
arcpy.env.extent = dem
arcpy.env.mask = study_area

print("Raster environment set for Notebook 2.")
print(f" Snap Raster   : {arcpy.env.snapRaster}")
print(f" Cell Size     : {arcpy.env.cellSize}")
print(f" Mask          : {arcpy.env.mask}")

# Notebook Environment Summary

dem_desc = arcpy.Describe(dem)

subbasin_count = int(arcpy.management.GetCount(subbasin_polygons)[0])

stream_count = int(arcpy.management.GetCount(stream_network)[0])

subbasin_ids = set()

with arcpy.da.SearchCursor(subbasin_polygons, ["gridcode"]) as cursor:

    for row in cursor:
        subbasin_ids.add(row[0])

print("Notebook 1 handoff summary:")
print(f"Active DEM          : {os.path.basename(dem)}")
print(f"DEM CRS             : {dem_desc.spatialReference.name}")
print(f"DEM cell size       : {dem_desc.meanCellWidth} x {dem_desc.meanCellHeight}")
print(f"Subbasin polygons   : {subbasin_count}")
print(f"Unique subbasin IDs : {len(subbasin_ids)}")
print(f"Stream features     : {stream_count}")

# Define land cover outputs

lulc_raster      = os.path.join(project_gdb, "LULC_Raster")
lulc_swat_raster = os.path.join(project_gdb, "LULC_SWAT_Raster")

lulc_lookup_table = os.path.join(project_gdb, "LULC_SWAT_Lookup")
lulc_lookup_excel = os.path.join(tables_folder, "LULC_SWAT_Lookup.xlsx")

lulc_by_subbasin       = os.path.join(project_gdb, f"LULC_By_Subbasin_T{stream_threshold}")
lulc_by_subbasin_csv   = os.path.join(tables_folder, f"LULC_By_Subbasin_T{stream_threshold}.csv")
lulc_by_subbasin_excel = os.path.join(tables_folder, f"LULC_By_Subbasin_T{stream_threshold}.xlsx")

print("Land cover outputs defined.")
print(f"LULC Raster        : {lulc_raster}")
print(f"LULC SWAT Raster   : {lulc_swat_raster}")
print(f"LULC Lookup Table  : {lulc_lookup_table}")
print(f"LULC Summary Table : {lulc_by_subbasin}")

# Define soils outputs

soils_raster = os.path.join(project_gdb, "Soils_MUKEY_Raster")

soils_lookup_table = os.path.join(project_gdb, "Soils_MUKEY_HSG_Lookup")
soils_lookup_excel = os.path.join(tables_folder, "Soils_MUKEY_HSG_Lookup.xlsx")

soils_by_subbasin       = os.path.join(project_gdb, f"Soils_By_Subbasin_T{stream_threshold}")
soils_by_subbasin_csv   = os.path.join(tables_folder, f"Soils_By_Subbasin_T{stream_threshold}.csv")
soils_by_subbasin_excel = os.path.join(tables_folder, f"Soils_By_Subbasin_T{stream_threshold}.xlsx")

print("Soils outputs defined.")
print(f"Soils raster        : {soils_raster}")
print(f"Soils Lookup Table  : {soils_lookup_table}")
print(f"Soils Summary Table : {soils_by_subbasin}")

#  Define Slope Outputs

slope_raster = os.path.join(project_gdb, "Slope_Percent")
slope_reclass = os.path.join(project_gdb, "Slope_Reclass")

slope_lookup_table = os.path.join(project_gdb, "Slope_Class_Lookup")
slope_lookup_excel = os.path.join(tables_folder, "Slope_Class_Lookup.xlsx")

slope_by_subbasin       = os.path.join(project_gdb, f"Slope_By_Subbasin_T{stream_threshold}")
slope_by_subbasin_csv   = os.path.join(tables_folder, f"Slope_By_Subbasin_T{stream_threshold}.csv")
slope_by_subbasin_excel = os.path.join(tables_folder, f"Slope_By_Subbasin_T{stream_threshold}.xlsx")

print("Slope outputs defined.")
print(f"Slope raster        : {slope_raster}")
print(f"Slope reclassified  : {slope_reclass}")
print(f"Slope Lookup Table  : {slope_lookup_table}")
print(f"Slope Summary Table : {slope_by_subbasin}")

# Define Optional Notebook 2 Cleanup

rerun_cleanup = False

print(f"Rerun cleanup enabled: {rerun_cleanup}")

# Delete Notebook 2 Outputs (Optional)

notebook_2_outputs = [

    # Land cover outputs
    lulc_raster,
    lulc_swat_raster,
    lulc_lookup_table,
    lulc_by_subbasin,

    # Soils outputs
    soils_raster,
    soils_lookup_table,
    soils_by_subbasin,

    # Slope outputs
    slope_raster,
    slope_reclass,
    slope_lookup_table,
    slope_by_subbasin]

if rerun_cleanup:
    print("Running Notebook 2 cleanup...")

    for output in notebook_2_outputs:
        if arcpy.Exists(output):
            arcpy.management.Delete(output)
            print(f"Deleted: {os.path.basename(output)}")

    print("")
    print("Notebook 2 cleanup complete.")

else:

    print("Notebook 2 cleanup skipped.")

# Inspect LULC Fields

print("LULC fields:")

for field in arcpy.ListFields(lulc_projected):
    print(f"{field.name:<30} {field.type}")

# Define Land Cover Code Field

lulc_code_field = "LULC_2011"
lulc_desc_field = "Descr_2011"


print(f"LULC code field  : {lulc_code_field}")
print(f"LULC desc. field : {lulc_desc_field}")

# Convert RI Land Cover Vector to Raster
# Raster Value = RI land cover code from LULC_2011.

if arcpy.Exists(lulc_raster):
    arcpy.management.Delete(lulc_raster)

arcpy.conversion.PolygonToRaster(
    in_features=lulc_projected,
    value_field=lulc_code_field,
    out_rasterdataset=lulc_raster,
    cell_assignment="MAXIMUM_AREA",
    priority_field="NONE",
    cellsize=dem)

if not arcpy.Exists(lulc_raster):
    raise RuntimeError("LULC raster was not created.")

print("Raw RI land cover raster created.")
print(f"Output: {lulc_raster}")

# Build Raster Attribute Table

arcpy.management.BuildRasterAttributeTable(in_raster=lulc_raster, overwrite="Overwrite")

print("Raster attribute table built.")

# LULC Raster Alignment QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=dem,
    comparison_rasters=[lulc_raster])


# Create empty lookup table that connects RI LULC codes to SWAT land use codes.

if arcpy.Exists(lulc_lookup_table):
    arcpy.management.Delete(lulc_lookup_table)

arcpy.management.CreateTable(out_path=project_gdb, out_name="LULC_SWAT_Lookup")

print("SWAT lookup table created.")
print(f"Output: {lulc_lookup_table}")

#  Add Lookup Fields

lookup_fields = [
    ("RI_Code", "LONG", None),
    ("RI_Desc", "TEXT", 100),
    ("SWAT_Code", "TEXT", 20),
    ("SWAT_ID", "LONG", None)]

for field_name, field_type, field_length in lookup_fields:

    if field_type == "TEXT":

        arcpy.management.AddField(in_table=lulc_lookup_table, field_name=field_name, field_type=field_type, field_length=field_length)

    else:

        arcpy.management.AddField(in_table=lulc_lookup_table, field_name=field_name, field_type=field_type)

print("Lookup fields added.")

# Define Lookup Records

lulc_lookup_records = [
    (111, "High Density Residential", "URHD", 22),
    (112, "Medium High Density Residential", "URHD", 22),
    (113, "Medium Density Residential", "URMD", 21),
    (114, "Medium Low Density Residential", "URLD", 20),
    (115, "Low Density Residential", "URLD", 19),

    (120, "Commercial", "UCOM", 23),
    (130, "Industrial", "UIDU", 25),

    (140, "Roads", "UTRN", 26),
    (142, "Airports", "UTRN", 26),
    (144, "Water and Sewerage Treatment", "UIND", 25),
    (145, "Waste Disposal", "UIND", 25),
    (147, "Other Transportation", "UTRN", 26),

    (161, "Developed Recreation", "FESC", 55),
    (162, "Vacant Land", "RNGE", 71),
    (163, "Cemeteries", "FESC", 55),
    (170, "Institutions", "UINS", 24),

    (210, "Pasture", "PAST", 81),
    (220, "Cropland", "AGRR", 82),
    (230, "Orchards", "ORCD", 61),
    (250, "Idle Agriculture", "AGRL", 85),

    (300, "Brushland", "RNGB", 53),

    (410, "Deciduous Forest", "FRSD", 41),
    (420, "Softwood Forest", "FRST", 43),
    (430, "Mixed Forest", "FRST", 43),

    (500, "Water", "WATR", 11),
    (600, "Wetland", "WETF", 91),

    (720, "Sandy Areas", "SWRN", 33),
    (740, "Mines, Quarries, Gravel Pits", "SWRN", 33),
    (750, "Transitional Areas", "SWRN", 33),
    (760, "Mixed Barren Areas", "BARR", 77)]

print(f"Lookup records defined: {len(lulc_lookup_records)}")

# Populate Lookup Table

with arcpy.da.InsertCursor(lulc_lookup_table, ["RI_Code", "RI_Desc", "SWAT_Code", "SWAT_ID"]) as cursor:

    for row in lulc_lookup_records:
        cursor.insertRow(row)

print("Lookup table populated.")

# Lookup Table QA

lookup_count = int(arcpy.management.GetCount(lulc_lookup_table)[0])

print(f"Lookup table records: {lookup_count}")

# Remove Existing Join Fields

existing_fields = [field.name for field in arcpy.ListFields(lulc_raster)]

for field_name in ["RI_Desc", "SWAT_Code", "SWAT_ID"]:
    if field_name in existing_fields:
        arcpy.management.DeleteField(in_table=lulc_raster, drop_field=field_name)

print("Existing join fields removed.")

# Join Lookup Fields

arcpy.management.JoinField(
    in_data=lulc_raster,
    in_field="Value",
    join_table=lulc_lookup_table,
    join_field="RI_Code",
    fields=["RI_Desc", "SWAT_Code", "SWAT_ID"])

print("Lookup fields joined to lulc_raster attribute table.")

# Check for Missing SWAT IDs

missing_count = 0

with arcpy.da.SearchCursor(lulc_raster, ["Value", "SWAT_ID"]) as cursor:

    for value, swat_id in cursor:

        if swat_id is None:
            missing_count += 1
            print(f"Missing SWAT ID for RI code: {value}")

print(f"Missing SWAT IDs: {missing_count}")

# Create SWAT-Ready Raster
# Raster Value = SWAT_ID.

if arcpy.Exists(lulc_swat_raster):
    arcpy.management.Delete(lulc_swat_raster)

lulc_swat_result = Lookup(in_raster=lulc_raster, lookup_field="SWAT_ID")

lulc_swat_result.save(lulc_swat_raster)

print("SWAT-ready raster created.")

# Build SWAT Raster Attribute Table

arcpy.management.BuildRasterAttributeTable(in_raster=lulc_swat_raster, overwrite="Overwrite")

print("SWAT raster attribute table built.")

# LULC SWAT Raster QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=dem,
    comparison_rasters=[lulc_swat_raster])

# Remove existing SWAT code field if present

existing_fields = [field.name for field in arcpy.ListFields(lulc_swat_raster)]

if "SWAT_Code" in existing_fields:

    arcpy.management.DeleteField(in_table=lulc_swat_raster, drop_field="SWAT_Code")

    print("Existing SWAT code field checked.")

# Join SWAT Code

arcpy.management.JoinField(
    in_data=lulc_swat_raster,
    in_field="Value",
    join_table=lulc_lookup_table,
    join_field="SWAT_ID",
    fields=["SWAT_Code"])

print("SWAT codes joined.")

# SWAT Raster QA

print("SWAT raster attribute table:")

with arcpy.da.SearchCursor(lulc_swat_raster, ["Value", "Count", "SWAT_Code"]) as cursor:
    for value, count, swat_code in cursor:

        print(
            f"SWAT ID: {value:<5} "
            f"Count: {count:<10} "
            f"Code: {swat_code}")

# Summarize LULC by Subbasin

arcpy.raster_tools.Tabulate_Area_Summary_Table(
    zone_features=subbasin_polygons,
    zone_field="gridcode",
    class_raster=lulc_swat_raster,
    class_field="Value",
    output_tabulate_table=lulc_by_subbasin,
    output_csv=lulc_by_subbasin_csv,
    processing_cell_size=swat_cell_size)

# Export LULC Tables to Excel

if os.path.exists(lulc_lookup_excel):
    os.remove(lulc_lookup_excel)

if os.path.exists(lulc_by_subbasin_excel):
    os.remove(lulc_by_subbasin_excel)

arcpy.conversion.TableToExcel(Input_Table=lulc_lookup_table, Output_Excel_File=lulc_lookup_excel)

arcpy.conversion.TableToExcel(Input_Table=lulc_by_subbasin, Output_Excel_File=lulc_by_subbasin_excel)

print("LULC tables exported to Excel.")
print(f"Lookup Excel  : {lulc_lookup_excel}")
print(f"Summary Excel : {lulc_by_subbasin_excel}")

# Final LULC output QA

lulc_outputs = {
    "LULC Raster": lulc_raster,
    "SWAT LULC Raster": lulc_swat_raster,
    "Lookup Table": lulc_lookup_table,
    "Subbasin Summary": lulc_by_subbasin}

missing_outputs = []

print("LULC output QA:")

for name, path in lulc_outputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<22}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_outputs.append(name)

output_qa_pass = not missing_outputs

print(f"Output QA: {'PASS' if output_qa_pass else 'FAIL'}")

# Final LULC mapping QA

missing_mappings = []

with arcpy.da.SearchCursor(lulc_raster, ["Value", "SWAT_Code", "SWAT_ID"]) as cursor:
    for value, swat_code, swat_id in cursor:

        if swat_code is None or swat_id is None:
            missing_mappings.append(value)

mapping_qa_pass = not missing_mappings

print("LULC mapping QA:")
print(f"Missing mapped classes: {missing_mappings}")
print(f"Mapping QA            : {'PASS' if mapping_qa_pass else 'FAIL'}")

# Final LULC summary QA

summary_ids = set()

with arcpy.da.SearchCursor(lulc_by_subbasin, ["GRIDCODE"]) as cursor:
    for row in cursor:
        summary_ids.add(row[0])

missing_from_summary = sorted(subbasin_ids - summary_ids)

extra_in_summary = sorted(summary_ids - subbasin_ids)

summary_qa_pass = (
    not missing_from_summary and
    not extra_in_summary)

print("LULC summary QA:")
print(f"Subbasins    : {len(subbasin_ids):,}")
print(f"Summary rows : {len(summary_ids):,}")
print(f"Missing IDs  : {missing_from_summary}")
print(f"Extra IDs    : {extra_in_summary}")
print(f"Summary QA   : {'PASS' if summary_qa_pass else 'FAIL'}")

# Inspect Soil Fields

print("Soil fields:")

for field in arcpy.ListFields(soils_projected):
    print(f"{field.name:<30} {field.type}")

# Define soil fields

soil_mukey_field = "MUKEY"
soil_hsg_field = "HYDRO_GRP"
soil_mukey_id_field = "MUKEY_ID"

print(f"MUKEY field    : {soil_mukey_field}")
print(f"HSG field      : {soil_hsg_field}")
print(f"MUKEY ID field : {soil_mukey_id_field}")

# Add MUKEY_ID field if needed

existing_fields = [field.name for field in arcpy.ListFields(soils_projected)]

if soil_mukey_id_field not in existing_fields:
    arcpy.management.AddField(in_table=soils_projected, field_name=soil_mukey_id_field, field_type="LONG")
    print("MUKEY_ID field added.")

else:
    print("MUKEY_ID field already exists.")

# Calculate MUKEY_ID

arcpy.management.CalculateField(in_table=soils_projected, field=soil_mukey_id_field, expression=f"int(!{soil_mukey_field}!)", expression_type="PYTHON3")

print("MUKEY_ID calculated.")

# Create Soil MUKEY Raster - Raster Value = MUKEY_ID

if arcpy.Exists(soils_raster):
    arcpy.management.Delete(soils_raster)

arcpy.conversion.PolygonToRaster(
    in_features=soils_projected,
    value_field=soil_mukey_id_field,
    out_rasterdataset=soils_raster,
    cell_assignment="MAXIMUM_AREA",
    priority_field="NONE",
    cellsize=dem)

print("Soils raster created.")

# Build Soil Raster Attribute Table

arcpy.management.BuildRasterAttributeTable(in_raster=soils_raster, overwrite="Overwrite")

print("Soils raster attribute table built.")

# Soils Raster Alignment QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=dem,
    comparison_rasters=[soils_raster])

# Create soil lookup table

if arcpy.Exists(soils_lookup_table):
    arcpy.management.Delete(soils_lookup_table)

arcpy.management.CreateTable(out_path=project_gdb, out_name=os.path.basename(soils_lookup_table))

print("Soil lookup table created.")

# Add soil lookup fields

soil_lookup_fields = [
    ("MUKEY_ID", "LONG", None),
    ("MUKEY", "TEXT", 30),
    ("HSG", "TEXT", 10)]

for field_name, field_type, field_length in soil_lookup_fields:
    if field_type == "TEXT":
        arcpy.management.AddField(in_table=soils_lookup_table, field_name=field_name, field_type=field_type, field_length=field_length)

    else:
        arcpy.management.AddField(in_table=soils_lookup_table, field_name=field_name, field_type=field_type)

print("Soil lookup fields added.")

# Build soil lookup records

soil_records = {}

with arcpy.da.SearchCursor(soils_projected, [soil_mukey_id_field, soil_mukey_field, soil_hsg_field]) as cursor:
    for mukey_id, mukey, hsg in cursor:
        soil_records[mukey_id] = (mukey_id, str(mukey), hsg)

print(f"Soil lookup records prepared: {len(soil_records):,}")

# Populate Soil Lookup Table

with arcpy.da.InsertCursor(soils_lookup_table, ["MUKEY_ID", "MUKEY", "HSG"]) as cursor:

    for row in soil_records.values():
        cursor.insertRow(row)

print("Soil lookup table populated.")

# Soil Lookup Table QA

lookup_count = int(arcpy.management.GetCount(soils_lookup_table)[0])

print(f"Soil lookup records: {lookup_count:,}")

# Remove Existing Join Fields

existing_fields = [field.name for field in arcpy.ListFields(soils_raster)]

for field_name in ["MUKEY", "HSG"]:
    if field_name in existing_fields:

        arcpy.management.DeleteField(in_table=soils_raster, drop_field=field_name)

print("Existing soil join fields removed.")

# Join soil lookup fields

arcpy.management.JoinField(
    in_data=soils_raster,
    in_field="Value",
    join_table=soils_lookup_table,
    join_field="MUKEY_ID",
    fields=["MUKEY", "HSG"])

print("Soil lookup fields joined.")

# Soil raster mapping QA

missing_mappings = []

with arcpy.da.SearchCursor(soils_raster, ["Value", "MUKEY", "HSG"]) as cursor:
    for value, mukey, hsg in cursor:

        if mukey is None:
            missing_mappings.append(value)

print("Soil mapping QA:")
print(f"Missing mappings: {missing_mappings}")
print(f"Mapping QA      : {'PASS' if not missing_mappings else 'FAIL'}")

# Summarize soils by subbasin

arcpy.raster_tools.Tabulate_Area_Summary_Table(
    zone_features=subbasin_polygons,
    zone_field="gridcode",
    class_raster=soils_raster,
    class_field="Value",
    output_tabulate_table=soils_by_subbasin,
    output_csv=soils_by_subbasin_csv,
    processing_cell_size=swat_cell_size)

# Export Soil Tables to Excel

if os.path.exists(soils_lookup_excel):
    os.remove(soils_lookup_excel)

if os.path.exists(soils_by_subbasin_excel):
    os.remove(soils_by_subbasin_excel)

arcpy.conversion.TableToExcel(Input_Table=soils_lookup_table, Output_Excel_File=soils_lookup_excel)

arcpy.conversion.TableToExcel(Input_Table=soils_by_subbasin, Output_Excel_File=soils_by_subbasin_excel)

print("Soil Excel exports created.")

# Final soils output QA

soils_outputs = {
    "Soils Raster": soils_raster,
    "Lookup Table": soils_lookup_table,
    "Subbasin Summary": soils_by_subbasin}

missing_outputs = []

print("Soils output QA:")

for name, path in soils_outputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<22}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_outputs.append(name)

output_qa_pass = not missing_outputs

print(f"Output QA: {'PASS' if output_qa_pass else 'FAIL'}")

# Final soils mapping QA

missing_mappings = []

with arcpy.da.SearchCursor(soils_raster, ["Value", "MUKEY", "HSG"]) as cursor:
    for value, mukey, hsg in cursor:
        if mukey is None or hsg is None:
            missing_mappings.append(value)

mapping_qa_pass = not missing_mappings

print("Soils mapping QA:")
print(f"Missing mapped classes: {missing_mappings}")
print(f"Mapping QA            : {'PASS' if mapping_qa_pass else 'FAIL'}")

# Final soils summary QA

summary_ids = set()

with arcpy.da.SearchCursor(soils_by_subbasin, ["GRIDCODE"]) as cursor:
    for row in cursor:
        summary_ids.add(row[0])

missing_from_summary = sorted(subbasin_ids - summary_ids)

extra_in_summary = sorted(summary_ids - subbasin_ids)

summary_qa_pass = (
    not missing_from_summary and
    not extra_in_summary)

print("Soils summary QA:")
print(f"Subbasins    : {len(subbasin_ids):,}")
print(f"Summary rows : {len(summary_ids):,}")
print(f"Missing IDs  : {missing_from_summary}")
print(f"Extra IDs    : {extra_in_summary}")
print(f"Summary QA   : {'PASS' if summary_qa_pass else 'FAIL'}")

# Create percent slope raster

if arcpy.Exists(slope_raster):
    arcpy.management.Delete(slope_raster)

slope_result = Slope(in_raster=dem, output_measurement="PERCENT_RISE")

slope_result.save(slope_raster)

print("Percent slope raster created.")
print(f"Output: {slope_raster}")

# Check percent slope raster statistics

arcpy.management.CalculateStatistics(slope_raster)

minimum = arcpy.management.GetRasterProperties(slope_raster, "MINIMUM")[0]
maximum = arcpy.management.GetRasterProperties(slope_raster, "MAXIMUM")[0]
mean = arcpy.management.GetRasterProperties(slope_raster, "MEAN")[0]

print("Percent slope raster statistics:")
print(f"Minimum slope : {minimum}")
print(f"Maximum slope : {maximum}")
print(f"Mean slope    : {mean}")

# Slope Raster Alignment QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=dem,
    comparison_rasters=[slope_raster])

# Define Slope Reclassification
# 1 = 0–3%, 2 = 3–6%, 3 = 6–10%, 4 = 10–9999%

slope_remap = RemapRange([
    [0, 3, 1],
    [3, 6, 2],
    [6, 10, 3],
    [10, 9999999, 4]])

print("Slope classes defined.")

# Create reclassified slope raster

if arcpy.Exists(slope_reclass):
    arcpy.management.Delete(slope_reclass)

slope_reclass_result = Reclassify(in_raster=slope_raster, reclass_field="Value", remap=slope_remap)

slope_reclass_result.save(slope_reclass)

print("Slope reclassification raster created.")

# Build reclassified slope raster attribute table

arcpy.management.BuildRasterAttributeTable(in_raster=slope_reclass, overwrite="Overwrite")

print("Slope reclass attribute table built.")

# Reclassified Slope Raster Alignment QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=dem,
    comparison_rasters=[slope_reclass])

# Create slope lookup table

if arcpy.Exists(slope_lookup_table):
    arcpy.management.Delete(slope_lookup_table)

arcpy.management.CreateTable(out_path=project_gdb, out_name=os.path.basename(slope_lookup_table))

print("Slope lookup table created.")

# Add slope lookup fields

slope_lookup_fields = [
    ("Slope_ID", "LONG", None),
    ("Slope_Class", "TEXT", 20)]

for field_name, field_type, field_length in slope_lookup_fields:
    if field_type == "TEXT":
        arcpy.management.AddField(in_table=slope_lookup_table, field_name=field_name, field_type=field_type, field_length=field_length)

    else:
        arcpy.management.AddField(in_table=slope_lookup_table, field_name=field_name, field_type=field_type)

print("Slope lookup fields added.")

# Populate slope lookup table

slope_lookup_records = [
    (1, "0-3%"),
    (2, "3-6%"),
    (3, "6-10%"),
    (4, "10% +")]

with arcpy.da.InsertCursor(slope_lookup_table, ["Slope_ID", "Slope_Class"]) as cursor:
    for row in slope_lookup_records:
        cursor.insertRow(row)

print("Slope lookup table populated.")

# Slope lookup table QA

lookup_count = int(arcpy.management.GetCount(slope_lookup_table)[0])

print(f"Slope lookup records: {lookup_count:,}")

# Remove Existing Join Fields

existing_fields = [
    field.name
    for field in arcpy.ListFields(slope_reclass)]

if "Slope_Class" in existing_fields:

    arcpy.management.DeleteField(in_table=slope_reclass, drop_field="Slope_Class")

print("Existing slope join fields removed.")

# Join Slope Lookup Fields

arcpy.management.JoinField(
    in_data=slope_reclass,
    in_field="Value",
    join_table=slope_lookup_table,
    join_field="Slope_ID",
    fields=["Slope_Class"])

print("Slope lookup joined.")

# Summarize slopes by subbasin

arcpy.raster_tools.Tabulate_Area_Summary_Table(
    zone_features=subbasin_polygons,
    zone_field="gridcode",
    class_raster=slope_reclass,
    class_field="Value",
    output_tabulate_table=slope_by_subbasin,
    output_csv=slope_by_subbasin_csv,
    processing_cell_size=swat_cell_size)

# Export Slope Tables to Excel

if os.path.exists(slope_lookup_excel):
    os.remove(slope_lookup_excel)

if os.path.exists(slope_by_subbasin_excel):
    os.remove(slope_by_subbasin_excel)

arcpy.conversion.TableToExcel(Input_Table=slope_lookup_table, Output_Excel_File=slope_lookup_excel)
arcpy.conversion.TableToExcel(Input_Table=slope_by_subbasin, Output_Excel_File=slope_by_subbasin_excel)

print("Slope Excel exports created.")

# Slope Class Summary

print("Slope classes:")

with arcpy.da.SearchCursor(slope_reclass, ["Value", "Count", "Slope_Class"]) as cursor:

    for value, count, slope_class in cursor:

        print(
            f"Class: {value:<5} "
            f"Count: {count:<10} "
            f"Range: {slope_class}")

# Final slope summary QA

summary_ids = set()

with arcpy.da.SearchCursor(slope_by_subbasin, ["GRIDCODE"]) as cursor:
    for row in cursor:
        summary_ids.add(row[0])

missing_from_summary = sorted(subbasin_ids - summary_ids)

extra_in_summary = sorted(summary_ids - subbasin_ids)

summary_qa_pass = (
    not missing_from_summary and
    not extra_in_summary)

print("Slope summary QA:")
print(f"Subbasins    : {len(subbasin_ids):,}")
print(f"Summary rows : {len(summary_ids):,}")
print(f"Missing IDs  : {missing_from_summary}")
print(f"Extra IDs    : {extra_in_summary}")
print(f"Summary QA   : {'PASS' if summary_qa_pass else 'FAIL'}")

final_swat_outputs = {
    "LULC Raster": lulc_raster,
    "LULC SWAT Raster": lulc_swat_raster,
    "LULC Lookup Table": lulc_lookup_table,
    "LULC Summary Table": lulc_by_subbasin,

    "Soils Raster": soils_raster,
    "Soils Lookup Table": soils_lookup_table,
    "Soils Summary Table": soils_by_subbasin,

    "Slope Percent Raster": slope_raster,
    "Slope Class Raster": slope_reclass,
    "Slope Lookup Table": slope_lookup_table,
    "Slope Summary Table": slope_by_subbasin}

missing_outputs = []

print("Final SWAT spatial output QA:")

for name, path in final_swat_outputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<24}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_outputs.append(name)

output_qa_pass = not missing_outputs

print("")
print(f"Output QA: {'PASS' if output_qa_pass else 'REVIEW'}")

# Raster alignment QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=dem,
    comparison_rasters=[lulc_swat_raster, soils_raster, slope_reclass])

alignment_pass = True
print("Raster alignment QA complete.")

# Define Subbasin IDs for Summary QA

subbasin_ids = set()

with arcpy.da.SearchCursor(subbasin_polygons, ["gridcode"]) as cursor:
    for row in cursor:
        subbasin_ids.add(row[0])

print("Subbasin IDs loaded.")
print(f"Subbasins: {len(subbasin_ids):,}")

# Summary Table Subbasin Coverage QA

summary_tables = {
    "LULC Summary": lulc_by_subbasin,
    "Soils Summary": soils_by_subbasin,
    "Slope Summary": slope_by_subbasin}

coverage_pass = True

print("Subbasin summary coverage QA:")

for name, table in summary_tables.items():
    summary_ids = set()
    table_fields = [field.name for field in arcpy.ListFields(table)]
    zone_field = "gridcode" if "gridcode" in table_fields else "GRIDCODE"

    with arcpy.da.SearchCursor(table, [zone_field]) as cursor:
        for row in cursor:
            summary_ids.add(row[0])

    missing_ids = sorted(subbasin_ids - summary_ids)
    extra_ids = sorted(summary_ids - subbasin_ids)
    table_pass = (
        not missing_ids and
        not extra_ids)

    if not table_pass:
        coverage_pass = False

    print("")
    print(name)
    print(f"Zone field  : {zone_field}")
    print(f"Rows        : {len(summary_ids):,}")
    print(f"Missing IDs : {missing_ids}")
    print(f"Extra IDs   : {extra_ids}")
    print(f"Status      : {'PASS' if table_pass else 'REVIEW'}")

print("")
print(f"Subbasin Coverage QA: {'PASS' if coverage_pass else 'REVIEW'}")

# Calculate watershed area for raster coverage QA
watershed_area_sq_m = 0

with arcpy.da.SearchCursor(study_area, ["SHAPE@AREA"]) as cursor:
    for row in cursor:
        watershed_area_sq_m += row[0]

print(f"Watershed area: {watershed_area_sq_m:,.0f} sq m")

# Raster coverage QA

coverage_rasters = {
    "Land Cover": lulc_swat_raster,
    "Soils": soils_raster,
    "Slope": slope_reclass}

minimum_coverage_percent = 95.0
raster_coverage_pass = True

print("SWAT raster coverage QA:")

for name, raster in coverage_rasters.items():

    cell_count = 0

    arcpy.management.BuildRasterAttributeTable(in_raster=raster, overwrite="Overwrite")

    with arcpy.da.SearchCursor(raster, ["Count"]) as cursor:
        for row in cursor:
            cell_count += row[0]

    raster_area_sq_m = (cell_count * swat_cell_size * swat_cell_size)
    coverage_percent = (raster_area_sq_m / watershed_area_sq_m * 100)
    raster_pass = (coverage_percent >= minimum_coverage_percent)

    if not raster_pass:
        raster_coverage_pass = False

    print("")
    print(name)
    print(f"Valid cells : {cell_count:,.0f}")
    print(f"Area        : {raster_area_sq_m:,.0f} sq m")
    print(f"Coverage    : {coverage_percent:.2f}%")
    print(f"Status      : {'PASS' if raster_pass else 'REVIEW'}")

# Final Notebook 2 status

notebook_2_pass = (
    output_qa_pass and
    alignment_pass and
    coverage_pass and
    raster_coverage_pass)

print("Notebook 2 final status:")

if notebook_2_pass:
    print("PASS - SWAT spatial inputs are ready for Notebook 3 cleanup/export.")

else:
    print("REVIEW - Check the QA results above before continuing.")
