import re
import usaddress
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path


def convert_price(price):

    """
    Converts string price into integers.
    Example: C$2,200/mo -> 2200
    """

    return int(''.join(re.findall('[0-9]+', price)))


def convert_address(address):
    address_number, street_name, place_name = 'no_data', 'no_data', 'no_data'
    try:
        conv_address = usaddress.tag(address[:address.rfind(',')])
        address_number = conv_address[0].get('AddressNumber') if conv_address[0].get(
            'AddressNumber') else address_number
        street_name = conv_address[0].get('StreetName') if conv_address[0].get('StreetName') else street_name
        place_name = conv_address[0].get('PlaceName') if conv_address[0].get('PlaceName') else place_name
    except:
        pass

    return '&'.join([address_number, street_name, place_name])


if __name__ == '__main__':
    current_path = Path.cwd().joinpath('analyzing')
    dataframe = pd.read_excel(Path.cwd().joinpath('scraping', 'data.xlsx'))
    dataframe = dataframe.drop(columns=['Unnamed: 0'])

    # Converting price column into integer values
    dataframe['Price'] = dataframe['Price'].apply(convert_price)

    # Adding new columns by converting address into new format
    dataframe['TempAddress'] = dataframe['Address'].apply(convert_address)
    dataframe[['AddressNumber', 'Street', 'City']] = dataframe['TempAddress'].str.split('&', expand=True)
    del dataframe['TempAddress']
    column_names = dataframe.columns.to_list()
    for idx in range(-3, 0):
        column_names.insert(8+idx, column_names.pop(idx))
    dataframe = dataframe.reindex(columns=column_names)
    sns.set_theme(style="whitegrid")

    # Plot prices range
    plt.figure()
    ranges = [0, 2000, 4000, 6000, 8000, 10000]
    prices_range = sns.barplot(x="Price", y="Count",
                               data=pd.DataFrame(
                                   dataframe.groupby(pd.cut(dataframe.Price, ranges)).count()['Price']
                               ).rename(columns={"Price": "Count"}).reset_index(), palette="Blues_d")
    prices_range.get_figure().savefig(current_path.joinpath('prices_range.png'))

    # Plot heatmap
    plt.figure()
    corr = dataframe.corr()
    heatmap = sns.heatmap(corr, xticklabels=corr.columns, yticklabels=corr.columns, annot=True)
    heatmap.get_figure().savefig(current_path.joinpath('heatmap.png'))

    # Plot mean prices
    plt.figure()
    fig, axs = plt.subplots(ncols=2, figsize=(14, 5))
    sns.barplot(x="Bedrooms", y="Price", data=dataframe.groupby('Bedrooms').mean().reset_index(),
                palette="Blues_d", ax=axs[0])
    sns.barplot(x="Bathrooms", y="Price", data=dataframe.groupby('Bathrooms').mean().reset_index(),
                palette="Blues_d", ax=axs[1])
    fig.savefig(current_path.joinpath('prices_mean.png'))

    # Plot number of available offers with certain amount of bedrooms and bathrooms
    plt.figure()
    fig, axs = plt.subplots(ncols=2, figsize=(14, 5))
    sns.barplot(x="Bedrooms", y="Count",
                data=dataframe['Bedrooms'].value_counts().reset_index().rename(
                    columns={"index": "Bedrooms", "Bedrooms": "Count"}
                ), palette="Blues_d", ax=axs[0])
    sns.barplot(x="Bathrooms", y="Count",
                data=dataframe['Bathrooms'].value_counts().reset_index().rename(
                    columns={"index": "Bathrooms", "Bathrooms": "Count"}
                ), palette="Blues_d", ax=axs[1])
    fig.savefig(current_path.joinpath('offers_count.png'))

    # Plot scatter plot with coordinates of offerings
    plt.figure()
    sns.set_style("ticks")
    plt.figure(figsize=(18, 14))
    sns.kdeplot(x='Longitude', y='Latitude', data=dataframe, cmap='Blues', shade=True, thresh=0.05, alpha=0.6)
    scatter = sns.scatterplot(x="Longitude", y="Latitude",  data=dataframe[dataframe['Price'] < 10000],
                              palette="inferno", hue='Price', size='Price')
    scatter.get_figure().savefig(current_path.joinpath('xy_scatter.png'))
