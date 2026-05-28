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

arcpy.ImportToolbox(os.path.join(toolbox_folder, "Field_Tools.pyt"), "field_tools")
arcpy.ImportToolbox(os.path.join(toolbox_folder, "Raster_Tools.pyt"), "raster_tools")
arcpy.ImportToolbox(os.path.join(toolbox_folder, "Vector_Tools.pyt"), "vector_tools")

print("Custom Python toolboxes imported.")
print("Field tools  : field_tools")
print("Raster tools : raster_tools")
print("Vector tools : vector_tools")

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

# Define source data folders

source_data_folder = os.path.join(base_folder, "GIS_Data")
ri_data            = os.path.join(source_data_folder, "RI_State_Data")
lidar_data         = os.path.join(source_data_folder, "LIDAR")

print("Source data folders defined.")
print(f"Source data : {source_data_folder}")
print(f"RI data     : {ri_data}")
print(f"LIDAR data  : {lidar_data}")

# Create Project GDB and Temp GDB if it does not already exist

if not arcpy.Exists(project_gdb):
    arcpy.management.CreateFileGDB(out_folder_path=project_folder, out_name=f"{project_name}.gdb")
    print("Project GDB created.")

else:
    print("Project GDB already exists.")

# temp gdb

if not arcpy.Exists(temp_gdb):
    arcpy.management.CreateFileGDB(out_folder_path=project_folder, out_name="Temp.gdb")
    print("Temp GDB created.")

else:
    print("Temp GDB already exists.")

# Create project output folders

for folder in [
    outputs_folder,
    tables_folder,
    charts_folder]:

    os.makedirs(folder, exist_ok=True)

print("Output folders created or confirmed.")

# Configure workspace

arcpy.env.workspace = temp_gdb
arcpy.env.scratchWorkspace = temp_gdb
arcpy.env.overwriteOutput = True

# Define Coordinate System

ri_stateplane_meters = arcpy.SpatialReference(32130)
arcpy.env.outputCoordinateSystem = ri_stateplane_meters

print("ArcGIS environment configured.")
print(f"Workspace         : {arcpy.env.workspace}")
print(f"Scratch workspace : {arcpy.env.scratchWorkspace}")
print(f"Output CRS        : {ri_stateplane_meters.name}")
print(f"CRS WKID          : {ri_stateplane_meters.factoryCode}")

# Define shared project constants

study_area_name = "Queen_Usquepaug"

stream_threshold = 35000

swat_cell_size = 10

sq_m_to_acres = 0.000247105

print("Project constants defined.")
print(f"Study area            : {study_area_name}")
print(f"Stream threshold      : {stream_threshold:,}")
print(f"SWAT cell size        : {swat_cell_size} m")
print(f"Square meters to acres: {sq_m_to_acres}")

# Define source datasets
# Replace placeholder folders/files with local source data.

# National data
huc12 = os.path.join(source_data_folder, "USGS", "<NHDPLUS_GDB>", "WBD", "WBDHU12")

# Rhode Island source datasets
town_boundaries = os.path.join(ri_data, "Towns.shp")
rivers = os.path.join(ri_data, "<RIVERS_FOLDER>", "<RIVERS_FILE>.shp")
soils = os.path.join(ri_data, "Soils", "<SOILS_FILE>.shp")
lulc = os.path.join(ri_data, "<LAND_COVER_FOLDER>", "<LAND_COVER_FILE>.shp")

# DEM source dataset
dem_original = os.path.join(lidar_data, "<DEM_FOLDER>", "<DEM_NAME>")

print("Source data paths defined.")

# Validate Required Source Inputs

required_inputs = {
    "HUC12": huc12,
    "Town Boundaries": town_boundaries,
    "Rivers": rivers,
    "Soils": soils,
    "LULC": lulc,
    "DEM": dem_original}

missing_inputs = []

print("Input dataset QA:")

for name, path in required_inputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<18}: {'FOUND' if exists else 'MISSING'}")

    if not exists:
        missing_inputs.append(name)

if missing_inputs:
    raise FileNotFoundError(f"Missing required inputs: {missing_inputs}")

print("")
print("Input dataset QA: PASS")

# Define Study Area and Prepared Vector Outputs

study_area = os.path.join(project_gdb, f"{study_area_name}_StudyArea")

rivers_projected = os.path.join(project_gdb, "Rivers_Projected")
soils_projected  = os.path.join(project_gdb, "Soils_Projected")
lulc_projected   = os.path.join(project_gdb, "LULC_Projected")
towns_projected  = os.path.join(project_gdb, "Towns_Projected")

print("Study area and prepared vector outputs defined.")

# Define DEM and hydrology outputs

dem_hydro    = os.path.join(project_gdb, "DEM_HydroConditioned")
flow_dir     = os.path.join(project_gdb, "Flow_Direction")
flow_acc     = os.path.join(project_gdb, "Flow_Accumulation")
flow_acc_log = os.path.join(project_gdb, "Flow_Accumulation_Log")

print("DEM and hydrology outputs defined.")

# Define stream and subbasin outputs

stream_links      = os.path.join(project_gdb, f"StreamLinks_T{stream_threshold}")
stream_network    = os.path.join(project_gdb, f"StreamNetwork_T{stream_threshold}")

subbasin_raster   = os.path.join(project_gdb, f"SubbasinRaster_T{stream_threshold}")
subbasin_polygons = os.path.join(project_gdb, f"SubbasinPolygons_T{stream_threshold}")

print("Stream and subbasin outputs defined.")
print(f"Stream threshold : {stream_threshold:,}")
print("Notebook 1 outputs defined.")

# Optional Clear Temp GDB

clear_temp_gdb = False

if clear_temp_gdb:
    arcpy.env.workspace = temp_gdb

    datasets = (
        (arcpy.ListRasters() or []) +
        (arcpy.ListFeatureClasses() or []) +
        (arcpy.ListTables() or []) +
        (arcpy.ListDatasets() or []))

    print("Clearing Temp GDB:")
    print(f"Items found: {len(datasets):,}")

    deleted_count = 0
    skipped_count = 0

    for dataset in datasets:
        try:
            arcpy.management.Delete(dataset)
            deleted_count += 1

        except Exception:
            skipped_count += 1

    print(f"Deleted items: {deleted_count:,}")
    print(f"Skipped items: {skipped_count:,}")
    print("Temp GDB cleanup complete.")

else:
    print("Temp GDB cleanup skipped.")

# Define temporary vector outputs

study_area_selected = os.path.join(temp_gdb, "StudyArea_Selected")

rivers_clipped = os.path.join(temp_gdb, "Rivers_Clipped")
soils_clipped  = os.path.join(temp_gdb, "Soils_Clipped")
lulc_clipped   = os.path.join(temp_gdb, "LULC_Clipped")
towns_clipped  = os.path.join(temp_gdb, "Towns_Clipped")

print("Temporary vector outputs defined.")

# Confirm required HUC12 fields exist

huc12_fields = [field.name for field in arcpy.ListFields(huc12)]

required_huc12_fields = ["Name"]

missing_huc12_fields = [
    field
    for field in required_huc12_fields
    if field not in huc12_fields]

print("HUC12 field QA:")
print(f"Field count : {len(huc12_fields):,}")

for field in required_huc12_fields:
    status = "OK" if field in huc12_fields else "MISSING"
    print(f"{field:<12}: {status}")

if missing_huc12_fields:
    raise ValueError(f"Missing required HUC12 field(s): {missing_huc12_fields}")

print("")
print("HUC12 field QA: PASS")

# Define Study Area Selection Query

where_clause    = "Name = 'Usquepaug River'"

print(f" Study area name : {study_area_name}")
print(f" Where clause    : {where_clause}")

# Create HUC12 feature layer

huc12_layer = "huc12_layer"

arcpy.management.MakeFeatureLayer(in_features=huc12, out_layer=huc12_layer)

print("HUC12 feature layer created.")

# Select study area watershed

arcpy.management.SelectLayerByAttribute(in_layer_or_view=huc12_layer, selection_type="NEW_SELECTION", where_clause=where_clause)

print(f"Selected features.")

# Check Selected Feature Count

selected_count = int(arcpy.management.GetCount(huc12_layer)[0])

print(f"Selected features: {selected_count}")

if selected_count == 0:
    raise ValueError("No HUC12 selected. Check field name or watershed name.")

if selected_count > 1:
    raise ValueError("More than one HUC12 selected. Check selection query.")

# Export selected study area to Temp GDB

if arcpy.Exists(study_area_selected):
    arcpy.management.Delete(study_area_selected)

arcpy.management.CopyFeatures(in_features=huc12_layer, out_feature_class=study_area_selected)

print("Selected study area exported.")

# Clear selection and delete temporary layer

arcpy.management.SelectLayerByAttribute(in_layer_or_view=huc12_layer, selection_type="CLEAR_SELECTION")

arcpy.management.Delete(in_data=huc12_layer)

print("Temporary HUC12 layer cleaned up.")

# Project Selected Study Area

if arcpy.Exists(study_area):
    arcpy.management.Delete(study_area)

arcpy.management.Project(in_dataset=study_area_selected, out_dataset=study_area, out_coor_system=ri_stateplane_meters)

print("Study area projected.")

# Confirm study area was created correctly

if not arcpy.Exists(study_area):
    raise FileNotFoundError(f"Study area missing: {study_area}")

study_area_count = int(arcpy.management.GetCount(study_area)[0])
desc = arcpy.Describe(study_area)

crs_ok = (desc.spatialReference.factoryCode == ri_stateplane_meters.factoryCode)

print("Final study area QA:")
print(f"Feature count : {study_area_count:,}")
print(f"CRS check     : {'PASS' if crs_ok else 'FAIL'}")

if study_area_count != 1 or not crs_ok:
    raise ValueError("Study area QA failed.")

print("")
print("Final study area QA: PASS")

# Check source coordinate systems

source_crs_summary = {}

for name, path in required_inputs.items():
    sr = arcpy.Describe(path).spatialReference
    source_crs_summary[name] = sr.name

unique_crs = sorted(set(source_crs_summary.values()))

print("Source coordinate system QA:")
print(f"Input datasets : {len(source_crs_summary):,}")
print(f"Unique CRS     : {len(unique_crs):,}")

for crs in unique_crs:
    print(f"- {crs}")

print("")
print("Source coordinate system QA: PASS")

# Clip and project rivers

arcpy.vector_tools.Clip_Project_Dataset(
    input_features=rivers,
    clip_features=study_area,
    output_features=rivers_projected,
    spatial_reference_wkid=ri_stateplane_meters.factoryCode,
    repair_geometry=True,
    temp_workspace=temp_gdb)

river_count = int(arcpy.management.GetCount(rivers_projected)[0])

print("Rivers prepared.")
print(f"River features: {river_count:,}")

# Clip and project land cover

arcpy.vector_tools.Clip_Project_Dataset(
    input_features=lulc,
    clip_features=study_area,
    output_features=lulc_projected,
    spatial_reference_wkid=ri_stateplane_meters.factoryCode,
    repair_geometry=True,
    temp_workspace=temp_gdb)

lulc_count = int(arcpy.management.GetCount(lulc_projected)[0])

print("Rivers prepared.")
print(f"River features: {lulc_count:,}")

# Clip and project soils

arcpy.vector_tools.Clip_Project_Dataset(
    input_features=soils,
    clip_features=study_area,
    output_features=soils_projected,
    spatial_reference_wkid=ri_stateplane_meters.factoryCode,
    repair_geometry=True,
    temp_workspace=temp_gdb)

soils_count = int(arcpy.management.GetCount(soils_projected)[0])

print("Rivers prepared.")
print(f"River features: {soils_count:,}")

# Clip and project towns

arcpy.vector_tools.Clip_Project_Dataset(
    input_features=town_boundaries,
    clip_features=study_area,
    output_features=towns_projected,
    spatial_reference_wkid=ri_stateplane_meters.factoryCode,
    repair_geometry=True,
    temp_workspace=temp_gdb)

towns_count = int(arcpy.management.GetCount(towns_projected)[0])

print("Rivers prepared.")
print(f"River features: {towns_count:,}")

# Prepared vector QA

vector_outputs = {
    "Study Area": study_area,
    "Rivers": rivers_projected,
    "Soils": soils_projected,
    "LULC": lulc_projected,
    "Towns": towns_projected}

missing_vectors = []
empty_vectors = []
crs_failures = []

print("Prepared vector QA:")

for name, path in vector_outputs.items():
    if not arcpy.Exists(path):
        missing_vectors.append(name)

        continue

    count = int(arcpy.management.GetCount(path)[0])
    desc = arcpy.Describe(path)
    crs_ok = (desc.spatialReference.factoryCode == ri_stateplane_meters.factoryCode)

    if count == 0:
        empty_vectors.append(name)

    if not crs_ok:
        crs_failures.append(name)

    print(
        f"{name:<14}: "
        f"{count:>6,} features | "
        f"CRS {'PASS' if crs_ok else 'FAIL'}")

if missing_vectors or empty_vectors or crs_failures:
    raise ValueError("Prepared vector QA failed.")

print("")
print("Prepared vector QA: PASS")

# Define temporary DEM preparation outputs

dem_masked    = os.path.join(temp_gdb, "DEM_Masked")
dem_projected = os.path.join(temp_gdb, f"DEM_{swat_cell_size}m")

print("DEM preparation outputs defined.")
print(f"SWAT cell size : {swat_cell_size} m")

# Check current DEM

dem = dem_original

print("Current DEM properties.")
print(f" Original DEM   : {dem_original}")
print(f" SWAT cell size : {swat_cell_size} meters")
print(f" Current DEM    : {dem}")

# Extract and project DEM

dem_extract_result = arcpy.raster_tools.Extract_Project_Raster_Dataset(
    input_raster=dem,
    study_area=study_area,
    output_raster=dem_projected,
    target_crs_wkid=ri_stateplane_meters.factoryCode,
    output_cell_size=swat_cell_size,
    resampling_type="BILINEAR")

dem = dem_projected

print("DEM resampled to study area.")
print(f"Current DEM: {dem}")

# Calculate DEM statistics

arcpy.management.CalculateStatistics(dem)

print("DEM statistics calculated.")

# QA - Working DEM Properties

if not arcpy.Exists(dem):
    raise FileNotFoundError(f"Active DEM missing: {dem}")

dem_description = arcpy.Describe(dem)

cell_width   = dem_description.meanCellWidth
cell_height  = dem_description.meanCellHeight
crs_ok       = (dem_description.spatialReference.factoryCode == ri_stateplane_meters.factoryCode)
cell_size_ok = (
    round(cell_width, 6) == swat_cell_size and
    round(cell_height, 6) == swat_cell_size)

print("Working DEM QA:")
print(f"Active DEM      : {dem}")
print(f"Projection      : {dem_description.spatialReference.name}")
print(f"Cell width      : {cell_width} m")
print(f"Cell height     : {cell_height} m")
print(f"CRS Check       : {'PASS' if crs_ok else 'FAIL'}")
print(f"Cell Size Check : {'PASS' if cell_size_ok else 'FAIL'}")

print(
    f"\nDEM QA: "
    f"{'PASS' if crs_ok and cell_size_ok else 'FAIL'}")

# Define terrain preparation outputs

sink_group_summary_csv = os.path.join(tables_folder, "Sink_Group_Size_Summary.csv")

flow_dir_raw     = os.path.join(temp_gdb, "FlowDir_Raw")
flow_acc_raw     = os.path.join(temp_gdb, "FlowAcc_Raw")
flow_acc_raw_log = os.path.join(temp_gdb, "FlowAcc_Raw_Log")

sinks            = os.path.join(temp_gdb, "Sinks")
sink_groups      = os.path.join(temp_gdb, "Sink_Groups")
ponds            = os.path.join(temp_gdb, "Real_Sinks")

print("Terrain preparation outputs defined.")

# Define sink interpretation parameters

# Minimum sink size to preserve as a real depression
# 80 cells ≈ 8,000 sq m ≈ 2 acres at 10 m resolution

real_sink_min_cells = 80

# Small elevation offset used when restoring preserved sinks
# 0.01 m = 1 cm

sink_restore_depth = 0.01

print(f"Real sink minimum size : {real_sink_min_cells} cells")
print(f"Sink restore depth     : {sink_restore_depth} m")
print(f"Current DEM            : {dem}")

# Create raw flow direction raster

if arcpy.Exists(flow_dir_raw):
    arcpy.management.Delete(flow_dir_raw)

flow_dir_raw_result = FlowDirection(in_surface_raster=dem, force_flow="NORMAL")

flow_dir_raw_result.save(flow_dir_raw)

print("Raw flow direction raster created.")

# Create raw flow accumulation raster

if arcpy.Exists(flow_acc_raw):
    arcpy.management.Delete(flow_acc_raw)

flow_acc_raw_result = FlowAccumulation(in_flow_direction_raster=flow_dir_raw)

flow_acc_raw_result.save(flow_acc_raw)

print("Raw flow accumulation raster created.")

# Create log-transformed raw flow accumulation raster

if arcpy.Exists(flow_acc_raw_log):
    arcpy.management.Delete(flow_acc_raw_log)

flow_acc_raw_log_result = Log10(Raster(flow_acc_raw) + 1)

flow_acc_raw_log_result.save(flow_acc_raw_log)

print("Raw log flow accumulation raster created.")

# Create sink raster

if arcpy.Exists(sinks):
    arcpy.management.Delete(sinks)

sink_result = Sink(in_flow_direction_raster=flow_dir_raw)

sink_result.save(sinks)

print("Sink raster created.")

# Group connected sink regions

if arcpy.Exists(sink_groups):
    arcpy.management.Delete(sink_groups)

sink_group_result = RegionGroup(in_raster=sinks, number_neighbors="EIGHT", zone_connectivity="WITHIN", add_link="ADD_LINK")

sink_group_result.save(sink_groups)

print("Sink regions grouped.")

# Build Sink Group Attribute Table - required for sink group size filtering using COUNT.

arcpy.management.BuildRasterAttributeTable(in_raster=sink_groups, overwrite="Overwrite")

print("Sink group attribute table built.")

# Summarize sink group sizes

sink_counts = []

with arcpy.da.SearchCursor(sink_groups, ["Value", "Count"]) as cursor:
    for value, count in cursor:
        area_sq_m = (count * swat_cell_size * swat_cell_size)
        area_acres = area_sq_m * sq_m_to_acres

        sink_counts.append((value, count, area_sq_m, area_acres))

sink_counts = sorted(
    sink_counts,
    key=lambda x: x[1],
    reverse=True)

print("Sink groups summarized.")
print(f"Sink groups found: {len(sink_counts)}")

# Preview largest sink groups

print("Largest sink groups:")

for value, count, area_sq_m, area_acres in sink_counts[:20]:

    print(
        f"Group {value}: "
        f"{count} cells | "
        f"{area_sq_m:,.0f} sq m | "
        f"{area_acres:,.2f} acres")

# Export Sink Group Summary to CSV

if os.path.exists(sink_group_summary_csv):
    os.remove(sink_group_summary_csv)
    print("Existing sink group summary deleted.")

with open(sink_group_summary_csv, "w", newline="") as csvfile:

    writer = csv.writer(csvfile)

    writer.writerow(["Sink_Group_Value", "Cell_Count", "Area_sq_m", "Area_acres"])

    for row in sink_counts:
        writer.writerow(row)

print("Sink group summary exported.")
print(f"Output: {sink_group_summary_csv}")

# Define temporary terrain conditioning outputs

ponds0_else1     = os.path.join(temp_gdb, "Ponds0_Else1")
ponds_mask       = os.path.join(temp_gdb, "Ponds_Mask")

filled_dem          = os.path.join(temp_gdb, "DEM_Filled_AllSinks")
sink_restore_raster = os.path.join(temp_gdb, "Sink_Restore_Raster")

print("Terrain conditioning outputs defined.")

# Extract large sink regions to preserve. Small sink groups become NoData; preserved sink groups become 1

if arcpy.Exists(ponds):
    arcpy.management.Delete(ponds)

ponds_result = SetNull(in_conditional_raster=sink_groups, in_false_raster_or_constant=1, where_clause=f"COUNT < {real_sink_min_cells}")

ponds_result.save(ponds)

print("Large sink regions extracted.")

# Create inverse sink raster. Preserved sinks = 0; all other cells = 1

if arcpy.Exists(ponds0_else1):
    arcpy.management.Delete(ponds0_else1)

ponds0_else1_result = IsNull(in_raster=ponds)

ponds0_else1_result.save(ponds0_else1)

print("0/1 pond raster created.")

# Create preserved sink mask. Preserved sinks = 1; all other cells = 0

if arcpy.Exists(ponds_mask):
    arcpy.management.Delete(ponds_mask)

ponds_mask_result = EqualTo(in_raster_or_constant1=ponds0_else1, in_raster_or_constant2=0)

ponds_mask_result.save(ponds_mask)

print("Preserved sink mask created.")

# Confirm pond mask has cells with value 1

arcpy.management.BuildRasterAttributeTable(in_raster=ponds_mask, overwrite="Overwrite")

with arcpy.da.SearchCursor(ponds_mask, ["Value", "Count"]) as cursor:
    for value, count in cursor:
        area_sq_m = count * swat_cell_size * swat_cell_size
        area_acres = area_sq_m * sq_m_to_acres
        print(f"Value {value}: {count:,.0f} cells | {area_acres:,.2f} acres")

# Fill all sinks in DEM

if arcpy.Exists(filled_dem):
    arcpy.management.Delete(filled_dem)

filled_dem_result = Fill(in_surface_raster=dem)
filled_dem_result.save(filled_dem)

dem = filled_dem

print("Filled DEM created.")
print(f"Current DEM: {dem}")

# Create sink restore raster

if arcpy.Exists(sink_restore_raster):
    arcpy.management.Delete(sink_restore_raster)

sink_restore_result = Times(in_raster_or_constant1=ponds_mask, in_raster_or_constant2=sink_restore_depth)

sink_restore_result.save(sink_restore_raster)

print("Sink restore raster created.")

# Create hydro-conditioned DEM

if arcpy.Exists(dem_hydro):
    arcpy.management.Delete(dem_hydro)
    print("Existing hydro-conditioned DEM deleted.")

dem_hydro_result = Minus(in_raster_or_constant1=dem, in_raster_or_constant2=sink_restore_raster)
dem_hydro_result.save(dem_hydro)

dem = dem_hydro

print("Hydro-conditioned DEM created.")
print(f"Current DEM: {dem}")

# Set raster environment to hydro-conditioned DEM

arcpy.env.snapRaster = dem
arcpy.env.cellSize   = dem
arcpy.env.extent     = dem
arcpy.env.mask       = study_area

desc = arcpy.Describe(dem)

print("Raster environment updated to hydro DEM.")
print(f"DEM         : {dem}")
print(f"Snap Raster : {arcpy.env.snapRaster}")
print(f"Cell Size   : {desc.meanCellWidth}")
print(f"Mask        : {arcpy.env.mask}")

# Terrain conditioning output QA

terrain_conditioning_outputs = {
    "Sink Group Summary CSV": sink_group_summary_csv,
    "Filled DEM": filled_dem,
    "Sink Restore Raster": sink_restore_raster,
    "Hydro DEM": dem_hydro}

qa_pass = True

print("Terrain conditioning output QA:")

for name, path in terrain_conditioning_outputs.items():

    exists = (
        os.path.exists(path)
        if str(path).lower().endswith(".csv")
        else arcpy.Exists(path))

    print(f"{name:<24}: {'OK' if exists else 'MISSING'}")

    if not exists:
        qa_pass = False

print(f"\nOutput QA: {'PASS' if qa_pass else 'CHECK'}")

# Hydro-conditioned DEM properties QA

if not arcpy.Exists(dem_hydro):
    raise FileNotFoundError(f"Hydro-conditioned DEM missing: {dem_hydro}")

desc = arcpy.Describe(dem_hydro)

crs_ok = (desc.spatialReference.factoryCode == ri_stateplane_meters.factoryCode)

cell_size_ok = (round(desc.meanCellWidth, 6) == swat_cell_size and round(desc.meanCellHeight, 6) == swat_cell_size)

print("Hydro-conditioned DEM QA:")
print(f"Projection      : {desc.spatialReference.name}")
print(f"Cell size       : {desc.meanCellWidth:.2f} m x {desc.meanCellHeight:.2f} m")
print(f"CRS check       : {'PASS' if crs_ok else 'CHECK'}")
print(f"Cell size check : {'PASS' if cell_size_ok else 'CHECK'}")

print("")
print(f"DEM QA: {'PASS' if crs_ok and cell_size_ok else 'CHECK'}")

# DEM conditioning difference QA
# Difference = hydro-conditioned DEM minus fully filled DEM

dem_difference = Minus(in_raster_or_constant1=dem_hydro, in_raster_or_constant2=filled_dem)

min_difference = arcpy.management.GetRasterProperties(dem_difference, "MINIMUM")[0]

max_difference = arcpy.management.GetRasterProperties(dem_difference, "MAXIMUM")[0]

mean_difference = arcpy.management.GetRasterProperties(dem_difference, "MEAN")[0]

print("DEM conditioning difference QA:")
print(f"Minimum change : {min_difference}")
print(f"Maximum change : {max_difference}")
print(f"Mean change    : {mean_difference}")

# Define Stream Outputs
stream_raster  = os.path.join(temp_gdb, f"StreamRaster_T{stream_threshold}")

print("Temporary stream raster output defined.")

# Create final flow direction raster

if arcpy.Exists(flow_dir):
    arcpy.management.Delete(flow_dir)

flow_dir_result = FlowDirection(in_surface_raster=dem, force_flow="NORMAL")

flow_dir_result.save(flow_dir)

print("Final flow direction raster created.")

# Create final flow accumulation raster. Calculate upstream contributing area for each cell

if arcpy.Exists(flow_acc):
    arcpy.management.Delete(flow_acc)

flow_acc_result = FlowAccumulation(in_flow_direction_raster=flow_dir, data_type="FLOAT")

flow_acc_result.save(flow_acc)

print("Final flow accumulation raster created.")

# Create log-transformed final flow accumulation raster

if arcpy.Exists(flow_acc_log):
    arcpy.management.Delete(flow_acc_log)

flow_acc_log_result = Ln(in_raster_or_constant=Raster(flow_acc) + 1)

flow_acc_log_result.save(flow_acc_log)

print("Final log flow accumulation raster created.")

# Calculate flow accumulation display statistics

arcpy.management.CalculateStatistics(in_raster_dataset=flow_acc_log)

print("Flow log accumulation statistics calculated.")

# Set raster processing environment

arcpy.env.snapRaster = flow_dir
arcpy.env.cellSize   = swat_cell_size
arcpy.env.extent     = study_area
arcpy.env.mask       = study_area

print("Raster environment set for stream extraction.")

# Create stream raster, stream links, and stream network

print("Creating stream raster, stream links, and stream network...")

arcpy.raster_tools.Stream_Network_From_Flow_Accumulation(
    flow_direction=flow_dir,
    flow_accumulation=flow_acc,
    stream_threshold=stream_threshold,
    output_stream_raster=stream_raster,
    output_stream_links=stream_links,
    output_stream_network=stream_network)

# Add stream length metrics (meters)

arcpy.field_tools.Add_Standard_Metric_Field(
    input_features=stream_network,
    metric_type="Length Meters",
    field_name="Stream_Length_m",
    field_alias="Stream Length (m)")

# Add stream length metrics (kilometers)
arcpy.field_tools.Add_Standard_Metric_Field(
    input_features=stream_network,
    metric_type="Length Kilometers",
    field_name="Stream_Length_km",
    field_alias="Stream Length (km)")

# Count stream outputs

stream_count = int(arcpy.management.GetCount(stream_network)[0])

stream_link_count = len([row[0] for row in arcpy.da.SearchCursor(stream_links, ["Value"])])

print("Stream Network QA:")
print(f"Stream threshold : {stream_threshold}")
print(f"Stream features  : {stream_count:,}")
print(f"Stream links     : {stream_link_count:,}")

# Check stream network outputs

stream_outputs = {
    "Flow Direction": flow_dir,
    "Flow Accumulation": flow_acc,
    "Flow Accumulation Log": flow_acc_log,
    "Stream Raster": stream_raster,
    "Stream Links": stream_links,
    "Stream Network": stream_network}

qa_pass = True

print("Stream network output QA:")

for name, path in stream_outputs.items():

    exists = arcpy.Exists(path)

    print(f"{name:<24}: {'OK' if exists else 'MISSING'}")

    if not exists:
        qa_pass = False

print(f"\nStream Network QA: {'PASS' if qa_pass else 'FAIL'}")

print("Permanent subbasin outputs defined.")
print(f" Subbasin raster   : {subbasin_raster}")
print(f" Final polygons    : {subbasin_polygons}")

# Delineate subbasins from stream links

if arcpy.Exists(subbasin_raster):
    arcpy.management.Delete(subbasin_raster)

subbasin_raster_result = Watershed(in_flow_direction_raster=flow_dir, in_pour_point_data=stream_links)

subbasin_raster_result.save(subbasin_raster)

print("Subbasin raster created.")

# Build subbasin raster attribute table

arcpy.management.BuildRasterAttributeTable(in_raster=subbasin_raster, overwrite="Overwrite")

print("Subbasin raster attribute table built.")

# Convert Subbasin Raster to Polygons

if arcpy.Exists(subbasin_polygons):
    arcpy.management.Delete(subbasin_polygons)

arcpy.conversion.RasterToPolygon(
    in_raster=subbasin_raster,
    out_polygon_features=subbasin_polygons,
    simplify="NO_SIMPLIFY",
    raster_field="Value")

print("Subbasin polygons created.")

# Add Subbasin Area Field (m²)

arcpy.field_tools.Add_Standard_Metric_Field(
    input_features=subbasin_polygons,
    metric_type="Area Square Meters",
    field_name="Subbasin_Area_sq_m",
    field_alias="Subbasin Area (m²)")

# Add Subbasin Area Field (acres)

arcpy.field_tools.Add_Standard_Metric_Field(
    input_features=subbasin_polygons,
    metric_type="Area Acres",
    field_name="Subbasin_Area_acres",
    field_alias="Subbasin Area (acres)")

# Define temporary town attribution outputs

subbasin_town_intersect = os.path.join(temp_gdb, "SubbasinTownIntersect")
subbasin_town_stats     = os.path.join(temp_gdb, "SubbasinTownStats")
subbasin_town_dominant  = os.path.join(temp_gdb, "SubbasinTownDominant")

# Check projected town fields

for field in arcpy.ListFields(towns_projected):
    print(field.name)

# Add Dominant Town Attribution

arcpy.vector_tools.Dominant_Overlap_Attribution(
    base_features=subbasin_polygons,
    base_id_field="gridcode",
    overlay_features=towns_projected,
    overlay_attribute_field="NAME",
    output_field_name="Dominant_Town",
    temp_workspace=temp_gdb)

# Alter dominant town field name

arcpy.management.AlterField(in_table=subbasin_polygons, field="Dominant_Town", new_field_alias="Dominant Town")

print("Dominant town attribution complete.")

# Dominant town field QA

town_fields = [field.name for field in arcpy.ListFields(subbasin_polygons)]

print("Subbasin fields containing town/name:")

for field in town_fields:

    if "town" in field.lower() or "name" in field.lower():
        print(field)

# Dominant town value QA

missing_town_count = 0

with arcpy.da.SearchCursor(subbasin_polygons, ["GRIDCODE", "Dominant_Town"]) as cursor:
    for gridcode, dominant_town in cursor:
        if dominant_town in [None, ""]:
            missing_town_count += 1
            print(f"Missing dominant town for subbasin: {gridcode}")

print("Dominant town QA:")
print(f"Missing dominant towns : {missing_town_count}")
print(f"Town QA                : {'PASS' if missing_town_count == 0 else 'REVIEW'}")

# Define Notebook 1 Major Outputs

notebook_1_major_outputs = {
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

print("Notebook 2 required inputs defined.")

# Validate Notebook 1 Major Outputs

missing_handoff_outputs = []

print("Notebook 1 to Notebook 2 handoff QA:")
for name, path in notebook_1_major_outputs.items():
    exists = arcpy.Exists(path)
    print(f"{name:<26}: {'OK' if exists else 'MISSING'}")

    if not exists:
        missing_handoff_outputs.append(name)

if missing_handoff_outputs:
    raise FileNotFoundError(f"Notebook 1 handoff failed. Missing outputs needed by Notebook 2: {missing_handoff_outputs}")

print("")
print("Notebook 1 handoff QA: PASS")

# Print final Notebook 1 handoff summary

print("Notebook 1 complete.")
print("Ready for Notebook 2: SWAT Spatial Inputs.")
print("")
print("Notebook 2 can now use:")
print(f"- Study area          : {study_area}")
print(f"- DEM                 : {dem_hydro}")
print(f"- Flow direction      : {flow_dir}")
print(f"- Flow accumulation   : {flow_acc}")
print(f"- Stream links        : {stream_links}")
print(f"- Stream network      : {stream_network}")
print(f"- Subbasin raster     : {subbasin_raster}")
print(f"- Subbasin polygons   : {subbasin_polygons}")
