# Easy and (somewhat) fast Lidar Point Cloud Imporer for Blender 5.0

This blender extension  aims to provide a one-click solution for importing .las and .laz to blender. 

This addon is heavily inspired by the work of @nittanygeek and his [Lidar-Importer](https://github.com/nittanygeek/LiDAR-Importer). However, I've rewritten everything from scratch to make sure it fits the new extension architecture and it will be easier to maintain. 

In its current state, the extension supports :
- Import as native point cloud object
- Import as mesh object
- Early version of supporting Las Attributes as Point Attributes in Blender
- Automatic positionning at scene's center.
- Massive performance improvments over legacy addon. 

## Installation

Download the zip file from the release panel and drag and drop it anywhere in the Blender interface. 

## Usage:

File > Import > LiDAR Format (.las) > Select your LAS file and click "Import LiDAR File"

## License:

This code is available under the GNU Public Licence
