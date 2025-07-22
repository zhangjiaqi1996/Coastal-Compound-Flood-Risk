import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import os
from shapely.geometry import Polygon
import rasterio
from rasterstats import zonal_stats

###---------------------------------------------生成矢量网格--------------------------------------------------
# 设置经度和纬度的范围
lon_min, lon_max = -180, 180
lat_min, lat_max = -90, 90

# 网格的宽度和高度（0.1度对应大约11.1公里）
grid_width = 0.1  # 经度方向
grid_height = 0.1  # 纬度方向

# 创建经度和纬度的网格
lons = np.arange(lon_min, lon_max, grid_width)
lats = np.arange(lat_min, lat_max, grid_height)

# 创建网格多边形
polygons = []
for lon in lons:
    for lat in lats:
        # 创建每个网格单元（四个角）
        polygon = Polygon([(lon, lat), 
                           (lon + grid_width, lat), 
                           (lon + grid_width, lat + grid_height), 
                           (lon, lat + grid_height)])
        polygons.append(polygon)

# 将网格多边形转换为 GeoDataFrame
gdf = gpd.GeoDataFrame(geometry=polygons)

#设置网格的坐标系
gdf = gdf.set_crs('EPSG:4326') 

# 查看矢量的投影
print(gdf.crs)

###---------------------------------------------计算tiff--------------------------------------------------
# 使用 rasterio 打开 TIFF 文件

raster_file = '../flooding/coastal flooding/CFrp1000.tif'


with rasterio.open(raster_file) as src:
        print('columns,rows:', src.width, src.height)
        print(src.crs)
        print(src.transform)
        print('band number:', src.count) #波段数
        print('index of band:', src.indexes) #波段索引
        # Read the raster data and extract NoData value
        band1 = src.read(1)
        # Replace the NoData values (-9999.0) with NaN
        band1 = np.where(band1 == -9999.0, np.nan, band1)
        band1 = np.where(band1 == 0, np.nan, band1)
        # 更新元数据
        metadata = src.meta.copy()
        metadata.update(nodata=-9999.0)

# 写入新文件
with rasterio.open(raster_file, 'w', **metadata) as dst:
    dst.write(band1, 1)  # 将数据写入第一波段

    # Check the NoData value
    nodata_value = src.nodata 
    print(nodata_value)

nan_count = np.sum(np.isnan(band1))
valid_count = np.sum(~np.isnan(band1))

print(f"Number of NaN values: {nan_count}")
print(f"Number of valid data points: {valid_count}")

# Check the range of the data
# Using np.nanmin(band1) not np.min(band1), because the former one will correctly calculate min value while ignoring NaN.

min_value = np.nanmin(band1)
max_value = np.nanmax(band1)

print(f"Minimum value in band1: {min_value}")
print(f"Maximum value in band1: {max_value}")

###---------------------------------------------分区统计tif的均值和计数--------------------------------------------------

# 计算每个矢量网格的洪水平均深度和洪水面积比例
stats = zonal_stats(gdf, raster_file, stats=['mean','count'], geojson_out=True)

#geojson_out=True：设置为 True，表示输出结果将以 GeoJSON 格式返回。这使得结果可以直接与 GeoDataFrame 结合使用。
#nodata=0：指定 0 为 nodata 值。这意味着在计算 mean 和 count 时，值为 0 的栅格单元将被视为缺失数据，不参与计算。

# 将结果转换为 GeoDataFrame
flood_stats = gpd.GeoDataFrame.from_features(stats)

# 重命名 mean 列为 CF
flood_stats.rename(columns={'mean': 'D_CFrp1000'}, inplace=True)
flood_stats.rename(columns={'count': 'C_CFrp1000'}, inplace=True)

# 打印清除前的行数
print(f"Number of rows before dropping NaNs: {flood_stats.shape[0]}")

# 清除包含 NaN 的行
flood_stats_clean = flood_stats.dropna(subset=['D_CFrp1000'])

# 打印清除后的行数
print(f"Number of rows after dropping NaNs: {flood_stats_clean.shape[0]}")

# 打印前5行
print(flood_stats_clean.head())

flood_stats_clean = flood_stats_clean.set_crs('EPSG:4326') 

###---------------------------------------------计算大网格的面积--------------------------------------------------

# 复制原始的 GeoDataFrame，确保不修改原始数据
flood_stats_copy = flood_stats_clean.copy()

# 临时转换 CRS 为 EPSG:3035 进行面积计算
flood_stats_copy_3035 = flood_stats_copy.to_crs("EPSG:3035")

# 计算每个矢量网格的面积，单位是平方米
flood_stats_copy_3035["area_m2"] = flood_stats_copy_3035.geometry.area

# 如果需要，转换为平方千米
flood_stats_copy_3035["area_km2"] = flood_stats_copy_3035["area_m2"] / 1e6

# 将面积信息赋回原始的 flood_stats_clean，不修改 CRS
flood_stats_clean["area_m2"] = flood_stats_copy_3035["area_m2"]
flood_stats_clean["area_km2"] = flood_stats_copy_3035["area_km2"]


# 导出为 GeoDataFrame（如果已经是 GeoDataFrame 类型，则无需再转换）
flood_stats_clean.to_file('1.data/coastalnet_0.1degree/coastalnet_0.1degree.shp', driver='ESRI Shapefile')

