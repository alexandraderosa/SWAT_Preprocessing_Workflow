# Transparent SWAT Watershed Delineation and HRU Development Framework

This repository contains a modular ArcGIS Pro and ArcPy workflow for watershed delineation, terrain analysis, SWAT input preparation, watershed characterization, and hydrologic response unit (HRU) development.

Unlike traditional ArcSWAT preprocessing workflows, this project explicitly exposes and documents the intermediate GIS operations that are often treated as a "black box." Each processing step is implemented in reproducible Python notebooks with automated quality assurance (QA) checks, allowing users to inspect, validate, troubleshoot, and modify every stage of watershed preparation.

The workflow was developed using ArcGIS Pro, ArcPy, and custom Python tools to create transparent, reproducible, and auditable SWAT preprocessing workflows.

---

## Why This Workflow Exists

Many hydrologic modeling workflows rely on software tools that automate watershed delineation, subbasin generation, land cover processing, soils processing, and HRU development.

While these tools are extremely useful, they often obscure the underlying hydrologic and GIS operations being performed.

This project was developed to deconstruct those processes into transparent, reproducible components that can be independently inspected, validated, modified, and extended.

Rather than treating watershed preprocessing as a black box, the workflow reconstructs the major steps typically performed within ArcSWAT using ArcGIS Pro, ArcPy, custom Python tools, and automated QA procedures.

The result is a workflow that not only generates SWAT-ready inputs, but also documents how those inputs were created and validates the assumptions made at each stage of processing.

---

## Project Purpose

The primary goals of this project were to:

- modernize a legacy ArcMap SWAT preprocessing workflow
- expose intermediate GIS processing steps typically hidden within ArcSWAT
- transition manual GIS operations into reproducible Python notebooks
- automate repetitive hydrologic preprocessing tasks
- improve workflow transparency through automated QA and validation
- generate SWAT-ready watershed inputs
- document preprocessing logic in a reproducible and modular format
- provide a framework for troubleshooting and auditing watershed preparation workflows

---

## Workflow Philosophy

Traditional SWAT preprocessing often functions as a black box:

DEM → ArcSWAT → HRUs

This workflow instead treats each processing stage as a transparent and independently verifiable GIS operation.

Key principles include:

- reproducible notebook-based workflows
- modular GIS processing steps
- automated quality assurance and validation
- explicit intermediate outputs
- traceable watershed delineation logic
- reproducible HRU generation procedures

Every notebook concludes with QA dashboards that summarize workflow outputs, validation metrics, and readiness for the next processing stage.

---

## Workflow Diagram

![SWAT Workflow Diagram](Charts/SWAT_Workflow_Diagram.png)

---

## Workflow Overview

The workflow is organized into four sequential notebooks.

### Notebook 1 – Watershed Delineation and Terrain Processing

This notebook establishes the hydrologic framework of the watershed.

**Major workflow components:**

- study area extraction
- DEM preparation and conditioning
- sink identification and preservation
- flow direction generation
- flow accumulation generation
- stream network extraction
- stream link generation
- watershed delineation
- subbasin generation
- watershed QA and validation

**Outputs:**

- flow direction raster
- flow accumulation raster
- stream network
- stream links
- subbasin raster
- subbasin polygons

### Notebook 2 – SWAT Spatial Input Preparation

This notebook prepares and standardizes SWAT spatial inputs while validating raster coverage and consistency.

**Major workflow components:**

- SWAT land cover reclassification
- soils and hydrologic soil group processing
- slope raster generation
- slope classification
- raster alignment and standardization
- zonal statistics by subbasin
- spatial QA and coverage validation

**Outputs:**

- SWAT land cover raster
- soils raster
- slope class raster
- land cover summaries by subbasin
- soils summaries by subbasin
- slope summaries by subbasin

### Notebook 3 – Watershed Composition and Dominant Attribute Analysis

This notebook summarizes watershed composition and assigns dominant watershed characteristics to each subbasin.

**Major workflow components:**

- watershed composition analysis
- dominant land cover assignment
- dominant hydrologic soil group assignment
- dominant slope assignment
- chart generation
- export table creation
- GIS layer enrichment

**Outputs:**

- watershed composition tables
- dominant land cover summaries
- dominant hydrologic soil group summaries
- dominant slope summaries
- watershed characterization figures
- GIS-ready subbasin interpretation layers

### Notebook 4 – Hydrologic Response Unit (HRU) Development

This notebook generates SWAT-style hydrologic response units and evaluates the impacts of HRU filtering thresholds.

**Major workflow components:**

- HRU raster development
- HRU definition generation
- HRU area calculations
- HRU threshold filtering
- HRU reduction analysis
- watershed composition summaries
- final SWAT-ready HRU exports

**Outputs:**

- HRU definition tables
- filtered HRU tables
- subbasin HRU summaries
- watershed HRU summaries
- SWAT-ready HRU characterization outputs

---

## Quality Assurance Framework

Automated quality assurance checks are integrated throughout the workflow.

Validation components include:

- watershed area preservation checks
- raster-to-polygon consistency checks
- sink and pond validation
- raster coverage validation
- raster alignment validation
- subbasin summary completeness checks
- dominant attribute assignment checks
- HRU filtering impact assessment

Each notebook concludes with a handoff QA dashboard summarizing workflow outputs, validation metrics, and readiness for the next processing stage.

---

## Project Outputs

This workflow produces SWAT-ready watershed inputs and watershed characterization products suitable for hydrologic modeling, watershed assessment, and spatial analysis.

### Watershed Composition

![Watershed Land Cover Composition](Charts/Watershed_LandCover_Composition.png)

![Hydrologic Soil Group Distribution](Charts/Hydrologic_Soil_Group_Distribution.png)

### Watershed Characterization

![Total HRUs by Subbasin](Charts/Total_HRUs_By_Subbasin.png)

Additional charts, tables, maps, and GIS-ready datasets are available throughout the repository.

---

## Repository Structure

```text
SWAT_Preprocessing_Workflow/
├── Charts/
├── Maps/
├── Notebooks/
├── Python_Helpers/
├── Tables/
└── Toolbox_Reference/
```

---

## Tools and Libraries

### GIS Software

- ArcGIS Pro
- ArcPy
- Spatial Analyst

### Python Libraries

- Python
- Pandas
- Matplotlib

### Custom Workflow Components

- reusable Python helper functions
- custom ArcPy toolboxes
- modular notebook workflow architecture
- automated QA dashboards
- reproducible watershed preprocessing tools

---

## Data Requirements

Large GIS datasets and proprietary source data are not included in this repository.

Users must provide their own:

- DEM datasets
- land cover datasets
- soils datasets
- watershed boundary datasets
- LiDAR-derived terrain products

Notebook paths have been generalized for public release.

---

## Relationship to Companion Repository

This repository focuses on GIS preprocessing and watershed characterization for SWAT modeling.

The workflow produces transparent, reproducible, and QA-validated watershed inputs that can be used in ArcSWAT and related hydrologic modeling frameworks.

A companion repository documents the subsequent modeling phase, including:

- ArcSWAT model development
- streamflow calibration
- model validation
- sensitivity analysis
- SUFI-2 uncertainty analysis
- watershed interpretation
- scenario analysis

Together, the two repositories document the complete watershed modeling workflow from raw spatial data through calibrated hydrologic simulation.

---

## Author

Alexandra DeRosa

Master of Environmental Science and Management  
University of Rhode Island

Graduate Certificate in Hydrology  
Graduate Certificate in Geographic Information Systems and Remote Sensing