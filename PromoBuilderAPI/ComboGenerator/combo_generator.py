import pandas as pd
import pickle

df_dict = {}
dev_set_names = []

def get_dev_set_names():
    return dev_set_names

def get_list_by_volume(products_df):
    df_by_volume = products_df.groupby(products_df.columns[0]).agg({products_df.columns[1]: 'first', products_df.columns[2]: 'first', products_df.columns[3]: 'sum'})
    df_by_volume = df_by_volume[df_by_volume['Volume'] > 0]
    total_volume = df_by_volume['Volume'].sum()
    df_by_volume['SOM'] = (df_by_volume['Volume'] / total_volume) * 100
    df_by_volume = df_by_volume.sort_values(by=df_by_volume.columns[3], ascending=False)
    return df_by_volume

def split_by_dev_set(df_by_volume, dev_set_mappings, dev_set_size = 5):
    dev_set_size = 5
    for segment, products in dev_set_mappings.items():
        #dev_set_names.append(segment)
        df_segment = df_by_volume[df_by_volume['Product'].isin(products)]
        df_segment = df_segment.sort_values(by='Volume', ascending=False)
        df_segment = df_segment.head(dev_set_size)
        total_m = df_segment['SOM'].sum()
        df_segment['RSOM'] = df_segment['SOM'] / total_m * 100
        df_dict[segment] = df_segment

def generate_bundles_type1(dev_set_name, net_discount):
    SKUs = df_dict[dev_set_name].index.tolist()
    combo_list = [[comb] for comb in SKUs]
    all_combos = pd.DataFrame(combo_list, columns=["Product"])
    promoed_products = df_dict[dev_set_name].loc[all_combos['Product']]
    total_volume = promoed_products['Volume'].sum()
    discount_by_volume_function = promoed_products['Volume'] ** 0.85
    promoed_products['discount'] = (total_volume / discount_by_volume_function) * net_discount
    promoed_products['discount'] = promoed_products['discount'] / (promoed_products['discount'] * promoed_products['Volume']).sum() * total_volume * net_discount
    return promoed_products.to_json()


