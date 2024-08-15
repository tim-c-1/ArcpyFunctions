#exporttoDB

$dupPkgPath = "[insert path for text file checker]"

function Get-Files {
    #Prep raw files for database entry by taking target files, filetype, and datatype (SB/SSS/etc) and writing file info to csv.
    param (
        $FilePath,
        $FileExtension,
        $DataType
    )
    $filter = '*'+$FileExtension
    #get file names, write to csv. pull csv into write-database function
    Get-ChildItem -Path $FilePath -Filter $filter | Select-Object -Property @{Name = 'Filename'; expression = {$_.BaseName}},@{Name = 'Datatype'; expression = {$Datatype}},@{Name = 'file_type'; expression = {$_.Extension}},@{Name = 'File_pathway';expression = {$_.FullName}} | Export-Csv $dupPkgPath'filetest.csv'
}

function Write-FilesDB {
    # writes processed file info to database from prepped rawfile csv export
    param (
        $SurveyID,
        $Date,
        $initials,
        $tbltype,
        $wgsLon,
        $wgsLat,
        $area
    )
    if (!$Date -or !$SurveyID) {
        Write-Host "Fill out the parameters."
    }else{
        $adOpenStatic = 3
        $adLockOptimistic = 3
        $table = if($tbltype -eq "RawFiles"){"RawFiles"}else {
            "Processed_Files"
        }
        $importCSV = Import-Csv $dupPkgPath'filetest.csv'

        $objConnection = New-Object -com "ADODB.Connection"
        $objRecordSet = New-Object -com "ADODB.Recordset"
        $fileName = $importCSV."filename"
        $dataType = $importCSV."datatype"
        $fileType = $importCSV."file_type"
        $filePathway = $importCSV."File_pathway"
            
        $objConnection.Open("Provider = Microsoft.ACE.OLEDB.12.0; Data Source = [insert backend access database path]")

        $objRecordset.Open("Select * From $($table)", $objConnection,$adOpenStatic,$adLockOptimistic)

        $importLength = $importCSV | Measure-Object
        if($importLength."count" -eq 1){
            $objRecordSet.AddNew()
            $objRecordSet.Fields.Item("Survey_ID") = $SurveyID
            $objRecordSet.Fields.Item("Date") = $Date
            $objRecordSet.Fields.Item("File_name") = $fileName
            $objRecordSet.Fields.Item("Datatype") = $dataType
            $objRecordSet.Fields.Item("File_type") = $fileType
            $objRecordSet.Fields.Item("File_pathway") = $filePathway
            $objRecordSet.Fields.Item("Entered_By") = $initials
            if($table -eq "Processed_Files"){
            $objRecordSet.Fields.Item("CoordinateLon_WGS84") = $wgsLon
            $objRecordSet.Fields.Item("CoordinateLat_WGS84") = $wgsLat
            $objRecordSet.Fields.Item("Coordinate_Source") = "ArcPy centroid calculation"
                if($dataType -eq "SSS"){$objRecordSet.fields.Item("Area_Size") = $area}
            }
            # Write-Host $importCSV
            $objRecordSet.Update()
        }else{
            for ($i = 0; $i -lt $importLength."Count"; $i++) {
                $objRecordSet.AddNew()
                $objRecordSet.Fields.Item("Survey_ID") = $SurveyID
                $objRecordSet.Fields.Item("Date") = $Date
                $objRecordSet.Fields.Item("File_name") = $fileName[$i]
                $objRecordSet.Fields.Item("Datatype") = $dataType[$i]
                $objRecordSet.Fields.Item("File_type") = $fileType[$i]
                $objRecordSet.Fields.Item("File_pathway") = $filePathway[$i]
                $objRecordSet.Fields.Item("Entered_By") = $initials
                # Write-Host $importCSV[$i]
                $objRecordSet.Update()
            }
        }
        $objRecordSet.Close()
        
        if($table -eq "Processed_Files"){
            $query = "Select count(*) from ProjectCoordinates where Survey_ID = '$SurveyID'"
            $command = New-Object System.Data.OleDB.OleDbCommand
            $connection = New-Object System.Data.OleDB.OleDbConnection
            $connection.ConnectionString = "Provider = Microsoft.ACE.OLEDB.12.0; Data Source = [insert backend Access database path]"
            $command.Connection = $connection
            $command.commandtext = $query
            $connection.Open()
            $result = $command.ExecuteScalar()
            $connection.Close()
            
            if($result -eq 0) {       
                $objRecordSet.Open("Select * from ProjectCoordinates", $objConnection, $adOpenStatic,$adLockOptimistic)   
                $objRecordSet.AddNew()
                $objRecordSet.fields.Item("Survey_ID") = $SurveyID
                $objRecordSet.fields.Item("WGS84Lat") = $wgsLat
                $objRecordSet.fields.Item("WGS84Lon") = $wgsLon
                $objRecordSet.Fields.Item("Coordinate_Source") = "ArcPy centroid calculation"
                $objRecordSet.Update()
                $objRecordSet.Close()
            }
            
        }
        
        $objConnection.Close()
    }
}
function exporttoDB {
    param (
        $tblType,
        $initials,
        $wgsLon,
        $wgsLat,
        $filepath,
        $fileextension,
        $Survey_ID,
        $Date,
        $Datatype
    )
    Get-Files -FilePath $filepath -FileExtension $fileextension -DataType $Datatype
    Write-FilesDB -SurveyID  $Survey_ID -Date $Date -initials $initials -tbltype $tblType -wgsLon $wgsLon -wgsLat $wgsLat
}

if($args[1] -eq "RawFiles"){
    Write-Host "RawFiles"
    exporttoDB -initials $args[0] -tblType $args[1] -filepath $args[2] -fileextension $args[3] -Survey_ID $args[4] -Date $args[5] -Datatype $args[6]
}elseif($args[6] -eq "SSS"){
    Write-Host "SSS Processed"
    exporttoDB  -initials $args[0] -tblType $args[1] -filepath $args[2] -fileextension $args[3] -Survey_ID $args[4] -Date $args[5] -DataType $args[6] -wgsLat $args[7] -wgsLon $args[8] -area $args [9]
}elseif($args[6] -eq "SB"){
    Write-Host "SB Processed"
    exporttoDB -initials $args[0] -tblType $args[1] -filepath $args[2] -fileextension $args[3] -Survey_ID $args[4] -Date $args[5] -DataType $args[6] -wgsLat $args[7] -wgsLon $args[8] 
}
# Write-Host "Initials: " $args[0]
# Write-Host "tbltype: " $args[1]
# Write-Host "filepath: " $args[2]
# Write-Host "fileextension: "$args[3]
# Write-Host "surveyid: "$args[4]
# Write-Host "date: " $args[5]
# Write-Host "datatype: " $args[6]
# Write-Host "wgsLat: " $args[7]
# Write-Host "wgsLon: " $args[8]
