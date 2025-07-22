import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import os
from shapely.geometry import Polygon
import rasterio
from rasterstats import zonal_stats

#检查当前工作目录
print(os.getcwd())

gdf = gpd.read_file("/public/home/jiaqizhang/JiaqiZhang/data-doctor3/2.reanalysis/1.data/10.tidalflat/gridnet_tidalflats_pop.shp",engine="pyogrio")##################################modify here

#设置网格的坐标系

# 查看矢量的投影
print(gdf.crs)

# 替换为栅格数据的EPSG代码
# gdf = gdf.set_crs('EPSG:4326')  # 替换为栅格数据的EPSG代码

# 使用 rasterio 打开 TIFF 文件
tiff_file = '/public/home/jiaqizhang/JiaqiZhang/data-doctor3/GDP/2010/2010GDP_4326.tif'##################################modify here
with rasterio.open(tiff_file) as src:
    
    # 读取第一个波段数据
    band1 = src.read(1)
    
    # 获取 CRS 信息
    crs = src.crs  # 返回 CRS 对象
    # 输出 CRS 信息
    print(f'TIFF 文件的坐标参考系统: {crs}')
    
    # Check the NoData value
    nodata_value = src.nodata  
    print(f"NoData value: {nodata_value}")

    # Replace the NoData values (-9999.0) with NaN
    # band1 = np.where(band1 == nodata_value, np.nan, band1) #NaN data mean it will be ignored when calculating
    # Replace the Data values (0) with NaN,maybe it is not correct to replace 0 with NaN,0 means no flooding depth.
    # band1 = np.where(band1 == 0, np.nan, band1)
    
    # 获取图像的地理坐标范围
    bounds = src.bounds  # 获取边界 (min_x, min_y, max_x, max_y)
    
    # 获取图像的分辨率
    pixel_width = src.res[0]  # x方向的分辨率
    pixel_height = src.res[1]  # y方向的分辨率
    
    print(f"分辨率 (像素大小): {pixel_width} m (宽) x {pixel_height} m (高)")

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

# 计算每个矢量网格的洪水平均深度和洪水面积比例
stats = zonal_stats(gdf, tiff_file, stats=['sum','count'], geojson_out=True, nodata=nodata_value)


#geojson_out=True：设置为 True，表示输出结果将以 GeoJSON 格式返回。这使得结果可以直接与 GeoDataFrame 结合使用。
#nodata=0：指定 0 为 nodata 值。这意味着在计算 mean 和 count 时，值为 0 的栅格单元将被视为缺失数据，不参与计算。

# 将结果转换为 GeoDataFrame
flood_stats = gpd.GeoDataFrame.from_features(stats)

flood_stats = flood_stats.set_crs('EPSG:4326')  # set the coordinate system for the Geodataframe.

# 重命名 mean 列为 CFD_rp1000, count 列为 CFAc_rp1000
flood_stats.rename(columns={'sum': 'GDP'}, inplace=True)##################################modify here

# 打印清除前的行数
print(f"Number of rows: {flood_stats.shape[0]}")

# 打印前5行
print(flood_stats.head())

# 导出为 GeoDataFrame（如果已经是 GeoDataFrame 类型，则无需再转换）
flood_stats.to_file('/public/home/jiaqizhang/JiaqiZhang/data-doctor3/2.reanalysis/1.data/11.GDP/gridnet_GDP.shp', driver='ESRI Shapefile')##################################modify here
flood_stats.to_excel('/public/home/jiaqizhang/JiaqiZhang/data-doctor3/2.reanalysis/1.data/11.GDP/gridnet_GDP.xlsx', index=False)
