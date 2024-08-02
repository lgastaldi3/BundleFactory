import pandas as pd
import numpy as np

my_df = pd.read_excel("../Data/Reseller_Elite_Reporting_DATA.xlsx")
grouped_df = my_df.groupby(['PRODUCT_DESCRIPTION', 'PACKAGE_GROUP'])['VOLUME_RAW_CASES'].sum().reset_index()

SKUs_by_volume = grouped_df.sort_values(by='VOLUME_RAW_CASES', ascending=False).reset_index(drop=True)


def get_specific_volumes(SKUs):
    queried_df = SKUs_by_volume[SKUs_by_volume['PRODUCT_DESCRIPTION'].isin(SKUs)]
    return queried_df

def generate_discounts(introductory_discount, incremental_discount, anchor_discount):
    SKUs_by_volume['introductory_discount'] = 0
    SKUs_by_volume['incremental_discount'] = 0
    SKUs_by_volume['anchor_discount'] = 0
    
    total_volume = SKUs_by_volume['VOLUME_RAW_CASES'].sum()
    discount_by_volume_function = SKUs_by_volume['VOLUME_RAW_CASES'] ** 0.25
    
    SKUs_by_volume['introductory_discount'] = (total_volume / discount_by_volume_function) * introductory_discount
    SKUs_by_volume['introductory_discount'] = SKUs_by_volume['introductory_discount'] / (SKUs_by_volume['introductory_discount'] * SKUs_by_volume['VOLUME_RAW_CASES']).sum() * total_volume * introductory_discount
    SKUs_by_volume['introductory_discount'] = SKUs_by_volume['introductory_discount'].round(2)

    SKUs_by_volume['incremental_discount'] = (total_volume / discount_by_volume_function) * introductory_discount
    SKUs_by_volume['incremental_discount'] = SKUs_by_volume['incremental_discount'] / (SKUs_by_volume['incremental_discount'] * SKUs_by_volume['VOLUME_RAW_CASES']).sum() * total_volume * incremental_discount
    SKUs_by_volume['incremental_discount'] = SKUs_by_volume['incremental_discount'].round(2)
    
    SKUs_by_volume['anchor_discount'] = (total_volume / discount_by_volume_function) * introductory_discount
    SKUs_by_volume['anchor_discount'] = SKUs_by_volume['anchor_discount'] / (SKUs_by_volume['anchor_discount'] * SKUs_by_volume['VOLUME_RAW_CASES']).sum() * total_volume * anchor_discount
    SKUs_by_volume['anchor_discount'] = SKUs_by_volume['anchor_discount'].round(2)


def generate_quantities():
    SKUs_by_volume['introductory_quantity'] = np.random.randint(1, 4, size=len(SKUs_by_volume))
    SKUs_by_volume['incremental_quantity'] = np.random.randint(1, 4, size=len(SKUs_by_volume))
    SKUs_by_volume['anchor_quantity'] = np.random.randint(1, 4, size=len(SKUs_by_volume))

#generate_discounts(3, 2, 1)

#################### TODO: DEFINE DISCOUNT LOGIC ####################