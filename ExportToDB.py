#Add survey information to database.
import subprocess
# import arcpy
import os
# import arcpy.management
import numpy as np
from pyproj import Transformer

def call_powershell_script(initials, tbltype, file_path, file_extension, survey_id, survey_date, datatype, wgsLat=None, wgsLon=None, area=None):
    script_path = "C:/Users/tcooney/Documents/scripts/#exportToDB.ps1"
    # script_path = "M:\MGS\Coastal\Tim\DuplicateCheckingPackage\DatabaseScripts\#exporttoDB.ps1"
    args = ['powershell.exe', '-File', script_path, initials, tbltype, file_path, file_extension, survey_id, survey_date, datatype]

    if wgsLat is not None:
        # add Lat arg
        args.extend([str(wgsLat)])
    if wgsLon is not None:
        # add Lon arg
        args.extend([str(wgsLon)])
    if area is not None:
        #add area arg
        args.extend([str(area)])

    subprocess.call(args)
    # subprocess.call(['powershell.exe', '-File', script_path, initials, tbltype, wgsLat, wgsLon, file_path, file_extension, survey_id, date, datatype])

def readGeoJPG(file):
   
    desc = arcpy.Describe(file)
    # utm_zone = desc.spatialreference.PCSName

    transformer = Transformer.from_crs("EPSG:32618", "EPSG:4326")

    extent = desc.extent
    xmin = extent.XMin
    xmax = extent.XMax
    ymin = extent.YMin
    ymax = extent.YMax

    centerX = (xmax + xmin) / 2
    centerY = (ymax + ymin) / 2

    print(centerX, centerY)
    
    point_wgs = transformer.transform(centerX, centerY)
    wgsCoord = str(point_wgs).split(" ")
    wgsLat = wgsCoord[0]
    wgsLon = wgsCoord[1]

    return wgsLat, wgsLon

def navRead(file):

    arr = np.loadtxt(file) #use numpy to load .nav as array
    #find first row
    starting_lat = arr[0,1]
    starting_lon = arr[0,2]
    #find last row
    end_lat = arr[-1,1]
    end_lon = arr[-1,2]
    #calc midpoint between start and end lat/lon
    mid_lat = str((end_lat-((end_lat - starting_lat)/2))/60) #convert minutes to degrees
    mid_lon = str((end_lon-((end_lon-starting_lon)/2))/60) #convert minutes to degrees
    
    return mid_lon, mid_lat

def readTIF(file_path):
    # Load the raster dataset
    # raster = arcpy.Raster(file_path).getRasterBands(1)
    desc = arcpy.Describe(file_path)

    if desc.bandCount > 1:
        raster = arcpy.Raster(file_path).getRasterBands(1)
    else:
        raster = arcpy.Raster(file_path)
        
    transformer = Transformer.from_crs("EPSG:32618", "EPSG:4326")

    # Get raster properties
    width = raster.width
    height = raster.height
    cell_size = raster.meanCellWidth  # Assuming square cells

    # Define threshold for white background
    # This threshold could be adjusted based on your specific data
    white_threshold = 255

    # Read raster data as numpy array
    raster_data = arcpy.RasterToNumPyArray(raster)

    # Create a boolean mask for white values
    white_mask = raster_data < white_threshold

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
        return None, None
        
    point_wgs = transformer.transform(avg_x, avg_y)
    
    wgsLat = point_wgs[0]
    wgsLon = point_wgs[1]

    return wgsLat, wgsLon

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

    # Check if the linear units are in meters
    # if linear_unit == "Meter":
    #     # Linear units are already in meters, no need to project
    #     raster_proj = raster
    # else:
    #     # Project the raster to a suitable coordinate system with linear units in meters
    #     # Define the path for the projected raster
    #     # projected_raster = "path/to/your/projected_raster.tif"
    #     projected_raster = arcpy.ProjectRaster_management(raster, None, arcpy.SpatialReference(utm_zone), "BILINEAR")

    #     # Use the projected raster for calculations
    #     raster_proj = projected_raster

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

initials = input("initials: ")
if input("Raw or Processed? (R/P): ") == "R":
    tbltype = "RawFiles"
else:
    tbltype = "Processed_Files"

path = input("Path: ")
survey_id = input("Survey_ID: ")
survey_date = input("Survey date: ")
datatype = input("Datatype (SSS/SB/Bathy/etc.): ")

if tbltype == "Processed_Files":
    if datatype == "SSS" or datatype == "SB" or datatype == "Bathy":
        print("Reading files...")
        if datatype == "SSS" or datatype == "Bathy":
            import arcpy #lazy load only if datatype will need arcpy tools for coord calculations.
        for root, dirs, files in os.walk(path):
            for file in files:
                #   print(file)
                if file.lower().endswith((".tif",".jpg",".shp")):
                    file_path = os.path.join(root, file)
                    print(file_path)
                    if datatype == "SSS" or datatype == "Bathy":
                        if file.lower().endswith(".tif"):
                            coords = readTIF(file_path)
                            area = rasterArea(file_path)
                            print("made it to tif coords")
                        elif file.endswith((".jpg",".shp")):
                            coords = readGeoJPG(file_path)
                            area = None
                        wgsLat = coords[0]
                        wgsLon = coords[1]
                        print("coords = ", coords)
                        print("area = ", area)
                        # print(coords[0],coords[1],file_path,os.path.splitext(file_path[1]))
                        call_powershell_script(initials, tbltype, file_path, os.path.splitext(file_path)[1], survey_id, survey_date, datatype, wgsLat, wgsLon, area)
                    elif datatype == "SB":
                        try:
                            coords = navRead(file_path.replace(".jpg",".nav"))      
                            wgsLat = coords[0]
                            wgsLon = coords[1]
                            call_powershell_script(initials, tbltype, file_path, os.path.splitext(file_path)[1], survey_id, survey_date, datatype, wgsLat, wgsLon)
                        except: print("couldn't find nav of ",file_path)
                    else:
                        print("Datatype did not match SSS or SB")
else:
    ftypes = input("filetype to read (.jsf/etc.): ")
    print("Reading raw files...")
    call_powershell_script(initials, tbltype, path, ftypes, survey_id, survey_date, datatype, None, None)