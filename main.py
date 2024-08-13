from geo.Geoserver import Geoserver
import json
import ntpath

from osgeo import gdal
from utils import *


def sanitize_name(name):
    """
    Sanitize a string to create a valid name for GeoServer layers and stores.

    Parameters:
    name (str): The string to sanitize.

    Returns:
    str: The sanitized string, with non-alphanumeric characters replaced by underscores.
    """
    return re.sub(r'\W+', '_', name)


def load_data_netcdf(input_file, variable_name, output_file, workspace, default_style, additional_styles=[]):
    """
    Convert a NetCDF variable to a GeoTIFF file and publish it to GeoServer.

    Parameters:
    input_file (str): Path to the NetCDF file.
    variable_name (str): The variable name within the NetCDF file to convert.
    output_file (str): Path to save the output GeoTIFF file.
    workspace (str): The GeoServer workspace where the layer will be published.
    default_style (str): The default style to apply to the layer in GeoServer.
    additional_styles (list): A list of additional styles to add to the layer in GeoServer.
    """
    dataset = gdal.Open(f"NETCDF:{input_file}:{variable_name}")
    gdal.Translate(output_file, dataset)
    load_data_tif(output_file, workspace, default_style, additional_styles)


def load_data_tif(tif_file, workspace, default_style, additional_styles=[]):
    """
    Publish a GeoTIFF file to GeoServer and apply the specified styles.

    Parameters:
    tif_file (str): Path to the GeoTIFF file.
    workspace (str): The GeoServer workspace where the layer will be published.
    default_style (str): The default style to apply to the layer in GeoServer.
    additional_styles (list): A list of additional styles to add to the layer in GeoServer.
    """
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

    # Add 'crop_extent_compare' as an additional style
    for style in additional_styles:
        geo.publish_style(layer_name, style_name=style, workspace=workspace)
    # Set the default style to 'crop_extent'
    geo.publish_style(layer_name, style_name=default_style, workspace=workspace)

    print(
        f"GeoTIFF published successfully to GeoServer.")


def process_directory(directory_path, file_type, variable_name=None, workspace="crops", default_style="crop_extent",
                      additional_styles=[]):
    """
    Process all GeoTIFF or NetCDF files in a directory and publish them to GeoServer.

    Parameters:
    directory_path (str): The directory containing the files.
    file_type (str): The type of files to process ('tif' or 'netcdf').
    variable_name (str): The variable name within NetCDF files to convert (required for NetCDF files).
    workspace (str): The GeoServer workspace where the layers will be published.
    default_style (str): The default style to apply to the layers in GeoServer.
    additional_styles (list): A list of additional styles to add to the layers in GeoServer.
    """
    if file_type not in ['tif', 'netcdf']:
        print("Invalid file type specified. Please use 'tif' or 'netcdf'.")
        return

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            if file_type == 'tif' and filename.endswith('.tif'):
                print(f"Processing GeoTIFF file: {filename}")
                load_data_tif(file_path, workspace, default_style, additional_styles)
            elif file_type == 'netcdf' and filename.endswith(('.nc', '.nc4')):
                if variable_name is None:
                    print(f"Variable name must be provided for NetCDF files. Skipping {filename}.")
                    continue
                print(f"Processing NetCDF file: {filename}")
                output_file = f"{os.path.splitext(filename)[0]}.tif"
                load_data_netcdf(file_path, variable_name, output_file, workspace, default_style, additional_styles)
            else:
                print(f"Skipping file: {filename}")


if __name__ == "__main__":
    tif_file_location = ""
    # load_data_netcdf("/mnt/rdst/crops/bhutan/crop_extent/crop-extent.20020101T000000Z.bhutan.30m.yearly.nc4", "crop_extent", "crop-extent.20020101T000000Z.bhutan.30m.yearly.tif", "crops", "crop_extent", ["crop_extent_compare"])
    # load_data_tif("/mnt/rdst/crops/bhutan/crop_extent/Bhutan_croplandextent_2002_ps_20Apr24.tif", "crops", "crop_extent", ["crop_extent_compare"])

    # filepath = "D:\\mnt\\cropmonitor\\bhutan\\crop_extent\\Bhutan_croplandextent_2002_ps_20Apr24.tif"
    # input_pattern = r"Bhutan_croplandextent_(?P<year>\d{4})_ps_20Apr24\.tif"
    # output_pattern = "crop-extent.{year}0101T000000Z.bhutan.30m.yearly.tif"
    #
    # rename_file(filepath, input_pattern, output_pattern)

    # Example usage: processing all GeoTIFF files in a directory
    process_directory("/mnt/rdst/crops/bhutan/crop_extent/", file_type='tif', workspace="crops",
                      default_style="crop_extent", additional_styles=["crop_extent_compare"])
