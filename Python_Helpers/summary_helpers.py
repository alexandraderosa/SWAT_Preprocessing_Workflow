# ============================================================
# summary_helpers.py
# Shared reusable helper functions for GIS/Pandas workflows
# ============================================================

# Included helper functions:
#
# 1. dataframe_to_gdb_table()
#    Export Pandas DataFrame to geodatabase table
#
# 2. create_horizontal_bar_chart()
#    Create and export horizontal summary charts
#
# Future helpers:
# - create_dominant_summary()
# - prepare_join_table()
# - apply_field_aliases()
# - delete_existing_fields()


# ============================================================
# Dependencies
# ============================================================

import os
import arcpy
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


# ============================================================
# Helper Function 1
# Export Pandas DataFrame to Geodatabase Table
# ============================================================

def dataframe_to_gdb_table(df, output_table):

    # Delete existing table if it already exists
    if arcpy.Exists(output_table):

        arcpy.management.Delete(output_table)

    # Create temporary CSV path inside project Outputs/Tables folder
    temp_csv = os.path.join(
        os.path.dirname(arcpy.env.workspace),
        "Outputs",
        "Tables",
        "_temp_dataframe_export.csv"
    )

    # Delete temporary CSV if it already exists
    if os.path.exists(temp_csv):

        os.remove(temp_csv)

    # Export dataframe to temporary CSV
    df.to_csv(
        temp_csv,
        index=False
    )

    # Convert temporary CSV to geodatabase table
    arcpy.conversion.TableToTable(
        in_rows=temp_csv,
        out_path=os.path.dirname(output_table),
        out_name=os.path.basename(output_table)
    )

    # Delete temporary CSV after conversion
    if os.path.exists(temp_csv):

        os.remove(temp_csv)

    # Return final table path
    return output_table


# ============================================================
# Helper Function 2
# Create Horizontal Bar Chart from Summary Table
# ============================================================

def create_horizontal_bar_chart(
    df,
    category_field,
    value_field,
    output_png,
    title,
    xlabel,
    ylabel,
    top_n=None,
    show_figure=True,
    add_value_labels=False,
    use_thousands_separator=True):

    # Create copy of dataframe for plotting
    plot_df = df.copy()

    # Convert plotting field to numeric
    plot_df[value_field] = pd.to_numeric(
        plot_df[value_field],
        errors="coerce"
    )

    # Remove rows with missing values
    plot_df = plot_df.dropna(
        subset=[category_field, value_field]
    )

    # Keep only top N rows if requested
    if top_n is not None:

        plot_df = plot_df.nlargest(
            int(top_n),
            value_field
        )

    # Sort values for plotting
    plot_df = plot_df.sort_values(
        by=value_field,
        ascending=False
    )

    # Create figure
    plt.figure(figsize=(10, 6))

    # Create horizontal bar chart
    bars = plt.barh(
        plot_df[category_field].astype(str),
        plot_df[value_field]
    )

    # Set chart title and axis labels
    plt.title(
        title,
        fontweight="bold"
    )

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # Format axis with thousands separator if requested
    if use_thousands_separator:

        plt.gca().xaxis.set_major_formatter(
            ticker.StrMethodFormatter("{x:,.0f}")
        )

    # Add value labels to bars if requested
    if add_value_labels:

        max_value = plot_df[value_field].max()

        offset = (
            max_value * 0.01
            if max_value
            else 0.1
        )

        for bar in bars:

            width = bar.get_width()

            label = (
                f"{width:,.2f}"
                if abs(width - round(width)) > 0.001
                else f"{width:,.0f}"
            )

            plt.text(
                width + offset,
                bar.get_y() + bar.get_height() / 2,
                label,
                va="center"
            )

    # Adjust layout
    plt.tight_layout()

    # Export figure to PNG
    plt.savefig(
        output_png,
        dpi=300,
        bbox_inches="tight"
    )

    # Show figure in notebook if requested
    if show_figure:

        plt.show()

    # Close figure after export
    plt.close()

    # Return output figure path
    return output_png