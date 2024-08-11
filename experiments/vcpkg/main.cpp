#include <ostream>
#include <iostream>

#include <pdal/PointView.hpp>
#include <pdal/PointTable.hpp>
#include <pdal/Dimension.hpp>
#include <pdal/Options.hpp>
#include <pdal/StageFactory.hpp>
#include <spdlog/spdlog.h>
#include "fmt/format.h"
#include <ogrsf_frmts.h>
#include <ogr_core.h>
#include <ogr_spatialref.h>

int main(int argc, char* argv[]) {
    auto path_gdal = argv[1];
    // auto path_pdal = argv[2];

    GDALAllRegister();
    GDALDataset       *poDS;

    poDS = (GDALDataset*) GDALOpenEx( path_gdal, GDAL_OF_VECTOR, NULL, NULL, NULL );
    if( poDS == NULL )
    {
        printf( "Open failed.\n" );
        exit( 1 );
    }
    OGRLayer  *poLayer;
    poLayer = poDS->GetLayer(0);
    OGREnvelope *poEnvelope;
    poLayer->GetExtent(poEnvelope);
    spdlog::info("OGR bbox: {} {} {} {}", poEnvelope->MinX, poEnvelope->MinY, poEnvelope->MaxX, poEnvelope->MaxY);
    char *pszSRS_WKT = NULL;
    poLayer->GetSpatialRef()->exportToWkt(&pszSRS_WKT);
    spdlog::info("OGR spatial reference: {}", pszSRS_WKT);
    CPLFree( pszSRS_WKT );
    GDALClose( poDS );

    return 0;
}

