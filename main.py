import json
import ntpath
import re

import rasterio
from osgeo import gdal
from geo.Geoserver import Geoserver


def sanitize_name(name):
    return re.sub(r'\W+', '_', name)


def load_data_netcdf(input_file, variable_name, output_file, workspace, default_style, additional_styles=[]):
    dataset = gdal.Open(f"NETCDF:{input_file}:{variable_name}")
    gdal.Translate(output_file, dataset)
    load_data_tif(output_file, workspace, default_style, additional_styles)


def load_data_tif(tif_file, workspace, default_style, additional_styles=[]):
    with open('data.json') as f:
        data = json.load(f)
    # Paths and variables
    geoserver_url = data["geoserver_url"]
    username = data["geoserver_publisher"]
    password = data["geoserver_pass"]
    workspace = workspace
    store_name = sanitize_name(ntpath.basename(tif_file))
    layer_name = sanitize_name(ntpath.basename(tif_file))

    # Initialize the GeoServer connection
    try:
        geo = Geoserver(geoserver_url, username=username, password=password)
    except Exception as e:
        print(f"Failed to connect to GeoServer: {e}")
        return
    # Ensure the workspace exists
    workspaces = geo.get_workspaces().get('workspaces', {}).get('workspace', [])
    if workspace not in [ws['name'] for ws in workspaces]:
        geo.create_workspace(workspace, geoserver_url)
    # Publish the GeoTIFF to GeoServer
    geo.create_coveragestore(path=tif_file, workspace=workspace, layer_name=layer_name)
    # Set the default style to 'crop_extent'
    geo.publish_style(layer_name, style_name=default_style, workspace=workspace)
    # Add 'crop_extent_compare' as an additional style
    for style in additional_styles:
        geo.publish_style(layer_name, style_name=style, workspace=workspace)
    # Enable WMS service (ensure the layer is published)
    layers = geo.get_layers().get('layers', {}).get('layer', [])
    if layer_name not in [l['name'] for l in layers]:
        geo.publish_layer(workspace, store_name, layer_name, default_style)
    print(
        f"GeoTIFF published successfully to GeoServer.")


if __name__ == "__main__":
    tif_file_location = ""
    load_data_netcdf("/mnt/rdst/crops/bhutan/crop_extent/crop-extent.20020101T000000Z.bhutan.30m.yearly.nc4", "crop_extent", "crop-extent.20020101T000000Z.bhutan.30m.yearly.tif", "crops", "crop_extent", ["crop_extent_compare"])
    load_data_tif("/mnt/rdst/crops/bhutan/crop_extent/Bhutan_croplandextent_2002_ps_20Apr24.tif", "crops", "crop_extent", ["crop_extent_compare"])
