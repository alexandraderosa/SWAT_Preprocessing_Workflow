# Import Python Libraries

import os
import sys
import csv
import arcpy
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

print("Python libraries imported.")

# Import Shared Helper Functions

helper_folder = r"C:\Users\Alexandra\Documents\ArcGIS\Python_Helpers"

if helper_folder not in sys.path:
    sys.path.append(helper_folder)

from summary_helpers import *

print("Shared helper functions imported.")

# Import custom Python toolboxes
# Update this path before running locally.

base_folder = r"<BASE_ARCGIS_FOLDER>"
toolbox_folder = os.path.join(base_folder, "Toolboxes")

arcpy.ImportToolbox(os.path.join(toolbox_folder, "Field_Tools.pyt"), "field_tools")
arcpy.ImportToolbox(os.path.join(toolbox_folder, "Raster_Tools.pyt"), "raster_tools")
arcpy.ImportToolbox(os.path.join(toolbox_folder, "Vector_Tools.pyt"), "vector_tools")

print("Custom Python toolboxes imported.")
print("Field tools  : field_tools")
print("Raster tools : raster_tools")
print("Vector tools : vector_tools")

# Define Coordinate System and Shared Constants

ri_stateplane_meters = arcpy.SpatialReference(32130)
arcpy.env.outputCoordinateSystem = ri_stateplane_meters

# Shared constants
study_area_name = "Queen_Usquepaug"
stream_threshold = 35000
swat_cell_size = 10
sq_m_to_acres = 0.000247105

print("Coordinate system and shared constants defined.")
print(f"CRS WKID         : {ri_stateplane_meters.factoryCode}")
print(f"Study area       : {study_area_name}")
print(f"Stream threshold : {stream_threshold}")
print(f"SWAT cell size   : {swat_cell_size} m")

# Define Shared Join Fields

subbasin_join_field = "gridcode"
hru_polygon_join_field = "gridcode"
hru_table_join_field = "Value"

print("Shared join fields defined.")
print(f"Subbasin join field    : {subbasin_join_field}")
print(f"HRU polygon join field : {hru_polygon_join_field}")
print(f"HRU table join field   : {hru_table_join_field}")

# Define Project Paths

project_name = "Queen_Usquepaug"

project_folder = os.path.join(base_folder, "Projects", project_name)

# Define geodatabases
project_gdb = os.path.join(project_folder, f"{project_name}.gdb")
temp_gdb    = os.path.join(project_folder, "Temp.gdb")

# Define Output Folders
outputs_folder = os.path.join(project_folder, "Outputs")
tables_folder = os.path.join(outputs_folder, "Tables")
charts_folder = os.path.join(outputs_folder, "Charts")

print("Project paths defined.")
print(f"Project folder : {project_folder}")
print(f"Project GDB    : {project_gdb}")
print(f"Temp GDB       : {temp_gdb}")
print(f"Tables folder  : {tables_folder}")
print(f"Charts folder  : {charts_folder}")

# Confirm existing project infrastructure

required_project_items = {
    "Project GDB": project_gdb,
    "Temp GDB": temp_gdb,
    "Outputs Folder": outputs_folder,
    "Tables Folder": tables_folder,
    "Charts Folder": charts_folder}

missing_items = []

print("Project infrastructure QA:")

for name, path in required_project_items.items():
    exists = (
        arcpy.Exists(path)
        if path.endswith(".gdb")
        else os.path.exists(path))
    
    print(f"{name:<18}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_items.append(name)

if missing_items:
    raise FileNotFoundError(
        f"Missing project infrastructure: {missing_items}")

print("")
print("Project infrastructure QA: PASS")

# Define study area and watershed inputs from previous notebooks

study_area = os.path.join(project_gdb, f"{study_area_name}_StudyArea")

subbasin_raster = os.path.join(project_gdb, f"SubbasinRaster_T{stream_threshold}")
subbasin_polygons = os.path.join(project_gdb, f"SubbasinPolygons_T{stream_threshold}")
stream_network = os.path.join(project_gdb, f"StreamNetwork_T{stream_threshold}")

# Define SWAT-ready raster inputs

lulc_swat_raster = os.path.join(project_gdb, "LULC_SWAT_Raster")
soils_raster = os.path.join(project_gdb, "Soils_MUKEY_Raster")
slope_reclass = os.path.join(project_gdb, "Slope_Reclass")

print("Study area and watershed inputs defined.")
print("SWAT-ready raster inputs defined.")

# Check input datasets

required_inputs = {
    "Study Area": study_area,
    "Subbasin Raster": subbasin_raster,
    "Subbasin Polygons": subbasin_polygons,
    "Stream Network": stream_network,
    "Land Cover Raster": lulc_swat_raster,
    "Soils Raster": soils_raster,
    "Slope Raster": slope_reclass}

missing_inputs = []

print("Input dataset QA:")

for name, path in required_inputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<22}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_inputs.append(name)

if missing_inputs:
    raise FileNotFoundError(f"Missing inputs: {missing_inputs}")

print("")
print("Input dataset QA: PASS")

# Configure ArcPy Environment

arcpy.CheckOutExtension("Spatial")

arcpy.env.workspace = temp_gdb
arcpy.env.scratchWorkspace = temp_gdb
arcpy.env.overwriteOutput = True

print("ArcPy environment configured.")
print(f"Default workspace : {arcpy.env.workspace}")
print(f"Scratch workspace : {arcpy.env.scratchWorkspace}")
print(f"Overwrite enabled : {arcpy.env.overwriteOutput}")

# Configure Raster Environment

subbasin_desc = arcpy.Describe(subbasin_raster)

arcpy.env.snapRaster = subbasin_raster
arcpy.env.cellSize = swat_cell_size
arcpy.env.extent = subbasin_desc.extent
arcpy.env.mask = study_area

print("Raster environment configured for HRU creation.")
print(f"Snap raster : {os.path.basename(subbasin_raster)}")
print(f"Cell size   : {swat_cell_size} m")
print("Extent      : Subbasin raster extent")
print(f"Mask        : {os.path.basename(study_area)}")

# Define HRU outputs
hru_combined_temp   = os.path.join(temp_gdb, f"HRU_Combined_T{stream_threshold}_Temp")
hru_combined_raster = os.path.join(project_gdb, f"HRU_Combined_T{stream_threshold}")

hru_table    = os.path.join(project_gdb, f"HRU_Table_T{stream_threshold}")
hru_polygons = os.path.join(project_gdb, f"HRU_Polygons_T{stream_threshold}")

hru_definition_csv   = os.path.join(tables_folder, f"HRU_Definition_T{stream_threshold}.csv")
hru_definition_excel = os.path.join(tables_folder, f"HRU_Definition_T{stream_threshold}.xlsx")

hru_filtered_csv   = os.path.join(tables_folder, f"HRU_Filtered_Min1Acre_T{stream_threshold}.csv")
hru_filtered_excel = os.path.join(tables_folder, f"HRU_Filtered_Min1Acre_T{stream_threshold}.xlsx")

hru_definition_table_gdb = os.path.join(project_gdb, f"HRU_Definition_T{stream_threshold}")

print("HRU outputs defined.")

# Define HRU Summary Output Paths

subbasin_hru_summary_csv = os.path.join(tables_folder, f"Subbasin_HRU_Summary_T{stream_threshold}.csv")
subbasin_hru_summary_excel = os.path.join(tables_folder, f"Subbasin_HRU_Summary_T{stream_threshold}.xlsx")
subbasin_hru_summary_table = os.path.join(project_gdb, f"Subbasin_HRU_Summary_T{stream_threshold}")

print("HRU summary output paths defined.")

# Raster Alignment QA

arcpy.raster_tools.Raster_Alignment_QA(
    reference_raster=subbasin_raster,
    comparison_rasters=[
        lulc_swat_raster,
        soils_raster,
        slope_reclass])

print("Raster alignment QA complete.")

# Define Optional Notebook 4 Cleanup

rerun_cleanup = False

print(f"Rerun cleanup enabled: {rerun_cleanup}")

rerun_outputs = [hru_combined_raster, hru_table, hru_polygons]

if rerun_cleanup:
    print("Running rerun cleanup...")

    for output in rerun_outputs:
        if arcpy.Exists(output):
            arcpy.management.Delete(output)
            print(f"Deleted: {os.path.basename(output)}")

    print("Rerun cleanup complete.")

else:
    print("Rerun cleanup skipped.")

# Combine HRU Input Rasters

for raster in [hru_combined_temp, hru_combined_raster]:
    if arcpy.Exists(raster):
        arcpy.management.Delete(raster)

hru_combined_result = arcpy.sa.Combine([subbasin_raster, lulc_swat_raster, soils_raster, slope_reclass])
hru_combined_result.save(hru_combined_temp)

arcpy.management.CopyRaster(in_raster=hru_combined_temp, out_rasterdataset=hru_combined_raster)

print("HRU combined raster created.")
print(f"Temp output  : {hru_combined_temp}")
print(f"Final output : {hru_combined_raster}")

# Build HRU raster attribute table

arcpy.management.BuildRasterAttributeTable(in_raster=hru_combined_raster, overwrite="Overwrite")

print("HRU raster attribute table built.")

# Export HRU Raster Table to Project GDB

if arcpy.Exists(hru_table):
    arcpy.management.Delete(hru_table)

arcpy.conversion.TableToTable(in_rows=hru_combined_raster, out_path=project_gdb, out_name=os.path.basename(hru_table))

print("HRU raster table exported.")
print(f"Output: {hru_table}")

# Preview HRU Raster Table Fields

print("HRU raster table fields:")

for field in arcpy.ListFields(hru_table):
    print(f"- {field.name}")

# Step 1E - Count Unique HRU Combinations

hru_count = int(arcpy.management.GetCount(hru_table)[0])

print(f"Unique HRU combinations: {hru_count:,}")

# Delete Existing HRU Fields

hru_fields_to_delete = ["HRU_ID", "HRU_Area_sq_m", "HRU_Area_acres"]

existing_fields = [field.name for field in arcpy.ListFields(hru_table)]

fields_to_delete = [field_name for field_name in hru_fields_to_delete if field_name in existing_fields]

if fields_to_delete:
    arcpy.management.DeleteField(in_table=hru_table, drop_field=fields_to_delete)
    print("Existing HRU fields deleted.")

    for field_name in fields_to_delete:
        print(f"- {field_name}")

else:
    print("No existing HRU fields found.")

# Add HRU Fields

hru_fields_to_add = [
    ["HRU_ID", "LONG"],
    ["HRU_Area_sq_m", "DOUBLE"],
    ["HRU_Area_acres", "DOUBLE"]]

for field_name, field_type in hru_fields_to_add:
    arcpy.management.AddField(in_table=hru_table, field_name=field_name, field_type=field_type)

    print(f"Added field: {field_name}")

# Calculate HRU ID and Area Fields

cell_area_sq_m = swat_cell_size * swat_cell_size

with arcpy.da.UpdateCursor(hru_table, ["OBJECTID", "COUNT", "HRU_ID", "HRU_Area_sq_m", "HRU_Area_acres"]) as cursor:
    for row in cursor:
        row[2] = row[0]
        row[3] = (row[1] * cell_area_sq_m)
        row[4] = (row[3] * sq_m_to_acres)
        cursor.updateRow(row)

print("HRU ID and area fields calculated.")
print(f"Cell area : {cell_area_sq_m:,} m²")

# Apply HRU Field Aliases

field_aliases = {
    "HRU_ID": "HRU ID",
    "HRU_Area_sq_m": "HRU Area (m²)",
    "HRU_Area_acres": "HRU Area (acres)"}

for field_name, field_alias in field_aliases.items():
    arcpy.management.AlterField(in_table=hru_table, field=field_name, new_field_alias=field_alias)

    print(f"Alias updated: {field_name}")

# Preview HRU Field Names and Aliases

print("Updated HRU field aliases:")

for field in arcpy.ListFields(hru_table):
    if field.name in field_aliases:

        print(f"{field.name:<18} → {field.aliasName}")

# Preview Updated HRU Table Values

preview_fields = [
    "HRU_ID",
    "COUNT",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

preview_array = arcpy.da.TableToNumPyArray(hru_table, preview_fields)
preview_df = pd.DataFrame(preview_array)

print("Updated HRU table preview:")
print(f"Rows: {len(preview_df):,}")

display(preview_df.head(5))

# Check HRU Raster and Table Outputs

hru_outputs = {
    "HRU Combined Raster": hru_combined_raster,
    "HRU Table": hru_table}

missing_hru_outputs = []

print("HRU raster output QA:")

for name, path in hru_outputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<22}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_hru_outputs.append(name)

if missing_hru_outputs:
    raise FileNotFoundError(
        f"Missing HRU output(s): {missing_hru_outputs}")

print("")
print("HRU raster output QA: PASS")

# Check actual HRU table fields

print("Actual HRU table fields:")

for field in arcpy.ListFields(hru_table):
    print(f"- {field.name}")

# Validate Required HRU Table Fields

required_hru_fields = [
    "HRU_ID",
    "Value",
    "Count",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

hru_table_fields = [field.name for field in arcpy.ListFields(hru_table)]
missing_hru_fields = [field for field in required_hru_fields if field not in hru_table_fields]

print("HRU table field QA:")

for field in required_hru_fields:
    status = "OK" if field in hru_table_fields else "MISSING"
    print(f"{field:<18}: {status}")

if missing_hru_fields:
    raise ValueError(
        f"Missing required HRU field(s): {missing_hru_fields}")

print("")
print("HRU table field QA: PASS")

# Validate HRU Counts and Area Totals

hru_summary_fields = [
    "HRU_ID",
    "COUNT",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

hru_summary_array = arcpy.da.TableToNumPyArray(hru_table, hru_summary_fields, skip_nulls=False)
hru_summary_df = pd.DataFrame(hru_summary_array)

total_hru_cells = hru_summary_df["COUNT"].sum()
total_hru_area_sq_m = hru_summary_df["HRU_Area_sq_m"].sum()
total_hru_area_acres = hru_summary_df["HRU_Area_acres"].sum()

print("HRU count and area QA:")
print(f"Unique HRUs        : {len(hru_summary_df):,}")
print(f"Total HRU cells    : {total_hru_cells:,}")
print(f"Total area (m²)    : {total_hru_area_sq_m:,.2f}")
print(f"Total area (acres) : {total_hru_area_acres:,.2f}")

# Check for Null or Invalid HRU Values

invalid_hru_rows = hru_summary_df[
    (hru_summary_df["HRU_ID"].isna()) |
    (hru_summary_df["COUNT"] <= 0) |
    (hru_summary_df["HRU_Area_sq_m"] <= 0) |
    (hru_summary_df["HRU_Area_acres"] <= 0)]

print("Invalid HRU value QA:")

if len(invalid_hru_rows) > 0:
    display(invalid_hru_rows)

    raise ValueError(f"Invalid HRU rows found: {len(invalid_hru_rows):,}")

else:
    print("No null or invalid HRU values found.")

# Convert HRU Raster to Polygon Features

if arcpy.Exists(hru_polygons):
    arcpy.management.Delete(hru_polygons)

arcpy.conversion.RasterToPolygon(
    in_raster=hru_combined_raster,
    out_polygon_features=hru_polygons,
    simplify="NO_SIMPLIFY",
    raster_field="Value",
    create_multipart_features="SINGLE_OUTER_PART")

print("HRU polygons created.")
print(f"Output: {hru_polygons}")

# Calculate Polygon Geometry Field (square meters)

arcpy.field_tools.Add_Standard_Metric_Field(
    input_features=hru_polygons,
    metric_type="Area Square Meters",
    field_name="HRU_Area_sq_m",
    field_alias="HRU Area (m²)")

# Calculate Polygon Geometry Field (acres)

arcpy.field_tools.Add_Standard_Metric_Field(
    input_features=hru_polygons,
    metric_type="Area Acres",
    field_name="HRU_Area_acres",
    field_alias="HRU Area (acres)")

print("Polygon geometry fields calculated.")

# Delete Redundant Polygon Fields

fields_to_delete = ["Id"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(hru_polygons)]

delete_fields = [
    field
    for field in fields_to_delete
    if field in existing_polygon_fields]

if delete_fields:
    arcpy.management.DeleteField(in_table=hru_polygons, drop_field=delete_fields)
    print("Redundant polygon fields deleted.")

    for field in delete_fields: print(f"- {field}")

else:
    print("No redundant polygon fields found.")

# Apply Polygon Field Aliases

polygon_field_aliases = {
    "gridcode": "HRU Raster Value",
    "Shape_Length": "Polygon Perimeter",
    "Shape_Area": "Polygon Area (m²)",
    "HRU_Area_sq_m": "HRU Area (m²)",
    "HRU_Area_acres": "HRU Area (acres)"}

existing_polygon_fields = [field.name for field in arcpy.ListFields(hru_polygons)]

for field_name, field_alias in polygon_field_aliases.items():
    if field_name in existing_polygon_fields:
        arcpy.management.AlterField(in_table=hru_polygons, field=field_name, new_field_alias=field_alias)
        print(f"Alias updated: {field_name} → {field_alias}")

print("Polygon field aliases updated.")

# Preview HRU Polygon Fields and Aliases

print("HRU polygon fields and aliases:")

for field in arcpy.ListFields(hru_polygons):
    print(f"{field.name:<20} → {field.aliasName}")

# Count HRU Polygon Features

hru_polygon_count = int(arcpy.management.GetCount(hru_polygons)[0])

print(f"HRU polygon features: {hru_polygon_count:,}")

# Remove Existing Joined HRU Fields

joined_hru_fields = [
    "Count",
    "HRU_ID",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(hru_polygons)]
fields_to_delete = [field for field in joined_hru_fields if field in existing_polygon_fields]

if fields_to_delete:
    arcpy.management.DeleteField(in_table=hru_polygons, drop_field=fields_to_delete)
    print("Existing joined HRU fields deleted.")

    for field in fields_to_delete:
        print(f"- {field}")

else:
    print("No existing joined HRU fields found.")

# Join HRU Table Attributes to Polygons

join_fields = [
    "Count",
    "HRU_ID",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

arcpy.management.JoinField(
    in_data=hru_polygons,
    in_field=hru_polygon_join_field,
    join_table=hru_table,
    join_field=hru_table_join_field,
    fields=join_fields)

print("HRU table attributes joined to HRU polygons.")

# Apply Joined Field Aliases

joined_field_aliases = {
    "gridcode": "HRU Raster Value",
    "Count": "Cell Count",
    "HRU_ID": "HRU ID",
    "HRU_Area_sq_m": "HRU Area from Raster (m²)",
    "HRU_Area_acres": "HRU Area from Raster (acres)"}

existing_polygon_fields = [field.name for field in arcpy.ListFields(hru_polygons)]

for field_name, field_alias in joined_field_aliases.items():
    if field_name in existing_polygon_fields:
        arcpy.management.AlterField(in_table=hru_polygons, field=field_name, new_field_alias=field_alias)
        print(f"Alias updated: {field_name} → {field_alias}")

print("Joined field aliases updated.")

# Validate Joined HRU Fields

required_joined_fields = [
    "gridcode",
    "Count",
    "HRU_ID",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(hru_polygons)]
missing_joined_fields = [field for field in required_joined_fields if field not in existing_polygon_fields]
print("Joined HRU field QA:")

for field in required_joined_fields:
    status = "OK" if field in existing_polygon_fields else "MISSING"
    print(f"{field:<18}: {status}")

if missing_joined_fields:
    raise ValueError(f"Missing joined HRU field(s): {missing_joined_fields}")
print("")
print("Joined HRU field QA: PASS")

# Preview Joined HRU Polygon Attributes

preview_fields = [
    "gridcode",
    "Count",
    "HRU_ID",
    "HRU_Area_sq_m",
    "HRU_Area_acres"]

preview_array = arcpy.da.TableToNumPyArray(hru_polygons, preview_fields, skip_nulls=False)
hru_polygon_preview_df = pd.DataFrame(preview_array)

print("Joined HRU polygon preview:")
print(f"Rows: {len(hru_polygon_preview_df):,}")

display(hru_polygon_preview_df.head(5))

# Convert HRU Input Rasters to Arrays

hru_value_array = arcpy.RasterToNumPyArray(hru_combined_raster)
subbasin_array = arcpy.RasterToNumPyArray(subbasin_raster)

lulc_array = arcpy.RasterToNumPyArray(lulc_swat_raster)
soils_array = arcpy.RasterToNumPyArray(soils_raster)
slope_array = arcpy.RasterToNumPyArray(slope_reclass)

print("HRU input rasters converted to arrays.")

# Build HRU Cell DataFrame

hru_cell_df = pd.DataFrame(
    {
        "HRU Raster Value": hru_value_array.flatten(),
        "Subbasin ID": subbasin_array.flatten(),
        "SWAT ID": lulc_array.flatten(),
        "MUKEY ID": soils_array.flatten(),
        "Slope Class": slope_array.flatten()})

print("HRU cell dataframe created.")
print(f"Rows before cleanup: {len(hru_cell_df):,}")

display(hru_cell_df.head(2))

# Remove NoData and background cells

hru_cell_df = hru_cell_df.dropna().copy()

hru_cell_df = hru_cell_df[
    (hru_cell_df["HRU Raster Value"] > 0) &
    (hru_cell_df["Subbasin ID"] > 0) &
    (hru_cell_df["SWAT ID"] > 0) &
    (hru_cell_df["MUKEY ID"] > 0) &
    (hru_cell_df["Slope Class"] > 0)].copy()

print("NoData and background cells removed.")
print(f"Rows after cleanup: {len(hru_cell_df):,}")

display(hru_cell_df.head(5))

# Convert HRU cell fields to integer IDs

integer_fields = [
    "HRU Raster Value",
    "Subbasin ID",
    "SWAT ID",
    "MUKEY ID",
    "Slope Class"]

for field in integer_fields:
    hru_cell_df[field] = hru_cell_df[field].astype(int)
print("HRU cell ID fields converted to integers.")

display(hru_cell_df.head(5))

# Summarize unique HRU combinations

hru_definition_df = (
    hru_cell_df
    .groupby(["HRU Raster Value", "Subbasin ID", "SWAT ID", "MUKEY ID", "Slope Class"], as_index=False).size()
    .rename(columns={"size": "Cell Count"}))

print("Unique HRU combinations summarized.")
print(f"Rows: {len(hru_definition_df):,}")

display(hru_definition_df.head(5))

# Add HRU Area Fields

cell_area_sq_m = swat_cell_size * swat_cell_size

hru_definition_df["HRU Area (m²)"] = (hru_definition_df["Cell Count"] * cell_area_sq_m)
hru_definition_df["HRU Area (acres)"] = (hru_definition_df["HRU Area (m²)"] * sq_m_to_acres)

print("HRU area fields calculated.")
print(f"Cell area: {cell_area_sq_m:,} m²")

display(hru_definition_df.head(5))

# Organize HRU Definition Fields

hru_definition_df = hru_definition_df.rename(columns={"HRU Raster Value": "HRU ID"})

hru_definition_df = hru_definition_df[
    [
        "Subbasin ID",
        "HRU ID",
        "Cell Count",
        "HRU Area (m²)",
        "HRU Area (acres)",
        "SWAT ID",
        "MUKEY ID",
        "Slope Class"]].copy()

hru_definition_df = hru_definition_df.sort_values(by=["Subbasin ID", "HRU ID"], ascending=[True, True])

print("HRU definition table organized.")

display(hru_definition_df.head(15))

# Validate HRU definition table

missing_hru_ids = hru_definition_df[hru_definition_df["HRU ID"].isna()]

duplicate_combinations = (hru_definition_df[["Subbasin ID", "HRU ID", "SWAT ID", "MUKEY ID", "Slope Class"]].duplicated().sum())

print("HRU definition table QA:")
print(f"Rows                        : {len(hru_definition_df):,}")
print(f"Missing HRU IDs             : {len(missing_hru_ids):,}")
print(f"Duplicate HRU combinations  : {duplicate_combinations:,}")
print(f"Total area (acres)          : {hru_definition_df['HRU Area (acres)'].sum():,.2f}")

if len(missing_hru_ids) > 0:
    raise ValueError("Some HRU records are missing HRU IDs.")

if duplicate_combinations > 0:
    raise ValueError("Duplicate HRU combinations found.")

print("")
print("HRU definition table QA: PASS")

# Format Final HRU Definition Table

hru_definition_export_df = hru_definition_df.copy()

hru_definition_export_df["HRU Area (m²)"] = (hru_definition_export_df["HRU Area (m²)"].round(2))
hru_definition_export_df["HRU Area (acres)"] = (hru_definition_export_df["HRU Area (acres)"].round(2))

print("Final HRU definition table formatted.")

display(hru_definition_export_df.head(5))

# Export HRU Definition CSV

hru_definition_export_df.to_csv(hru_definition_csv, index=False)
hru_definition_export_df.to_excel(hru_definition_excel, index=False)

print("HRU definition CSV exported.")
print(f"Output: {hru_definition_csv}")
print(f"Output: {hru_definition_excel}")
print(f"Output: {hru_definition_table_gdb}")

# Export HRU Definition GDB Table

dataframe_to_gdb_table(
    hru_definition_export_df,
    hru_definition_table_gdb)

print("HRU definition geodatabase table exported.")
print(f"Output: {hru_definition_table_gdb}")

# Create Filtered HRU Definition Table

minimum_hru_area_acres = 1

hru_filtered_df = hru_definition_export_df[
    hru_definition_export_df["HRU Area (acres)"] >= minimum_hru_area_acres].copy()

print("Filtered HRU definition table created.")
print(f"Minimum HRU area : {minimum_hru_area_acres} acre")
print(f"Remaining HRUs   : {len(hru_filtered_df):,}")

display(hru_filtered_df.head(5))

# Export Filtered HRU Tables

hru_filtered_df.to_csv(hru_filtered_csv, index=False)
hru_filtered_df.to_excel(hru_filtered_excel, index=False)

print("Filtered HRU tables exported.")
print(f"CSV   : {hru_filtered_csv}")
print(f"Excel : {hru_filtered_excel}")

# Preview Final HRU Outputs

final_hru_outputs = {
    "HRU Definition CSV": hru_definition_csv,
    "HRU Definition Excel": hru_definition_excel,
    "Filtered HRU CSV": hru_filtered_csv,
    "Filtered HRU Excel": hru_filtered_excel,
    "HRU Definition GDB Table": hru_definition_table_gdb}

print("Final HRU output QA:")

for name, path in final_hru_outputs.items():
    if path.lower().endswith((".csv", ".xlsx")):
        exists = os.path.exists(path)
    else:
        exists = arcpy.Exists(path)
    print(f"{name:<28}: {'OK' if exists else 'MISSING'}")

print("")
print("TASK 03 complete: HRU definition tables exported.")

# Summarize Total HRUs by Subbasin

subbasin_hru_summary_df = (
    hru_definition_df
    .groupby("Subbasin ID")
    .agg(
        Total_HRUs=("HRU ID", "nunique"),
        Total_HRU_Area_Acres=("HRU Area (acres)", "sum"),
        Total_HRU_Cells=("Cell Count", "sum")).reset_index())

subbasin_hru_summary_df["Total_HRU_Area_Acres"] = (subbasin_hru_summary_df["Total_HRU_Area_Acres"].round(2))

print("Total HRU summary by subbasin created.")

display(subbasin_hru_summary_df.head(5))

# Summarize Filtered HRUs by Subbasin

filtered_hru_summary_df = (
    hru_filtered_df
    .groupby("Subbasin ID")
    .agg(
        Filtered_HRUs=("HRU ID", "nunique"),
        Filtered_HRU_Cells=("Cell Count", "sum"),
        Filtered_HRU_Area_Acres=("HRU Area (acres)", "sum"))
    .reset_index())

filtered_hru_summary_df["Filtered_HRU_Area_Acres"] = (filtered_hru_summary_df["Filtered_HRU_Area_Acres"].round(2))

print("Filtered HRU summary by subbasin created.")

display(filtered_hru_summary_df.head(5))

# Merge HRU Summary Tables

subbasin_hru_summary_df = (
    subbasin_hru_summary_df
    .merge(filtered_hru_summary_df, on="Subbasin ID", how="left"))

for field in [
    "Filtered_HRUs",
    "Filtered_HRU_Cells",
    "Filtered_HRU_Area_Acres"]:

    if field in subbasin_hru_summary_df.columns:
        subbasin_hru_summary_df[field] = (subbasin_hru_summary_df[field].fillna(0))

print("HRU summary tables merged.")

display(subbasin_hru_summary_df.head(5))

# Convert Summary Fields to Integers

integer_fields = [
    "Subbasin ID",
    "Total_HRUs",
    "Total_HRU_Cells",
    "Filtered_HRUs",
    "Filtered_HRU_Cells"]

for field in integer_fields:
    subbasin_hru_summary_df[field] = (subbasin_hru_summary_df[field].astype(int))

print("Integer summary fields converted.")

display(subbasin_hru_summary_df.head(5))

# Preview HRU Summary Statistics

print("Subbasin HRU summary statistics:")
print(f"Subbasins                  : {len(subbasin_hru_summary_df):,}")
print(f"Total HRUs                 : {subbasin_hru_summary_df['Total_HRUs'].sum():,}")
print(f"Filtered HRUs              : {subbasin_hru_summary_df['Filtered_HRUs'].sum():,}")
print(f"Total HRU Area (acres)     : {subbasin_hru_summary_df['Total_HRU_Area_Acres'].sum():,.2f}")
print(f"Filtered HRU Area (acres)  : {subbasin_hru_summary_df['Filtered_HRU_Area_Acres'].sum():,.2f}")

# Preview Final HRU Summary Table

display(subbasin_hru_summary_df.sort_values(by="Total_HRUs", ascending=False).head(15))

# Format HRU Summary Export Table

subbasin_hru_export_df = (subbasin_hru_summary_df.copy())

area_fields = [
    "Total_HRU_Area_Acres",
    "Filtered_HRU_Area_Acres"]

for field in area_fields:
    subbasin_hru_export_df[field] = (subbasin_hru_export_df[field].round(2))

print("HRU summary export table formatted.")
display(subbasin_hru_export_df.head(5))

# Export HRU summaries to cvs, Excel, and geodatabase table

subbasin_hru_export_df.to_csv(subbasin_hru_summary_csv, index=False)
subbasin_hru_export_df.to_excel(subbasin_hru_summary_excel, index=False)
dataframe_to_gdb_table(subbasin_hru_export_df, subbasin_hru_summary_table)

print("HRU summaries exported.")
print(f"Output: {subbasin_hru_summary_csv}")
print(f"Output: {subbasin_hru_summary_excel}")
print(f"Output: {subbasin_hru_summary_table}")

# Preview HRU Summary Output QA

summary_outputs = {
    "HRU Summary CSV": subbasin_hru_summary_csv,
    "HRU Summary Excel": subbasin_hru_summary_excel,
    "HRU Summary GDB Table": subbasin_hru_summary_table}

print("HRU summary export QA:")

for name, path in summary_outputs.items():
    if path.lower().endswith((".csv", ".xlsx")):
        exists = os.path.exists(path)
    else:
        exists = arcpy.Exists(path)
    print(f"{name:<28}: {'OK' if exists else 'MISSING'}")

print("")
print("TASK 04 complete: Subbasin HRU summaries exported.")

# Preview Existing Subbasin Polygon Fields

print("Subbasin polygon fields before HRU summary join:")

for field in arcpy.ListFields(subbasin_polygons):
    print(f"- {field.name}")

# Delete Existing HRU Summary Fields

hru_summary_fields = [
    "Total_HRUs",
    "Total_HRU_Cells",
    "Total_HRU_Area_Acres",
    "Filtered_HRUs",
    "Filtered_HRU_Cells",
    "Filtered_HRU_Area_Acres"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]
fields_to_delete = [field for field in hru_summary_fields if field in existing_polygon_fields]

if fields_to_delete:
    arcpy.management.DeleteField(in_table=subbasin_polygons, drop_field=fields_to_delete)
    print("Existing HRU summary fields deleted.")

else:
    print("No existing HRU summary fields found.")

# Preview HRU Summary Table Fields

print("HRU summary table fields:")

for field in arcpy.ListFields(subbasin_hru_summary_table):
    print(f"- {field.name}")

# Join HRU Summary Fields to Subbasin Polygons

join_fields = [
    "Total_HRUs",
    "Total_HRU_Cells",
    "Total_HRU_Area_Acres",
    "Filtered_HRUs",
    "Filtered_HRU_Cells",
    "Filtered_HRU_Area_Acres"]

arcpy.management.JoinField(
    in_data=subbasin_polygons,
    in_field=subbasin_join_field,
    join_table=subbasin_hru_summary_table,
    join_field="Subbasin_ID",
    fields=join_fields)

print("HRU summary fields joined to subbasin polygons.")

# Validate Joined HRU Summary Fields

required_join_fields = [
    "Total_HRUs",
    "Total_HRU_Cells",
    "Total_HRU_Area_Acres",
    "Filtered_HRUs",
    "Filtered_HRU_Cells",
    "Filtered_HRU_Area_Acres"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]
missing_join_fields = [field for field in required_join_fields if field not in existing_polygon_fields]

print("Joined HRU summary field QA:")

for field in required_join_fields:
    status = ("OK" if field in existing_polygon_fields else "MISSING")
    print(f"{field:<30}: {status}")

if missing_join_fields:
    raise ValueError(f"Missing joined HRU summary fields: {missing_join_fields}")

print("")
print("Joined HRU summary field QA: PASS")

# Apply HRU Summary Field Aliases

field_aliases = {
    "Total_HRUs": "Total HRUs",
    "Total_HRU_Cells": "Total HRU Cells",
    "Total_HRU_Area_Acres": "Total HRU Area (acres)",
    "Filtered_HRUs": "Filtered HRUs",
    "Filtered_HRU_Cells": "Filtered HRU Cells",
    "Filtered_HRU_Area_Acres": "Filtered HRU Area (acres)"}

existing_polygon_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]

for field_name, field_alias in field_aliases.items():
    if field_name in existing_polygon_fields:
        arcpy.management.AlterField(in_table=subbasin_polygons, field=field_name, new_field_alias=field_alias)
        print(f"Alias updated: {field_name}")

# Preview HRU Summary Field Aliases

print("Updated HRU summary field aliases:")

for field in arcpy.ListFields(subbasin_polygons):
    if field.name in field_aliases:
        print(f"{field.name:<30} → {field.aliasName}")

# Preview Joined Polygon Attributes

preview_fields = [
    "gridcode",
    "Total_HRUs",
    "Filtered_HRUs",
    "Total_HRU_Area_Acres",
    "Filtered_HRU_Area_Acres"]

preview_array = arcpy.da.TableToNumPyArray(subbasin_polygons, preview_fields, skip_nulls=False)
subbasin_polygon_preview_df = pd.DataFrame(preview_array)

display(subbasin_polygon_preview_df.head(12))

# Check for Null HRU Summary Values

qa_fields = ["Total_HRUs", "Filtered_HRUs"]

qa_array = arcpy.da.TableToNumPyArray(subbasin_polygons, qa_fields, skip_nulls=False)
qa_df = pd.DataFrame(qa_array)
null_summary_rows = qa_df[qa_df.isnull().any(axis=1)]
print("Null HRU summary QA:")

if len(null_summary_rows) > 0:
    display(null_summary_rows)
    raise ValueError("Null HRU summary values found.")

else:
    print("No null HRU summary values found.")

# Final Polygon Layer QA Summary

subbasin_feature_count = int(arcpy.management.GetCount(subbasin_polygons)[0])

print("Final polygon layer QA summary:")
print(f"Subbasin features          : {subbasin_feature_count:,}")
print(f"Total HRUs                 : {subbasin_hru_summary_df['Total_HRUs'].sum():,}")
print(f"Filtered HRUs              : {subbasin_hru_summary_df['Filtered_HRUs'].sum():,}")
print(f"Total HRU Area (acres)     : {subbasin_hru_summary_df['Total_HRU_Area_Acres'].sum():,.2f}")
print(f"Filtered HRU Area (acres)  : {subbasin_hru_summary_df['Filtered_HRU_Area_Acres'].sum():,.2f}")

print("")
print("TASK 05 complete.")

# Delete Redundant Polygon Fields

fields_to_delete = ["Id"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]

delete_fields = [field for field in fields_to_delete if field in existing_polygon_fields]
if delete_fields:
    arcpy.management.DeleteField(in_table=subbasin_polygons, drop_field=delete_fields)
    print("Redundant polygon fields deleted.")

else:
    print("No redundant polygon fields found.")

# Apply Final Polygon Field Aliases

final_field_aliases = {
    "gridcode": "Subbasin ID",
    "Subbasin_Area_sq_m": "Subbasin Area (m²)",
    "Subbasin_Area_acres": "Subbasin Area (acres)",
    "Dominant_Town": "Dominant Town",
    "Dominant_LULC": "Dominant Land Cover",
    "SWAT_LULC": "Dominant SWAT Land Cover",
    "LULC_Pct": "Dominant LULC (%)",
    "Dominant_HSG": "Dominant Hydrologic Soil Group",
    "HSG_Pct": "Dominant HSG (%)",
    "Dominant_Slope": "Dominant Slope Class",
    "Slope_Pct": "Dominant Slope (%)"}

existing_polygon_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]

for field_name, field_alias in final_field_aliases.items():
    if field_name in existing_polygon_fields:
        arcpy.management.AlterField(in_table=subbasin_polygons, field=field_name, new_field_alias=field_alias)
        print(f"Alias updated: {field_name}")

# Preview Final Polygon Fields and Aliases

print("Final polygon fields and aliases:")

for field in arcpy.ListFields(subbasin_polygons):
    print(f"{field.name:<32} → {field.aliasName}")

# Preview Final Polygon Attributes

preview_fields = [
    "gridcode",
    "Dominant_Town",
    "Dominant_LULC",
    "Dominant_HSG",
    "Dominant_Slope",
    "Total_HRUs",
    "Filtered_HRUs"]

preview_array = arcpy.da.TableToNumPyArray(subbasin_polygons, preview_fields, skip_nulls=False)
final_polygon_preview_df = pd.DataFrame(preview_array)

display(final_polygon_preview_df.head(12))

# Validate Final Polygon Fields

required_fields = [
    "gridcode",
    "Dominant_Town",
    "Dominant_LULC",
    "Dominant_HSG",
    "Dominant_Slope",
    "Total_HRUs",
    "Filtered_HRUs"]

existing_polygon_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]

missing_fields = [field for field in required_fields if field not in existing_polygon_fields]
print("Final polygon field QA:")

for field in required_fields:
    status = ("OK" if field in existing_polygon_fields else "MISSING")
    print(f"{field:<28}: {status}")

if missing_fields:
    raise ValueError(f"Missing final polygon fields: {missing_fields}")

print("")
print("TASK 06 complete.")

# Create Chart Output Paths

total_hrus_chart    = os.path.join(charts_folder, "Total_HRUs_By_Subbasin.png")
filtered_hrus_chart = os.path.join(charts_folder, "Filtered_HRUs_By_Subbasin.png")
total_area_chart    = os.path.join(charts_folder, "Total_HRU_Area_By_Subbasin.png")
filtered_area_chart = os.path.join(charts_folder, "Filtered_HRU_Area_By_Subbasin.png")

print("Chart output paths defined.")

# Calculate HRU Filtering Metrics

subbasin_hru_summary_df["HRU_Filter_Reduction_Pct"] = ((subbasin_hru_summary_df["Total_HRUs"] - subbasin_hru_summary_df["Filtered_HRUs"]) / subbasin_hru_summary_df["Total_HRUs"]) * 100

subbasin_hru_summary_df["HRU_Area_Retention_Pct"] = (subbasin_hru_summary_df["Filtered_HRU_Area_Acres"] / subbasin_hru_summary_df["Total_HRU_Area_Acres"]) * 100

print("HRU filtering metrics calculated.")

# Create Total HRUs by Subbasin Chart

create_horizontal_bar_chart(
    df=subbasin_hru_summary_df,
    category_field="Subbasin ID",
    value_field="Total_HRUs",
    output_png=total_hrus_chart,
    title="Total HRUs by Subbasin",
    xlabel="Total HRUs",
    ylabel="Subbasin ID",
    add_value_labels=True)

# Create Filtered HRUs by Subbasin Chart

create_horizontal_bar_chart(
    df=subbasin_hru_summary_df,
    category_field="Subbasin ID",
    value_field="Filtered_HRUs",
    output_png=filtered_hrus_chart,
    title="Filtered HRUs by Subbasin",
    xlabel="Filtered HRUs",
    ylabel="Subbasin ID",
    add_value_labels=True)

# Create Total HRU Area Chart

create_horizontal_bar_chart(
    df=subbasin_hru_summary_df,
    category_field="Subbasin ID",
    value_field="Total_HRU_Area_Acres",
    output_png=total_area_chart,
    title="Total HRU Area by Subbasin",
    xlabel="Area (acres)",
    ylabel="Subbasin ID",
    add_value_labels=False)

# Create Filtered HRU Area Chart

create_horizontal_bar_chart(
    df=subbasin_hru_summary_df,
    category_field="Subbasin ID",
    value_field="Filtered_HRU_Area_Acres",
    output_png=filtered_area_chart,
    title="Filtered HRU Area by Subbasin",
    xlabel="Area (acres)",
    ylabel="Subbasin ID",
    add_value_labels=False)


