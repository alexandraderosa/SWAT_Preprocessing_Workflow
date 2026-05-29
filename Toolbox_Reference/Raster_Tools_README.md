# Raster Tools

Custom ArcPy Python toolbox used for raster preprocessing, terrain analysis, hydrologic conditioning, and watershed modeling support workflows.

## Toolbox Alias

raster_tools

## Included Tools

### Extract Project Raster Dataset

Extracts a raster to a study area, projects it to a target coordinate system, optionally applies an output cell size, and performs raster quality assurance checks.

### Tabulate Area Summary Table

Runs Tabulate Area for a categorical raster by zone features and produces summary tables suitable for watershed characterization and SWAT preprocessing.

### Raster Alignment QA

Compares raster coordinate systems, cell sizes, and alignment against a reference raster to ensure compatibility across modeling inputs.

### Stream Network From Flow Accumulation

Generates a binary stream raster, stream link raster, and vector stream network from a flow accumulation surface.

### Real Sink Summary

Identifies sink regions, groups connected sink cells, and preserves larger sink features as potential natural depressions for hydrologic analysis.