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

# 读取另一个shp文件（如国家边界）
gridnet = gpd.read_file("1.data/coastalnet_0.1degree/merged_flood_results.shp")#---------------------------modify here
# gridnet = gpd.read_file("data-doctor3/2.reanalysis/1.data/coastalnet_0.1degree/ceshi/merged_flood_results.shp")

# Print all column names
print(gridnet.columns.tolist())

# 打印前5行数据查看
print(gridnet.head())

# 查看矢量的投影
print(gridnet.crs)

#------------------------------------------  data cleaning ------------------------------------------ 
# Count values greater than a threshold
threshold_value = 144

count_above_threshold = (gridnet['C_CFrp1000'] > threshold_value).sum()

print(f"Number of values greater than {threshold_value} in C_CFrp1000: {count_above_threshold}")

# Count rows where CFC equals 0
zero_count = (gridnet['C_CFrp1000'] == 0).sum()
print(f"Number of rows where C_CFrp1000 equals 0:", zero_count)

# Filter rows with CFC less than or equal to the threshold
gridnet_clean = gridnet[gridnet['C_CFrp1000'] <= threshold_value]

#------------------------------------------  calculating flooding area ------------------------------------------ 
total_grids=144

# Define the list of return periods you want to calculate for
return_periods = ['CFrp0005', 'CFrp0010', 'CFrp0025', 'CFrp0050', 'CFrp0100', 'CFrp0250', 'CFrp0500', 'CFrp1000',
                  'RFrp0005', 'RFrp0010', 'RFrp0025', 'RFrp0050', 'RFrp0100', 'RFrp0250', 'RFrp0500', 'RFrp1000']

# Iterate over each return period and calculate the corresponding 'CFA' columns
for rp in return_periods:
    
    # Construct the column names dynamically
    d_column = f'D_{rp}'  # e.g., 'D_CFrp0010'
    c_column = f'C_{rp}'  # e.g., 'C_CFrp0010'
    a_column = f'A_{rp}'  # e.g., 'A_CFrp0010'
    v_column = f'V_{rp}'  # e.g., 'V_CFrp0010'

    # 将 'a_column' 列中的 0 值替换为 NaN
    gridnet_clean[c_column] = gridnet_clean[c_column].replace(0, np.nan)

    # Perform the calculation for each return period
    gridnet_clean[a_column] = (gridnet_clean[c_column] / total_grids) * gridnet_clean['area_km2']
    gridnet_clean[v_column] = gridnet_clean[a_column] * gridnet_clean[d_column]

#------------------------------------------ 计算 FH_rp1000 - FH_rp0005------------------------------------------ 
# 定义重现期列表
rp_list = ['1000', '0500', '0250', '0100', '0050', '0025', '0010', '0005']

# 遍历每个重现期，计算对应的 FH_rp
for rp in rp_list:
    # 使用fillna(0)来替换空缺值为0，确保计算的正确而不改变原始数据
    gridnet_clean[f'FH_rp{rp}'] = gridnet_clean[f'V_RFrp{rp}'].fillna(0) + gridnet_clean[f'V_CFrp{rp}'].fillna(0)


# Display the first few rows of the updated DataFrame
print(gridnet_clean[[f'A_{rp}' for rp in return_periods]].head())
print(gridnet_clean[[f'V_{rp}' for rp in return_periods]].head())

# 打印前5行数据查看
print(gridnet_clean.head())
# Print all column names
print(gridnet_clean.columns.tolist())



# Export the gridnet_clean DataFrame to an Excel file
output_file = '1.data/coastalnet_0.1degree/merged_flood_results_area+volume+hazard.xlsx'  # Define the output file name
gridnet_clean.to_excel(output_file, index=False)

# Save the final merged results as a new shapefile
gridnet_clean.to_file("1.data/coastalnet_0.1degree/merged_flood_results_area+volume+hazard.shp")
