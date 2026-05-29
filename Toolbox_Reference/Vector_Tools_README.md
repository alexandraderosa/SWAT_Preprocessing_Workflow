# Vector Tools

Custom ArcPy Python toolbox used for vector preprocessing, spatial attribution, zonal analysis support, and watershed interpretation workflows.

## Toolbox Alias

vector_tools

## Included Tools

### Zonal Statistics Join Metric

Runs Zonal Statistics as Table, calculates a selected raster statistic, and joins the resulting metric back to the zone features.

### Clip Project Dataset

Clips a vector dataset to a study area, stores the clipped intermediate in a temporary workspace, projects the final dataset, and optionally repairs geometry.

### Dominant Overlap Attribution

Intersects base polygons with overlay polygons, calculates overlap area, identifies the dominant overlay feature for each base feature, and writes the dominant attribute back to the base features.

### Culvert Drainage Area From Pour Point

Snaps a culvert pour point to the highest nearby flow accumulation cell and delineates the contributing drainage area.

### Dominant Class Summary

Identifies the dominant class within each zone from a long-format summary table and produces watershed interpretation outputs.