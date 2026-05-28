# Imports

import os
import arcpy
import sys
import pandas as pd

from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

arcpy.env.overwriteOutput = True

print("Libraries imported.")
print(f"Overwrite output: {arcpy.env.overwriteOutput}")

# Import custom Python toolboxes
# Update this path before running locally.

base_folder = r"<BASE_ARCGIS_FOLDER>"
toolbox_folder = os.path.join(base_folder, "Toolboxes")

arcpy.ImportToolbox(os.path.join(toolbox_folder, "Raster_Tools.pyt"), "raster_tools")

print("Custom Python toolboxes imported.")
print("Raster tools : raster_tools")

# Import Shared Helper Functions

helper_folder = os.path.join(base_folder, "Python_Helpers")

if helper_folder not in sys.path:
    sys.path.append(helper_folder)

from summary_helpers import *

print("Shared helper functions imported.")
print(f"Helper folder: {helper_folder}")

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
    "Project GDB": project_gdb,
    "Temp GDB": temp_gdb,
    "Outputs Folder": outputs_folder,
    "Tables Folder": tables_folder,
    "Charts Folder": charts_folder}

missing_project_items = []

print("Project infrastructure QA:")
for name, path in required_project_items.items():
    exists = (arcpy.Exists(path) if path.endswith(".gdb") else os.path.exists(path))
    print(f"{name:<18}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_project_items.append(name)

if missing_project_items:
    raise FileNotFoundError(f"Missing required project infrastructure: {missing_project_items}")

print("")
print("Project infrastructure QA: PASS")

# Set workspace and coordinate system

ri_stateplane_meters = arcpy.SpatialReference(32130)

arcpy.env.workspace = temp_gdb
arcpy.env.scratchWorkspace = temp_gdb
arcpy.env.outputCoordinateSystem = ri_stateplane_meters

print("ArcGIS environment set.")
print(f"Workspace             : {arcpy.env.workspace}")
print(f"Scratch Workspace     : {arcpy.env.scratchWorkspace}")
print(f"Output Coordinate Sys : {arcpy.env.outputCoordinateSystem.name}")
print(f"CRS WKID              : {ri_stateplane_meters.factoryCode}")
print(f"Overwrite Enabled     : {arcpy.env.overwriteOutput}")

# Define shared constants

study_area_name = "Queen_Usquepaug"
stream_threshold = 35000
sq_m_to_acres = 0.000247105

print("Shared constants set.")
print(f" Stream threshold      : {stream_threshold:,}")
print(f" Square meters to acres: {sq_m_to_acres}")
print(f" Study area            : {study_area_name}")

# Define shared join fields

subbasin_join_field = "gridcode"

print("Shared join fields defined.")
print(f"Subbasin join field : {subbasin_join_field}")

# Terrain and watershed inputs

subbasin_polygons = os.path.join(project_gdb, f"SubbasinPolygons_T{stream_threshold}")

# SWAT-ready raster inputs

lulc_swat_raster = os.path.join(project_gdb, "LULC_SWAT_Raster")
soils_raster     = os.path.join(project_gdb, "Soils_MUKEY_Raster")
slope_reclass    = os.path.join(project_gdb, "Slope_Reclass")

# Lookup tables

lulc_lookup_table  = os.path.join(project_gdb, "LULC_SWAT_Lookup")
soils_lookup_table = os.path.join(project_gdb, "Soils_MUKEY_HSG_Lookup")
slope_lookup_table = os.path.join(project_gdb, "Slope_Class_Lookup")

# By-subbasin summary tables

lulc_by_subbasin = os.path.join(project_gdb, f"LULC_By_Subbasin_T{stream_threshold}")
soils_by_subbasin = os.path.join(project_gdb, f"Soils_By_Subbasin_T{stream_threshold}")
slope_by_subbasin = os.path.join(project_gdb, f"Slope_By_Subbasin_T{stream_threshold}")

print("Notebook 3 inputs defined.")

# Validate Notebook Inputs

notebook_inputs = {
    "Subbasin Polygons": subbasin_polygons,
    "LULC SWAT Raster": lulc_swat_raster,
    "Soils Raster": soils_raster,
    "Slope Reclass": slope_reclass,
    "LULC Lookup": lulc_lookup_table,
    "Soils Lookup": soils_lookup_table,
    "Slope Lookup": slope_lookup_table,
    "LULC by Subbasin": lulc_by_subbasin,
    "Soils by Subbasin": soils_by_subbasin,
    "Slope by Subbasin": slope_by_subbasin}

missing_inputs = []

print("Notebook input QA:")

for name, path in notebook_inputs.items():
    if arcpy.Exists(path):
        try:
            count = int(arcpy.management.GetCount(path)[0])

            print(f"{name:<24}: OK | {count:,} records/features")

        except Exception:
            print(f"{name:<24}: OK")

    else:
        print(f"{name:<24}: MISSING")
        missing_inputs.append(name)

if missing_inputs:
    raise FileNotFoundError(f"Missing required inputs: {missing_inputs}")

print("")
print("Notebook input QA: PASS")

# Define Notebook 3 Outputs

# Task 01 - Land Cover Summary Cleanup
lulc_subbasin_long_csv = os.path.join(tables_folder, "LULC_Subbasin_Long.csv")

# Task 02 - Soils Summary Cleanup
soils_subbasin_long_csv = os.path.join(tables_folder, "Soils_Subbasin_Long.csv")

# Task 03 - Slope Summary Cleanup
slope_subbasin_long_csv = os.path.join(tables_folder, "Slope_Subbasin_Long.csv")

# Task 04 - Dominant Class Summaries
lulc_dominant_summary_csv = os.path.join(tables_folder, "Dominant_LULC_By_Subbasin.csv")
soils_dominant_summary_csv = os.path.join(tables_folder, "Dominant_Soils_By_Subbasin.csv")
slope_dominant_summary_csv = os.path.join(tables_folder, "Dominant_Slope_By_Subbasin.csv")
lulc_dominant_frequency_csv = os.path.join(tables_folder, "Dominant_LULC_Frequency.csv")

# Task 05 - Dominant Class Mapping Layers
dominant_lulc_join_table = os.path.join(project_gdb, "Dominant_LULC_Join")
dominant_soils_join_table = os.path.join(project_gdb, "Dominant_Soils_Join")
dominant_slope_join_table = os.path.join(project_gdb, "Dominant_Slope_Join")

# Task 06 - Final Tables and Figures
lulc_composition_figure = os.path.join(charts_folder, "Watershed_LandCover_Composition.png")
slope_distribution_figure = os.path.join(charts_folder, "Watershed_Slope_Distribution.png")
hsg_distribution_figure = os.path.join(charts_folder, "Hydrologic_Soil_Group_Distribution.png")
lulc_dominant_frequency_figure = os.path.join(charts_folder, "Dominant_LandCover_Frequency.png")

print("Notebook 3 outputs defined.")

# Define Optional Notebook 3 Cleanup

rerun_cleanup = False

print(f"Rerun cleanup enabled: {rerun_cleanup}")

# Optional Rerun Cleanup (True / False)

notebook_outputs = [
    lulc_subbasin_long_csv,
    soils_subbasin_long_csv,
    slope_subbasin_long_csv,

    lulc_dominant_summary_csv,
    soils_dominant_summary_csv,
    slope_dominant_summary_csv,

    lulc_dominant_frequency_csv,

    dominant_lulc_join_table,
    dominant_soils_join_table,
    dominant_slope_join_table,

    lulc_composition_figure,
    slope_distribution_figure,
    hsg_distribution_figure,
    lulc_dominant_frequency_figure]

if rerun_cleanup:

    print("Running rerun cleanup...")

    for output in notebook_outputs:
        if arcpy.Exists(output):
            arcpy.management.Delete(output)
            print(f"Deleted GIS item: {os.path.basename(output)}")

        elif os.path.exists(output):
            os.remove(output)
            print(f"Deleted file: {os.path.basename(output)}")

        else:
            print(f"Skipped, not found: {os.path.basename(output)}")
    print("Rerun cleanup complete.")

else:
    print("Rerun cleanup skipped.")

# Get all non-geometry fields from the LULC by-subbasin table

lulc_fields = [
    field.name
    for field in arcpy.ListFields(lulc_by_subbasin)
    if field.type not in ["Geometry", "OID"]]

print("First lulc summary fields:")
for field in lulc_fields[:10]:
    print(field)

# Convert the ArcGIS table to a NumPy array
lulc_array = arcpy.da.TableToNumPyArray(lulc_by_subbasin, lulc_fields, skip_nulls=False)

# Convert the NumPy array to a Pandas DataFrame
lulc_wide_df = pd.DataFrame(lulc_array)

print("LULC wide table loaded.")
print(f"Rows    : {len(lulc_wide_df):,}")
print(f"Columns : {len(lulc_wide_df.columns):,}")

# Field containing the subbasin identifier
lulc_subbasin_field = "GRIDCODE"

if "gridcode" in lulc_wide_df.columns:
    lulc_subbasin_field = "gridcode"

# VALUE fields created by Tabulate Area
lulc_area_fields = [field for field in lulc_wide_df.columns if field.startswith("VALUE_")]

# Convert wide-format table to long-format table
lulc_subbasin_long_df = lulc_wide_df.melt(
    id_vars=[lulc_subbasin_field],
    value_vars=lulc_area_fields,
    var_name="LULC_Value_Field",
    value_name="Area (m²)")

# Remove zero-area rows
lulc_subbasin_long_df = (lulc_subbasin_long_df[lulc_subbasin_long_df["Area (m²)"] > 0].copy())

# Extract LULC ID from VALUE field names
lulc_subbasin_long_df["LULC ID"] = (
    lulc_subbasin_long_df["LULC_Value_Field"]
    .str.replace("VALUE_", "", regex=False)
    .astype(int))

# Remove temporary VALUE field
lulc_subbasin_long_df = (
    lulc_subbasin_long_df
    .drop(columns=["LULC_Value_Field"])
    .rename(columns={lulc_subbasin_field: "Subbasin ID"}))

print("LULC summary reshaped to long format.")
print(f"LULC area fields : {len(lulc_area_fields):,}")
print(f"Long rows        : {len(lulc_subbasin_long_df):,}")

display(lulc_subbasin_long_df.head(10))

# Fields needed from the LULC lookup table
lulc_lookup_fields = [
    "RI_Code",
    "RI_Desc",
    "SWAT_Code",
    "SWAT_ID"]

# Convert lookup table to Pandas DataFrame
lulc_lookup_array = arcpy.da.TableToNumPyArray(lulc_lookup_table, lulc_lookup_fields, skip_nulls=False)

lulc_lookup_df = pd.DataFrame(lulc_lookup_array)

# Standardize original ID fields before renaming
lulc_lookup_df["RI_Code"] = lulc_lookup_df["RI_Code"].astype(int)
lulc_lookup_df["SWAT_ID"] = lulc_lookup_df["SWAT_ID"].astype(int)

# Rename lookup fields for clearer final output
lulc_lookup_df = lulc_lookup_df.rename(
    columns={
        "RI_Code": "RILC Code",
        "RI_Desc": "RILC Description",
        "SWAT_Code": "SWAT LULC Code",
        "SWAT_ID": "LULC ID"})

# Standardize join fields before merge
lulc_lookup_df["LULC ID"] = lulc_lookup_df["LULC ID"].astype(int)
lulc_subbasin_long_df["LULC ID"] = lulc_subbasin_long_df["LULC ID"].astype(int)

print("LULC lookup table loaded.")
print(f"Lookup records: {len(lulc_lookup_df):,}")

display(lulc_lookup_df.head(10))

print("LULC lookup dataframe fields:")
for field in lulc_lookup_df.columns:
    print(f"- {field}")

# Join LULC Lookup Information

lulc_subbasin_long_df = lulc_subbasin_long_df.merge(lulc_lookup_df, on="LULC ID", how="left")

print("LULC lookup joined.")

display(lulc_subbasin_long_df.head(10))

# Check current LULC dataframe columns

print("Current LULC columns:")

for column in lulc_subbasin_long_df.columns:
    print(column)

# Convert square meters to acres

lulc_subbasin_long_df["Area (acres)"] = (lulc_subbasin_long_df["Area (m²)"] * sq_m_to_acres)

# Calculate total mapped LULC area within each subbasin

lulc_subbasin_long_df["Subbasin Area (m²)"] = (lulc_subbasin_long_df.groupby("Subbasin ID")["Area (m²)"].transform("sum"))

# Calculate percent of each subbasin represented by each LULC class

lulc_subbasin_long_df["Percent Subbasin"] = (lulc_subbasin_long_df["Area (m²)"] / lulc_subbasin_long_df["Subbasin Area (m²)"] * 100)

# Round numeric fields for cleaner formatting

lulc_subbasin_long_df["Area (m²)"] = lulc_subbasin_long_df["Area (m²)"].round(2)
lulc_subbasin_long_df["Area (acres)"] = lulc_subbasin_long_df["Area (acres)"].round(2)
lulc_subbasin_long_df["Percent Subbasin"] = lulc_subbasin_long_df["Percent Subbasin"].round(2)

print("LULC area statistics calculated.")

# Preview calculated area statistics

display(lulc_subbasin_long_df.head(10))

# Sum total LULC area by subbasin
lulc_area_summary = (lulc_subbasin_long_df.groupby("Subbasin ID")["Area (m²)"].sum())

# Check for LULC IDs that did not match the lookup table
missing_lulc_lookup = (
    lulc_subbasin_long_df[
        lulc_subbasin_long_df["RILC Code"].isna()
    ]["LULC ID"]
    .drop_duplicates()
    .tolist())

lulc_summary_qa_pass = len(missing_lulc_lookup) == 0

print("LULC summary QA:")
print(f"Subbasins summarized : {len(lulc_area_summary):,}")
print(f"Long table rows      : {len(lulc_subbasin_long_df):,}")
print(f"Total LULC area      : {lulc_area_summary.sum():,.2f} m²")
print(f"Missing mappings     : {len(missing_lulc_lookup)}")
print(f"LULC Summary QA      : {'PASS' if lulc_summary_qa_pass else 'FAIL'}")

# Get all non-geometry fields from the soils by-subbasin table
soils_fields = [
    field.name
    for field in arcpy.ListFields(soils_by_subbasin)
    if field.type not in ["Geometry", "OID"]]

print("First soils summary fields:")
for field in soils_fields[:10]:
    print(field)

# Convert the ArcGIS table to a NumPy array
soils_array = arcpy.da.TableToNumPyArray(soils_by_subbasin, soils_fields, skip_nulls=False)

# Convert the NumPy array to a Pandas DataFrame
soils_wide_df = pd.DataFrame(soils_array)

print("Soils wide table loaded.")
print(f"Rows    : {len(soils_wide_df):,}")
print(f"Columns : {len(soils_wide_df.columns):,}")

# Preview raw wide soils table

display(soils_wide_df.head())

# Field containing the subbasin identifier
soils_subbasin_field = "GRIDCODE"

# VALUE fields created by Tabulate Area
soils_area_fields = [field for field in soils_wide_df.columns if field.startswith("VALUE_")]

# Convert the wide table to a long table
soils_subbasin_long_df = soils_wide_df.melt(
    id_vars=[soils_subbasin_field],
    value_vars=soils_area_fields,
    var_name="Soils_Value_Field",
    value_name="Area (m²)")

# Remove soil map units that do not occur in a subbasin
soils_subbasin_long_df = (soils_subbasin_long_df[soils_subbasin_long_df["Area (m²)"] > 0].copy())

# Extract MUKEY ID from VALUE field names
soils_subbasin_long_df["MUKEY_ID"] = (
    soils_subbasin_long_df["Soils_Value_Field"]
    .str.replace("VALUE_", "", regex=False)
    .astype(int))

# Remove temporary VALUE field and rename subbasin field
soils_subbasin_long_df = (
    soils_subbasin_long_df
    .drop(columns=["Soils_Value_Field"])
    .rename(columns={soils_subbasin_field: "Subbasin ID"}))

print("Soils summary reshaped to long format.")
print(f"Subbasin ID field : {soils_subbasin_field}")
print(f"Soils area fields : {len(soils_area_fields):,}")
print(f"Long rows         : {len(soils_subbasin_long_df):,}")

display(soils_subbasin_long_df.head(10))

# Check soils lookup fields

print("Soils lookup fields:")

for field in arcpy.ListFields(soils_lookup_table):
    print(f"{field.name:<30} {field.type}")

# Fields needed from the soils lookup table
soils_lookup_fields = [
    "MUKEY_ID",
    "MUKEY",
    "HSG"]

# Convert lookup table to Pandas DataFrame
soils_lookup_array = arcpy.da.TableToNumPyArray(soils_lookup_table, soils_lookup_fields, skip_nulls=False)
soils_lookup_df = pd.DataFrame(soils_lookup_array)

# Standardize ID fields before joining
soils_lookup_df["MUKEY_ID"] = soils_lookup_df["MUKEY_ID"].astype(int)
soils_lookup_df["MUKEY"] = soils_lookup_df["MUKEY"].astype(str)

# Rename lookup fields for clearer final output
soils_lookup_df = soils_lookup_df.rename(columns={"HSG": "Hydrologic Soil Group"})

# Standardize join fields before merge
soils_lookup_df["MUKEY_ID"] = soils_lookup_df["MUKEY_ID"].astype(int)
soils_subbasin_long_df["MUKEY_ID"] = soils_subbasin_long_df["MUKEY_ID"].astype(int)

print("Soils lookup table loaded.")
print(f"Lookup records: {len(soils_lookup_df):,}")

display(soils_lookup_df.head(10))

# Join hydrologic soil group information onto the long-format summary table
soils_subbasin_long_df = soils_subbasin_long_df.merge(soils_lookup_df, on="MUKEY_ID", how="left")

print("Soils lookup joined.")

display(soils_subbasin_long_df.head(10))

# Convert square meters to acres
soils_subbasin_long_df["Area (acres)"] = (soils_subbasin_long_df["Area (m²)"] * sq_m_to_acres)

# Calculate total mapped soils area within each subbasin
soils_subbasin_long_df["Subbasin Area (m²)"] = (soils_subbasin_long_df.groupby("Subbasin ID")["Area (m²)"].transform("sum"))

# Calculate percent of each subbasin represented by each soil map unit
soils_subbasin_long_df["Percent Subbasin"] = (soils_subbasin_long_df["Area (m²)"] / soils_subbasin_long_df["Subbasin Area (m²)"] * 100)

# Round numeric fields for cleaner reporting
soils_subbasin_long_df["Area (m²)"] = soils_subbasin_long_df["Area (m²)"].round(2)
soils_subbasin_long_df["Area (acres)"] = soils_subbasin_long_df["Area (acres)"].round(2)
soils_subbasin_long_df["Percent Subbasin"] = soils_subbasin_long_df["Percent Subbasin"].round(2)

print("Soils area statistics calculated.")

# Sum total soils area by subbasin
soils_area_summary = (soils_subbasin_long_df.groupby("Subbasin ID")["Area (m²)"].sum())

# Check for MUKEY IDs that did not match the lookup table
missing_soils_lookup = (
    soils_subbasin_long_df[
        soils_subbasin_long_df["Hydrologic Soil Group"].isna()
    ]["MUKEY_ID"]
    .drop_duplicates()
    .tolist())

soils_summary_qa_pass = len(missing_soils_lookup) == 0

print("Soils summary QA:")
print(f"Subbasins summarized : {len(soils_area_summary):,}")
print(f"Long table rows      : {len(soils_subbasin_long_df):,}")
print(f"Total soils area     : {soils_area_summary.sum():,.2f} m²")
print(f"Missing mappings     : {len(missing_soils_lookup)}")
print(f"Soils Summary QA     : {'PASS' if soils_summary_qa_pass else 'FAIL'}")

# Get all non-geometry fields from the slope by-subbasin table
slope_fields = [
    field.name
    for field in arcpy.ListFields(slope_by_subbasin)
    if field.type not in ["Geometry", "OID"]]

# Convert the ArcGIS table to a NumPy array
slope_array = arcpy.da.TableToNumPyArray(slope_by_subbasin, slope_fields, skip_nulls=False)

# Convert the NumPy array to a Pandas DataFrame
slope_wide_df = pd.DataFrame(slope_array)

print("Slope wide table loaded.")
print(f"Rows    : {len(slope_wide_df):,}")
print(f"Columns : {len(slope_wide_df.columns):,}")

print("\nRaw slope summary fields:")
for field in slope_fields:
    print(f"- {field}")

# Preview raw wide slope table

display(slope_wide_df.head())

# Field containing the subbasin identifier
slope_subbasin_field = "GRIDCODE"

# Handle possible lowercase field naming
if "gridcode" in slope_wide_df.columns:
    slope_subbasin_field = "gridcode"

# VALUE fields created by Tabulate Area
slope_area_fields = [field for field in slope_wide_df.columns if field.startswith("VALUE_")]


print(f"Subbasin ID field : {slope_subbasin_field}")
print(f"Slope area fields : {len(slope_area_fields):,}")

# Convert the wide table to a long table
slope_subbasin_long_df = slope_wide_df.melt(
    id_vars=[slope_subbasin_field],
    value_vars=slope_area_fields,
    var_name="Slope_Value_Field",
    value_name="Area (m²)")

# Remove slope classes that do not occur in a subbasin
slope_subbasin_long_df = (slope_subbasin_long_df[slope_subbasin_long_df["Area (m²)"] > 0].copy())

# Extract Slope_ID from VALUE field names
slope_subbasin_long_df["Slope_ID"] = (
    slope_subbasin_long_df["Slope_Value_Field"]
    .str.replace("VALUE_", "", regex=False)
    .astype(int))

# Remove temporary VALUE field and rename subbasin field
slope_subbasin_long_df = (
    slope_subbasin_long_df
    .drop(columns=["Slope_Value_Field"])
    .rename(columns={slope_subbasin_field: "Subbasin ID"}))

print("Slope summary reshaped to long format.")
print(f"Subbasin ID field : {slope_subbasin_field}")
print(f"Slope area fields : {len(slope_area_fields):,}")
print(f"Long rows         : {len(slope_subbasin_long_df):,}")

display(slope_subbasin_long_df.head(10))

# Preview slope lookup table fields

print("Slope lookup table fields:")

for field in arcpy.ListFields(slope_lookup_table):
    print(field.name)

# Fields needed from the slope lookup table
slope_lookup_fields = [
    "Slope_ID",
    "Slope_Class"]

# Convert lookup table to Pandas DataFrame
slope_lookup_array = arcpy.da.TableToNumPyArray(
    slope_lookup_table,
    slope_lookup_fields,
    skip_nulls=False)

slope_lookup_df = pd.DataFrame(slope_lookup_array)

# Standardize join field before joining
slope_lookup_df["Slope_ID"] = slope_lookup_df["Slope_ID"].astype(int)
slope_subbasin_long_df["Slope_ID"] = slope_subbasin_long_df["Slope_ID"].astype(int)

print("Slope lookup table loaded.")
print(f"Lookup records: {len(slope_lookup_df):,}")

display(slope_lookup_df.head(10))

# Join slope class labels onto the long-format summary table
slope_subbasin_long_df = slope_subbasin_long_df.merge(slope_lookup_df, on="Slope_ID", how="left")

print("Slope lookup joined.")

display(slope_subbasin_long_df.head(10))

# Check current slope dataframe columns

print("Current slope dataframe columns:")

for column in slope_subbasin_long_df.columns:
    print(column)

# Convert square meters to acres
slope_subbasin_long_df["Area (acres)"] = (slope_subbasin_long_df["Area (m²)"] * sq_m_to_acres)

# Calculate total mapped slope area within each subbasin
slope_subbasin_long_df["Subbasin Area (m²)"] = (slope_subbasin_long_df.groupby("Subbasin ID")["Area (m²)"].transform("sum"))

# Calculate percent of each subbasin represented by each slope class
slope_subbasin_long_df["Percent Subbasin"] = (slope_subbasin_long_df["Area (m²)"] / slope_subbasin_long_df["Subbasin Area (m²)"] * 100)

# Round numeric fields for cleaner reporting
slope_subbasin_long_df["Area (m²)"] = slope_subbasin_long_df["Area (m²)"].round(2)
slope_subbasin_long_df["Area (acres)"] = slope_subbasin_long_df["Area (acres)"].round(2)
slope_subbasin_long_df["Percent Subbasin"] = slope_subbasin_long_df["Percent Subbasin"].round(2)

print("Slope area statistics calculated.")

# Sum total slope area by subbasin
slope_area_summary = (slope_subbasin_long_df.groupby("Subbasin ID")["Area (m²)"].sum())

# Check for slope IDs that did not match the lookup table
missing_slope_lookup = (
    slope_subbasin_long_df[
        slope_subbasin_long_df["Slope_Class"].isna()
    ]["Slope_ID"]
    .drop_duplicates()
    .tolist())

slope_summary_qa_pass = len(missing_slope_lookup) == 0

print("Slope summary QA:")
print(f"Subbasins summarized : {len(slope_area_summary):,}")
print(f"Long table rows      : {len(slope_subbasin_long_df):,}")
print(f"Total slope area     : {slope_area_summary.sum():,.2f} m²")
print(f"Missing mappings     : {len(missing_slope_lookup)}")
print(f"Slope Summary QA     : {'PASS' if slope_summary_qa_pass else 'FAIL'}")

print("LULC long dataframe fields:")

for field in lulc_subbasin_long_df.columns:
    print(field)

# Select the largest land cover class within each subbasin
lulc_dominant_df = (
    lulc_subbasin_long_df
    .sort_values(
        by=["Subbasin ID", "Percent Subbasin"],
        ascending=[True, False])
    .drop_duplicates(subset=["Subbasin ID"])
    .reset_index(drop=True))

# Organize final dominant LULC fields
lulc_dominant_df = lulc_dominant_df[
    [
        "Subbasin ID",
        "RILC Code",
        "RILC Description",
        "LULC ID",
        "SWAT LULC Code",
        "Area (m²)",
        "Area (acres)",
        "Percent Subbasin"]].copy()

# Preview Dominant LULC Summary

print("Dominant LULC summary created.")
print(f"Subbasins summarized: {len(lulc_dominant_df):,}")

display(lulc_dominant_df.head(10))

# Check Soils columns before dominant summary

print("Soils long dataframe fields:")

for field in soils_subbasin_long_df.columns:
    print(field)

# Select the largest soil map unit within each subbasin
soils_dominant_df = (
    soils_subbasin_long_df
    .sort_values(
        by=["Subbasin ID", "Percent Subbasin"],
        ascending=[True, False])
    .drop_duplicates(subset=["Subbasin ID"])
    .reset_index(drop=True))

print("Dominant soils selected.")

# Keep final dominant soils fields
soils_dominant_df = soils_dominant_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "MUKEY_ID",
        "MUKEY",
        "Area (m²)",
        "Area (acres)",
        "Hydrologic Soil Group",
        "Percent Subbasin"]].copy()

# Rename area and percent fields for clarity
soils_dominant_df = soils_dominant_df.rename(
    columns={
        "Area (m²)": "MUKEY Area (m²)",
        "Area (acres)": "MUKEY Area (acres)",
        "Percent Subbasin": "Percent of Subbasin"})

print("Dominant soils fields organized.")

# Preview Dominant Soils Summary
print("Dominant soils summary created.")
print(f"Subbasins summarized: {len(soils_dominant_df):,}")

display(soils_dominant_df.head(10))

# Check slope columns before dominant summary

print("Slope long dataframe fields:")

for field in slope_subbasin_long_df.columns:
    print(field)

# Select the largest slope class within each subbasin
slope_dominant_df = (
    slope_subbasin_long_df
    .sort_values(
        by=["Subbasin ID", "Area (m²)"],
        ascending=[True, False])
    .drop_duplicates(subset=["Subbasin ID"])
    .reset_index(drop=True))

print("Dominant slope classes selected.")

# Keep final dominant slope fields using current working field names
slope_dominant_df = slope_dominant_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "Slope_ID",
        "Slope_Class",
        "Area (m²)",
        "Area (acres)",
        "Percent Subbasin"]].copy()

# Rename area and percent fields for clarity
slope_dominant_df = slope_dominant_df.rename(
    columns={
        "Area (m²)": "Slope Area (m²)",
        "Area (acres)": "Slope Area (acres)",
        "Percent Subbasin": "Percent of Subbasin"})

print("Dominant slope fields organized.")

# Preview Dominant Slope Summary

print("Dominant slope summary created.")
print(f"Subbasins summarized: {len(slope_dominant_df):,}")

display(slope_dominant_df.head(10))

# Compare dominant summary row counts to source subbasin counts
dominant_summary_checks = {
    "Dominant LULC": [lulc_dominant_df, lulc_subbasin_long_df["Subbasin ID"].nunique()],
    "Dominant Soils": [soils_dominant_df, soils_subbasin_long_df["Subbasin ID"].nunique()],
    "Dominant Slope": [slope_dominant_df, slope_subbasin_long_df["Subbasin ID"].nunique()]}

print("Dominant summary QA:")

for name, values in dominant_summary_checks.items():
    dominant_df = values[0]
    expected_subbasins = values[1]

    dominant_rows = len(dominant_df)
    dominant_subbasins = dominant_df["Subbasin ID"].nunique()

    qa_pass = (dominant_rows == expected_subbasins and dominant_subbasins == expected_subbasins)

    print(
        f"{name:<18}: "
        f"{dominant_rows:,} rows | "
        f"{dominant_subbasins:,} unique subbasins | "
        f"expected {expected_subbasins:,} | "
        f"{'PASS' if qa_pass else 'CHECK'}")

# Summarize total land cover area across the whole watershed
lulc_summary_df = (
    lulc_subbasin_long_df
    .groupby("SWAT LULC Code", as_index=False)
    .agg(Area_acres=("Area (acres)", "sum")))

# Rename field for plotting/reporting
lulc_summary_df = lulc_summary_df.rename(
    columns={"Area_acres": "Area (acres)"})

# Calculate watershed land cover percentages
total_lulc_area = lulc_summary_df["Area (acres)"].sum()
lulc_summary_df["Percent Watershed"] = (lulc_summary_df["Area (acres)"] / total_lulc_area * 100).round(2)

# Sort by largest area
lulc_summary_df = lulc_summary_df.sort_values(by="Area (acres)", ascending=False)

print("Watershed land cover summary created.")

display(lulc_summary_df)

# Create Watershed Land Cover Composition figure

create_horizontal_bar_chart(
    df=lulc_summary_df,
    category_field="SWAT LULC Code",
    value_field="Area (acres)",
    output_png=lulc_composition_figure,
    title="Watershed Land Cover Composition",
    xlabel="Area (acres)",
    ylabel="SWAT Land Cover Code")

print(f"Saved: {lulc_composition_figure}")

# Summarize dominant land cover frequency by subbasin

dominant_lulc_plot_df = (lulc_dominant_df.groupby("SWAT LULC Code", as_index=False).size().rename(columns={"size": "Subbasins Dominated"}))

# Calculate dominant land cover percentages

total_subbasins = dominant_lulc_plot_df["Subbasins Dominated"].sum()
dominant_lulc_plot_df["Percent of Total Subbasins"] = (dominant_lulc_plot_df["Subbasins Dominated"] / total_subbasins * 100).round(2)

# Sort by most frequently dominant

dominant_lulc_plot_df = dominant_lulc_plot_df.sort_values(by="Subbasins Dominated", ascending=False)

print("Dominant land cover frequency table created.")

display(dominant_lulc_plot_df)

# Create dominant land cover frequency figure

create_horizontal_bar_chart(
    df=dominant_lulc_plot_df,
    category_field="SWAT LULC Code",
    value_field="Subbasins Dominated",
    output_png=lulc_dominant_frequency_figure,
    title="Dominant Land Cover Frequency by Subbasin",
    xlabel="Number of Subbasins",
    ylabel="SWAT Land Cover Code")

print(f"Saved: {lulc_dominant_frequency_figure}")

# Summarize watershed-wide slope distribution

slope_summary_df = (slope_subbasin_long_df.groupby("Slope_Class", as_index=False)["Area (acres)"].sum())

# Rename only the summary output field
slope_summary_df = slope_summary_df.rename(columns={"Area (acres)": "Slope Area (acres)"})

print("Slope areas summarized.")

# Calculate watershed slope percentages
total_slope_area = slope_summary_df["Slope Area (acres)"].sum()

slope_summary_df["Percent Watershed"] = (slope_summary_df["Slope Area (acres)"] / total_slope_area * 100).round(2)

# Sort summary table by largest area
slope_summary_df = slope_summary_df.sort_values(
    by="Slope Area (acres)",
    ascending=False)

print("Watershed slope summary created.")

display(slope_summary_df)

# Create watershed slope distribution figure

create_horizontal_bar_chart(
    df=slope_summary_df,
    category_field="Slope_Class",
    value_field="Slope Area (acres)",
    output_png=slope_distribution_figure,
    title="Watershed Slope Distribution",
    xlabel="Area (acres)",
    ylabel="Slope Class")

print(f"Saved: {slope_distribution_figure}")

# Summarize hydrologic soil group distribution

hsg_summary_df = (soils_subbasin_long_df.groupby("Hydrologic Soil Group", as_index=False)["Area (acres)"].sum())

# Rename summary output field
hsg_summary_df = hsg_summary_df.rename(
    columns={"Area (acres)": "MUKEY Area (acres)"})

print("Hydrologic soil group areas summarized.")

# Calculate hydrologic soil group percentages

total_hsg_area = hsg_summary_df["MUKEY Area (acres)"].sum()

hsg_summary_df["Percent Watershed"] = (hsg_summary_df["MUKEY Area (acres)"] / total_hsg_area * 100).round(2)

# Sort by largest watershed area
hsg_summary_df = hsg_summary_df.sort_values(by="MUKEY Area (acres)", ascending=False)

print("Hydrologic soil group summary created.")

display(hsg_summary_df)

# Create hydrologic soil group distribution figure

create_horizontal_bar_chart(
    df=hsg_summary_df,
    category_field="Hydrologic Soil Group",
    value_field="MUKEY Area (acres)",
    output_png=hsg_distribution_figure,
    title="Hydrologic Soil Group Distribution",
    xlabel="Area (acres)",
    ylabel="Hydrologic Soil Group")

print(f"Saved: {hsg_distribution_figure}")

# Prepare clean LULC export table

lulc_export_df = lulc_subbasin_long_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "LULC ID",
        "SWAT LULC Code",
        "RILC Code",
        "RILC Description",
        "Area (m²)",
        "Area (acres)",
        "Percent Subbasin"]].copy()

# Rename columns

lulc_export_df = lulc_export_df.rename(
    columns={
        "LULC ID": "SWAT ID",
        "RILC Code": "NLCD Code",
        "RILC Description": "NLCD Description",
        "Area (m²)": "LULC Area (m²)",
        "Area (acres)": "LULC Area (acres)",
        "Percent Subbasin": "Percent of Subbasin"})

# Sort values by subbasin and dominant LULC area

lulc_export_df = lulc_export_df.sort_values(
    by=["Subbasin ID", "LULC Area (m²)"],
    ascending=[True, False])

print("Clean LULC export table prepared.")

display(lulc_export_df.head(5))

# Prepare clean soils export table

soils_export_df = soils_subbasin_long_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "MUKEY_ID",
        "MUKEY",
        "Area (m²)",
        "Area (acres)",
        "Percent Subbasin",
        "Hydrologic Soil Group"]].copy()

# Rename columns

soils_export_df = soils_export_df.rename(
    columns={
        "MUKEY_ID": "MUKEY ID",
        "Area (m²)": "MUKEY Area (m²)",
        "Area (acres)": "MUKEY Area (acres)",
        "Percent Subbasin": "Percent of Subbasin"})

# Sort values by subbasin and dominant soil area

soils_export_df = soils_export_df.sort_values(
    by=["Subbasin ID", "MUKEY Area (m²)"],
    ascending=[True, False])

print("Clean soils export table prepared.")

display(soils_export_df.head(5))

# Prepare clean slope export table

slope_export_df = slope_subbasin_long_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "Slope_ID",
        "Slope_Class",
        "Area (m²)",
        "Area (acres)",
        "Percent Subbasin"]].copy()

# Rename columns

slope_export_df = slope_export_df.rename(
    columns={
        "Slope_ID": "Slope Class",
        "Slope_Class": "Slope Class Description",
        "Area (m²)": "Slope Area (m²)",
        "Area (acres)": "Slope Area (acres)",
        "Percent Subbasin": "Percent of Subbasin"})

# Sort values by subbasin and dominant slope class area

slope_export_df = slope_export_df.sort_values(
    by=["Subbasin ID", "Slope Class"],
    ascending=[True, True])

print("Clean slope export table prepared.")

display(slope_export_df.head(5))

# Preview dominant LULC dataframe fields

print("Dominant LULC dataframe fields:")

for field in lulc_dominant_df.columns:
    print(f"- {field}")

# Prepare clean dominant LULC export table

lulc_dominant_export_df = lulc_dominant_df[
    [
        "Subbasin ID",
        "RILC Code",
        "RILC Description",
        "LULC ID",
        "SWAT LULC Code",
        "Area (m²)",
        "Area (acres)",
        "Percent Subbasin"]].copy()

# Rename columns

lulc_dominant_export_df = lulc_dominant_export_df.rename(
    columns={
        "RILC Code": "NLCD Code",
        "RILC Description": "NLCD Description",
        "LULC ID": "SWAT ID",
        "Area (m²)": "Dominant LULC Area (m²)",
        "Area (acres)": "Dominant LULC Area (acres)",
        "Percent Subbasin": "Percent of Subbasin"})

print("Clean dominant LULC export table prepared.")

display(lulc_dominant_export_df.head(5))

# Preview dominant soils dataframe fields

print("Dominant soils dataframe fields:")

for field in soils_dominant_df.columns:
    print(f"- {field}")

# Prepare clean dominant soils export table

soils_dominant_export_df = soils_dominant_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "MUKEY_ID",
        "MUKEY",
        "Hydrologic Soil Group",
        "MUKEY Area (m²)",
        "MUKEY Area (acres)",
        "Percent of Subbasin"]].copy()

# Rename columns

soils_dominant_export_df = soils_dominant_export_df.rename(
    columns={
        "MUKEY_ID": "MUKEY ID",
        "MUKEY Area (m²)": "Dominant MUKEY Area (m²)",
        "MUKEY Area (acres)": "Dominant MUKEY Area (acres)"})

print("Clean dominant soils export table prepared.")

display(soils_dominant_export_df.head(5))

# Preview dominant slope dataframe fields

print("Dominant slope dataframe fields:")

for field in slope_dominant_df.columns:
    print(f"- {field}")

# Prepare clean dominant slope export table

slope_dominant_export_df = slope_dominant_df[
    [
        "Subbasin ID",
        "Subbasin Area (m²)",
        "Slope_ID",
        "Slope_Class",
        "Slope Area (m²)",
        "Slope Area (acres)",
        "Percent of Subbasin"]].copy()

# Rename columns

slope_dominant_export_df = slope_dominant_export_df.rename(
    columns={
        "Slope_ID": "Slope Class",
        "Slope_Class": "Slope Class Description",
        "Slope Area (m²)": "Dominant Slope Area (m²)",
        "Slope Area (acres)": "Dominant Slope Area (acres)"})

print("Clean dominant slope export table prepared.")

display(slope_dominant_export_df.head(5))

# Prepare dominant LULC join table

dominant_lulc_join_df = lulc_dominant_df[
    [
        "Subbasin ID",
        "RILC Description",
        "SWAT LULC Code",
        "Percent Subbasin"]].copy()

dominant_lulc_join_df = dominant_lulc_join_df.rename(
    columns={
        "Subbasin ID": "Subbasin",
        "RILC Description": "Dominant_LULC",
        "SWAT LULC Code": "SWAT_LULC",
        "Percent Subbasin": "LULC_Pct"})

print("Dominant LULC join table prepared.")

display(dominant_lulc_join_df.head(5))

# Prepare dominant soils join table

dominant_soils_join_df = soils_dominant_df[
    [
        "Subbasin ID",
        "Hydrologic Soil Group",
        "Percent of Subbasin"]].copy()

dominant_soils_join_df = dominant_soils_join_df.rename(
    columns={
        "Subbasin ID": "Subbasin",
        "Hydrologic Soil Group": "Dominant_HSG",
        "Percent of Subbasin": "HSG_Pct"})

print("Dominant soils join table prepared.")

display(dominant_soils_join_df.head(5))

# Prepare dominant slope join table

dominant_slope_join_df = slope_dominant_df[
    [
        "Subbasin ID",
        "Slope_Class",
        "Percent of Subbasin"]].copy()

dominant_slope_join_df = dominant_slope_join_df.rename(
    columns={
        "Subbasin ID": "Subbasin",
        "Slope_Class": "Dominant_Slope",
        "Percent of Subbasin": "Slope_Pct"})

print("Dominant slope join table prepared.")

display(dominant_slope_join_df.head(5))

# Preview long-format export tables

clean_export_tables = {
    "Clean LULC Export": lulc_export_df,
    "Clean Soils Export": soils_export_df,
    "Clean Slope Export": slope_export_df}

for name, df in clean_export_tables.items():

    print(f"\n{name}")
    print(f"Rows    : {len(df):,}")
    print(f"Columns : {len(df.columns):,}")

    display(df.head(5))

# Preview dominant export tables

dominant_export_tables = {
    "Dominant LULC Export": lulc_dominant_export_df,
    "Dominant Soils Export": soils_dominant_export_df,
    "Dominant Slope Export": slope_dominant_export_df}

for name, df in dominant_export_tables.items():

    print(f"\n{name}")
    print(f"Rows    : {len(df):,}")
    print(f"Columns : {len(df.columns):,}")

    display(df.head(5))

# Preview dominant join tables

dominant_join_preview_tables = {
    "Dominant LULC Join": dominant_lulc_join_df,
    "Dominant Soils Join": dominant_soils_join_df,
    "Dominant Slope Join": dominant_slope_join_df}

for name, df in dominant_join_preview_tables.items():

    print(f"\n{name}")
    print(f"Rows    : {len(df):,}")
    print(f"Columns : {len(df.columns):,}")

    display(df.head(5))

# Final output preview QA

preview_outputs = {
    "Clean LULC Export": lulc_export_df,
    "Clean Soils Export": soils_export_df,
    "Clean Slope Export": slope_export_df,
    "Dominant LULC Export": lulc_dominant_export_df,
    "Dominant Soils Export": soils_dominant_export_df,
    "Dominant Slope Export": slope_dominant_export_df,
    "Dominant LULC Join": dominant_lulc_join_df,
    "Dominant Soils Join": dominant_soils_join_df,
    "Dominant Slope Join": dominant_slope_join_df}

empty_outputs = []

print("Final output preview QA:")

for name, df in preview_outputs.items():
    if df is None or len(df) == 0:
        empty_outputs.append(name)
        print(f"{name:<24}: EMPTY")

    else:
        print(f"{name:<24}: OK | {len(df):,} rows")

if empty_outputs:
    raise ValueError(f"Empty output dataframe(s): {empty_outputs}")

print("")
print("Final output preview QA: PASS")

# Export clean long summary CSVs

lulc_export_df.to_csv(lulc_subbasin_long_csv, index=False)

soils_export_df.to_csv(soils_subbasin_long_csv, index=False)

slope_export_df.to_csv(slope_subbasin_long_csv, index=False)

print("Clean long summary CSVs exported.")
print(f"LULC  : {lulc_subbasin_long_csv}")
print(f"Soils : {soils_subbasin_long_csv}")
print(f"Slope : {slope_subbasin_long_csv}")

# Export dominant summary CSVs

lulc_dominant_export_df.to_csv(lulc_dominant_summary_csv, index=False)

soils_dominant_export_df.to_csv(soils_dominant_summary_csv, index=False)

slope_dominant_export_df.to_csv(slope_dominant_summary_csv, index=False)

print("Dominant summary CSVs exported.")
print(f"LULC  : {lulc_dominant_summary_csv}")
print(f"Soils : {soils_dominant_summary_csv}")
print(f"Slope : {slope_dominant_summary_csv}")

# Export dominant frequency CSV

dominant_lulc_plot_df.to_csv(lulc_dominant_frequency_csv, index=False)

print("Dominant LULC frequency CSV exported.")
print(f"CSV: {lulc_dominant_frequency_csv}")

# Export dominant join tables to geodatabase

dominant_join_exports = [
    {
        "name": "LULC",
        "dataframe": dominant_lulc_join_df,
        "table": dominant_lulc_join_table},
    {
        "name": "Soils",
        "dataframe": dominant_soils_join_df,
        "table": dominant_soils_join_table},
    {
        "name": "Slope",
        "dataframe": dominant_slope_join_df,
        "table": dominant_slope_join_table}]

print("Exporting dominant join tables to project geodatabase...")

for item in dominant_join_exports:
    dataframe_to_gdb_table(item["dataframe"], item["table"])

    row_count = int(arcpy.management.GetCount(item["table"])[0])

    print(f"{item['name']:<6}: exported | Rows: {row_count:,}")

print("Dominant join tables exported.")

# Preview subbasin polygon fields

print("Subbasin polygon fields:")

for field in arcpy.ListFields(subbasin_polygons):
    print(field.name)

print("")
print(f"Using subbasin join field: {subbasin_join_field}")

# Remove existing dominant fields before rejoining

existing_joined_fields = [
    "Dominant_LULC",
    "SWAT_LULC",
    "LULC_Pct",
    "Dominant_HSG",
    "HSG_Pct",
    "Dominant_Slope",
    "Slope_Pct"]

subbasin_field_names = [field.name for field in arcpy.ListFields(subbasin_polygons)]

fields_to_delete = [
    field
    for field in existing_joined_fields
    if field in subbasin_field_names]

if fields_to_delete:
    arcpy.management.DeleteField(subbasin_polygons, fields_to_delete)
    print(f"Deleted existing joined fields: {fields_to_delete}")

else:
    print("No existing joined fields to delete.")

# Join dominant LULC fields

arcpy.management.JoinField(
    in_data=subbasin_polygons,
    in_field=subbasin_join_field,
    join_table=dominant_lulc_join_table,
    join_field="Subbasin",
    fields=[
        "Dominant_LULC",
        "SWAT_LULC",
        "LULC_Pct"])

print("Dominant LULC fields joined to subbasin polygons.")

# Join dominant soils fields

arcpy.management.JoinField(
    in_data=subbasin_polygons,
    in_field=subbasin_join_field,
    join_table=dominant_soils_join_table,
    join_field="Subbasin",
    fields=[
        "Dominant_HSG",
        "HSG_Pct"])

print("Dominant soils fields joined to subbasin polygons.")

# Join dominant slope fields

arcpy.management.JoinField(
    in_data=subbasin_polygons,
    in_field=subbasin_join_field,
    join_table=dominant_slope_join_table,
    join_field="Subbasin",
    fields=[
        "Dominant_Slope",
        "Slope_Pct"])

print("Dominant slope fields joined to subbasin polygons.")

# Update joined field aliases

field_aliases = {
    "Dominant_LULC": "Dominant Land Cover",
    "SWAT_LULC": "SWAT Land Cover Code",
    "LULC_Pct": "Dominant Land Cover Percent",
    "Dominant_HSG": "Dominant Hydrologic Soil Group",
    "HSG_Pct": "Dominant HSG Percent",
    "Dominant_Slope": "Dominant Slope Class",
    "Slope_Pct": "Dominant Slope Percent"}

subbasin_field_names = [
    field.name
    for field in arcpy.ListFields(subbasin_polygons)]

for field_name, field_alias in field_aliases.items():
    if field_name in subbasin_field_names:

        arcpy.management.AlterField(in_table=subbasin_polygons, field=field_name, new_field_alias=field_alias)
        print(f"Alias updated: {field_name} → {field_alias}")

print("Joined field aliases updated.")

# Final joined field QA

joined_fields = [
    "Dominant_LULC",
    "SWAT_LULC",
    "LULC_Pct",
    "Dominant_HSG",
    "HSG_Pct",
    "Dominant_Slope",
    "Slope_Pct"]

subbasin_fields = [
    field.name
    for field in arcpy.ListFields(subbasin_polygons)]

missing_fields = [
    field
    for field in joined_fields
    if field not in subbasin_fields]

print("Joined field QA:")

if missing_fields:
    raise ValueError(f"Missing joined fields: {missing_fields}")

print("All dominant fields successfully joined.")

# Print Notebook 3 Handoff Summary

print("Notebook 3 handoff summary:")

print("\nClean summary CSVs:")
print(f"LULC  : {lulc_subbasin_long_csv}")
print(f"Soils : {soils_subbasin_long_csv}")
print(f"Slope : {slope_subbasin_long_csv}")

print("\nDominant summary CSVs:")
print(f"LULC  : {lulc_dominant_summary_csv}")
print(f"Soils : {soils_dominant_summary_csv}")
print(f"Slope : {slope_dominant_summary_csv}")

print("\nFigure outputs:")
print(f"LULC composition        : {lulc_composition_figure}")
print(f"Dominant LULC frequency : {lulc_dominant_frequency_figure}")
print(f"Slope distribution      : {slope_distribution_figure}")
print(f"HSG distribution        : {hsg_distribution_figure}")

print("\nGeodatabase join tables:")
print(f"LULC  : {dominant_lulc_join_table}")
print(f"Soils : {dominant_soils_join_table}")
print(f"Slope : {dominant_slope_join_table}")

print("\nFinal GIS layer updated:")
print(f"Subbasins : {subbasin_polygons}")

print("")
print("TASK 07 complete: Dominant fields joined to subbasin polygons.")
