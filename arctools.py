from pyproj import Transformer
import numpy as np
import arcpy

def readTIF(file_path):
    #lazy load arcpy
    import arcpy
    # Load the raster dataset
    desc = arcpy.Describe(file_path)
    white_threshold = 255
    # Create a boolean mask for white values
    white_mask = raster_data < white_threshold

    if desc.bandCount > 1:
        raster = arcpy.Raster(file_path).getRasterBands(1)
        if len(arcpy.RasterToNumPyArray(raster)[white_mask]) == 0:
            raster = arcpy.Raster(file_path).getRasterBands(2)
            if len(arcpy.RasterToNumPyArray(raster)[white_mask]) == 0:
                raster = arcpy.Raster(file_path).getRasterBands(3)
    else:
        raster = arcpy.Raster(file_path)
        
    transformer = Transformer.from_crs("EPSG:32618", "EPSG:4326")

    # Get raster properties
    width = raster.width
    height = raster.height
    cell_size = raster.meanCellWidth  # Assuming square cells

    # Read raster data as numpy array
    raster_data = arcpy.RasterToNumPyArray(raster)

    # Use the mask to filter out white values
    non_white_pixels = raster_data[white_mask]
    
    if len(non_white_pixels) > 0:
        # Get the coordinates of non-white pixels
        non_white_pixel_coords = np.argwhere(white_mask)
        # Calculate average x and y coordinates
        avg_x = np.mean([raster.extent.XMin + (coord[1] + 0.5) * cell_size for coord in non_white_pixel_coords])
        avg_y = np.mean([raster.extent.YMin + (coord[0] + 0.5) * cell_size for coord in non_white_pixel_coords])
    else:
        # If no valid pixels were found, return None
        print("no valid pixels")
        return None, None
        
    point_wgs = transformer.transform(avg_x, avg_y)
    
    wgsLat = point_wgs[0]
    wgsLon = point_wgs[1]

    print(wgsLat, wgsLon)

def transformDD(x,y):
    transformer = Transformer.from_crs("EPSG:32618", "EPSG:4326")
    
    # x = 72646.4
    # y = 567014.3
    DDcords = transformer.transform(x,y)
    print(DDcords)

    wgsCoord = str(DDcords).split(" ")
    wgsLat = DDcords[0]
    wgsLon = DDcords[1]

    # print(wgsLat)
    # print(wgsLon)
    return wgsLat, wgsLon

def navRead(file):
    arr = np.loadtxt(file) #use numpy to load .nav as array
    #find first row
    starting_lat = arr[0,1]
    starting_lon = arr[0,2]
    #find last row
    end_lat = arr[-1,1]
    end_lon = arr[-1,2]
    print(starting_lat,starting_lon)
    #calc midpoint between start and end lat/lon
    mid_lat = str((end_lat-((end_lat - starting_lat)/2))/60) #convert minutes to degrees
    mid_lon = str((end_lon-((end_lon-starting_lon)/2))/60) #convert minutes to degrees
    
    return mid_lon, mid_lat

def rasterArea(raster_file):

    desc = arcpy.Describe(raster_file)

    if desc.bandCount > 1:
        raster = arcpy.Raster(raster_file).getRasterBands(1)
    else:
        raster = arcpy.Raster(raster_file)

   # Define the value to ignore (255/255/255 in this case)
    ignore_value = 255

    # Define the UTM zone
    utm_zone = "18N"

    # Get the spatial reference of the raster
    desc = arcpy.Describe(raster)
    spatial_ref = desc.spatialReference
    linear_unit = spatial_ref.linearUnitName

    # Convert raster to NumPy array
    raster_array = arcpy.RasterToNumPyArray(raster)

    # Mask the array to ignore specified values
    masked_array = np.ma.masked_equal(raster_array, ignore_value)

    # Calculate total area
    cell_size = desc.meanCellHeight * desc.meanCellWidth
    non_masked_count = np.count_nonzero(~masked_array.mask)  # Count non-masked pixels
    total_area = non_masked_count * cell_size  # Multiply by cell size to get area in square meters

    # Print the total area
    print("acres: ", round(total_area/4047,0))
    return round(total_area/4047,0)

#use this block for reading nav files
# file_path = input("file: ")

# coords = navRead(file_path.replace(".jpg",".nav"))
# wgsLat = coords[0]
# wgsLon = coords[1]

# print(wgsLat, wgsLon)

#use this block for transforming coords from wgs 84 utm zone 18n to wgs 84 DD
# transformDD(380309.9288,4338328.892)


#use this block for reading rasters
# readTIF(input("raster filepath: "))

def loopnread(file):
    list = open(file, "r")
    for i in list:
        print(i)
        readTIF(i)
    list.close()

# loopnread(input("file: "))

def testnumpyarr(file):
    rast = arcpy.RasterToNumPyArray(file)
    print(rast)

rasterArea(input("file: "))
# testnumpyarr(input("file: "))