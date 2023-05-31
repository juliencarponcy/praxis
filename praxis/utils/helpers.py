import requests

from scipy.interpolate import griddata
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS

def get_all_soilgrid_for_points(points: gpd.GeoSeries):
    """
    Retrieve soilgrid data for multiple points using the ISQAPER API.

    Parameters:
        points (gpd.GeoSeries): GeoSeries with Shapely Point objects representing the grid points.

    Returns:
        list: List of API responses containing soilgrid data for each point.

    Assumes that each value in the GeoSeries is a Shapely Point.

    The function queries the ISRIC API and retrieves soilgrid data for each point. It returns a list
    containing the API responses for each point.
    """
    # URL and endpoint for the API
    url = 'https://isqaper.isric.org/isqaper-rest/api/1.0/query'

    # Create an empty list to store the API responses
    api_responses = []

    # Iterate over each grid point and query the API
    for point in points.geometry:
        lon, lat = point.x, point.y  # Extract the longitude and latitude from the grid point
        params = {'lon': lon, 'lat': lat}  # API parameters for the coordinates

        # Send GET request to the API
        response = requests.get(url, params=params)

        if response.status_code == 200:
            # Successful response
            data = response.json()
            api_responses.append(data)
        else:
            # Handle error response
            print(f"Error: {response.status_code}")

    return api_responses

def format_soilgrid_response(api_responses):
    """
    Format soilgrid API responses.

    Parameters:
        api_responses (list): List of API responses containing soilgrid data.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame with formatted soilgrid data.

    The function formats the soilgrid API responses by extracting relevant data and structuring it into
    a GeoDataFrame. The nested structure of the responses is browsed to extract short descriptions and
    values. If a metadata field is found, the values are stored in a column named after the short description.
    Otherwise, the function traverses the nested structure and extracts the short descriptions and values.

    Note: Some fields, such as Depth to Bedrock and Phosphorus using the Olsen method, are categorical
    and may require additional processing to be usable.

    The function returns a GeoDataFrame with the formatted soilgrid data.
    """
    coordinates = [[feat['geometry']['coordinates'] for feat in api_response['features']] for api_response in api_responses]
    # Create a list of Shapely Point geometries from the coordinates
    geometries = [Point(coord) for coord in coordinates]
    # Create the GeoDataFrame with points coordinates only
    gdf = gpd.GeoDataFrame(geometry=geometries, crs= CRS.from_epsg(4326))

    # browse the nested structure of api response dictionary and retrieve short description and values
    # and then fill the geodataframe column by column for all responses
    for feat_key , feat_value in api_responses[0]['features'][0]['properties']['properties'].items():
        if 'metadata' in feat_value.keys():
            gdf[feat_value['metadata']['short_description']] = [api_response['features'][0]['properties']['properties'][feat_key]['value'] for api_response in api_responses]

        else:
            for nested_key , nested_value in feat_value.items():
                gdf[nested_value['metadata']['short_description']] = [api_response['features'][0]['properties']['properties'][feat_key][nested_key]['value'] for api_response in api_responses]

    return gdf

def polygon_binning_to_points(gdf: gpd.GeoDataFrame, resolution_m: int) -> gpd.GeoDataFrame:
    '''
    Convert a GeoDataFrame with a target polygon into a GeoDataFrame of grid points within the polygon.

    Parameters:
        gdf (gpd.GeoDataFrame): GeoDataFrame with the target polygon.
        resolution_m (int): Desired resolution in meters for the grid points.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing the grid points within the polygon.

    NB: Assumes that the target polygon is using WGS 84 (EPSG:4326) and that the GeoDataFrame contains only one polygon.
    '''
    target_polygon = gdf.geometry[0]  # Assuming there's only one polygon in the file

    # Create a GeoDataFrame with the target polygon
    gdf_target = gpd.GeoDataFrame(geometry=[target_polygon], crs=gdf.crs)

    # Reproject the GeoDataFrame to the desired CRS (Web Mercator)
    # We need coordinates in meters to increment the binning by the desired resolution (in the test 250m)
    gdf_target_3857 = gdf_target.to_crs(CRS.from_epsg(3857))

    # Determine the bounding box of the projected polygon
    minx, miny, maxx, maxy = gdf_target_3857.geometry.bounds.values[0]

    # Generate grid points within the bounding box
    grid_points = []
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            point = Point(x, y)
            if gdf_target_3857.geometry[0].contains(point):
                grid_points.append(point)
            y += resolution_m
        x += resolution_m

    grid_geopd = gpd.GeoDataFrame(geometry=grid_points, crs= CRS.from_epsg(3857))
    # Retransform coordinates as latitude and longitude
    grid_geopd = grid_geopd.to_crs(crs = CRS.from_epsg(4326))

    return grid_geopd

def interpolate_point_measures(gdf: gpd.GeoDataFrame, selected_measures: list) -> gpd.GeoDataFrame:
    """
    Interpolate point measures to a regular grid.

    Parameters:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing the point measures.
        selected_measures (list): List of selected measures to interpolate.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame with interpolated measures on a regular grid.

    The function takes a GeoDataFrame containing point measures and interpolates the selected measures
    to a regular grid using the scipy.interpolate.griddata function. The grid is defined by the bounding
    box of the input data, and the step size can be adjusted as per the needs. The interpolation method
    used is linear.

    The function returns a GeoDataFrame with the interpolated measures on a regular grid.
    """
    xmin, ymin, xmax, ymax = gdf.total_bounds  # Get the bounding box of the data
    grid_x, grid_y = np.mgrid[xmin:xmax:500j, ymin:ymax:500j]  # Adjust the step size as per your needs

    interpolated_data = {}
    points = np.vstack([gdf.geometry.x.values, gdf.geometry.y.values]).T
    for measure in selected_measures:
        values = gdf[measure].values
        interpolated_values = griddata(points, values, (grid_x, grid_y), method='linear')
        interpolated_data[measure] = interpolated_values

    interp_gpd = gpd.GeoDataFrame()
    for col_name, values in interpolated_data.items():
        interp_gpd[col_name] = values.flatten()

    interp_gpd = interp_gpd.set_geometry(gpd.GeoSeries(map(Point, zip(grid_x.flatten(), grid_y.flatten()))))
    interp_gpd.crs = gdf.crs

    return interp_gpd
