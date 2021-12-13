import pandas as pd
import geopandas as gpd
import plotly.express as px
import ipywidgets as widgets
from IPython.display import display
import os
import folium
from folium import plugins

data_folder = os.path.abspath('../Data')

# load in data
gdf = gpd.read_file(os.path.join(data_folder, 'nola_crime_calls.geojson'))
cameras = gpd.read_file(os.path.join(data_folder, 'nola_cameras.geojson'))
pop_geo = gpd.read_file(os.path.join(data_folder, 'pop_geo.geojson'))

# convert to datetime type
gdf['TimeCreate'] = pd.to_datetime(gdf.TimeCreate)
gdf = gdf.sort_values(by='TimeCreate', ignore_index=True)

output = widgets.Output()
grouped_output = widgets.Output()
ts_plot_output = widgets.Output()
maps_output = widgets.Output()


def sorted_selections(array):
    return ['All'] + sorted(array.unique().tolist())


# maps selector
maps_selection = widgets.Dropdown(options=['Default', 'Choropleth'])

# census-tract filter
tract_filter = widgets.SelectMultiple(options=sorted_selections(pop_geo.tract))

# call-type filter
call_filter = widgets.SelectMultiple(options=sorted_selections(gdf.TypeText))

# time range filter
dates = pd.date_range(start='2014-01-01', end='2020-12-09', freq='D')
options = [(date.strftime('%Y/%m/%d'), date) for date in dates]
index = (0, len(options) - 1)

time_filter = widgets.SelectionRangeSlider(
    options=options,
    index=index,
    orientation='horizontal',
    layout={'width': '300px'}
)

# time-series groupby selection
time_grouping = widgets.Dropdown(options=['Date', 'Month', 'Year'])

ALL = ('All',)


# filtering function
def filtering(tracts, call_types, date_range, grouping, map_type):
    output.clear_output()
    grouped_output.clear_output()
    ts_plot_output.clear_output()
    maps_output.clear_output()

    if (tracts == ALL) and (call_types == ALL) and (date_range == (dates[0], dates[-1])):
        filtered_df = gdf
    elif (tracts == ALL) and (call_types == ALL):
        filtered_df = gdf[gdf.TimeCreate.between(date_range[0], date_range[1])]
    elif (tracts == ALL) and (date_range == (dates[0], dates[-1])):
        filtered_df = gdf[gdf.TypeText.isin(call_types)]
    elif (call_types == ALL) and (date_range == (dates[0], dates[-1])):
        filtered_df = gdf[gdf.census_tract.isin(tracts)]
    elif date_range == (dates[0], dates[-1]):
        filtered_df = gdf[gdf.census_tract.isin(tracts) & gdf.TypeText.isin(call_types)]
    elif tracts == ALL:
        filtered_df = gdf[gdf.TimeCreate.between(date_range[0], date_range[1]) & gdf.TypeText.isin(call_types)]
    elif call_types == ALL:
        filtered_df = gdf[gdf.TimeCreate.between(date_range[0], date_range[1]) & gdf.census_tract.isin(tracts)]
    else:
        filtered_df = gdf[gdf.TimeCreate.between(date_range[0], date_range[1]) & gdf.TypeText.isin(
            call_types) & gdf.census_tract.isin(tracts)]

    with output:
        display(filtered_df)

    if grouping == 'Date':
        group_df = filtered_df.groupby(filtered_df.TimeCreate.dt.date)[['NOPD_Item']] \
            .count().reset_index().rename(columns={'NOPD_Item': 'Call count', 'TimeCreate': 'Date'})
    elif grouping == 'Month':
        group_df = filtered_df.groupby([filtered_df.TimeCreate.dt.year, filtered_df.TimeCreate.dt.month])[
            ['NOPD_Item']].count().reset_index(level=1) \
            .rename(columns={'TimeCreate': 'Month', 'NOPD_Item': 'Call count'}).reset_index().rename(
            columns={'TimeCreate': 'Year'})
    else:
        group_df = filtered_df.groupby(filtered_df.TimeCreate.dt.year)[['NOPD_Item']] \
            .count().reset_index().rename(columns={'NOPD_Item': 'Call count', 'TimeCreate': 'Year'})

    with grouped_output:
        display(group_df)

    with ts_plot_output:
        if grouping == 'Month':
            fig = px.line(group_df, x=group_df.Year.astype(str) + '-' + group_df.Month.astype(str),
                          y=group_df.columns[2],
                          title='{} Calls'.format(', '.join(call_types)), labels=dict(x='Date'))
            fig.show()
        else:
            fig = px.line(group_df, x=group_df.columns[0], y=group_df.columns[1],
                          title='{} Calls'.format(', '.join(call_types)))
            fig.show()
            # add in fix for month grouping, see example above
    with maps_output:
        nola_map = folium.Map([29.9499, -90.0701],
                              zoom_start=11,
                              tiles='cartodbpositron')
        folium.GeoJson(cameras,
                       marker=folium.Circle(fill=True, color='red'),
                       name='cameras').add_to(nola_map)
        folium.GeoJson(pop_geo,
                       style_function=lambda x: {'color': 'black', 'weight': 1.0, 'fillOpacity': 0},
                       tooltip=folium.GeoJsonTooltip(['tract']),
                       name='Tracts').add_to(nola_map)
        if map_type == 'Default':
            calls_cluster = plugins.MarkerCluster(name='Calls').add_to(nola_map)
            folium.GeoJson(filtered_df.drop('TimeCreate', axis=1),
                           marker=folium.CircleMarker(radius=3),
                           name='calls').add_to(calls_cluster)
            folium.LayerControl(collapsed=False).add_to(nola_map)
            display(nola_map)

        else:
            choro_df = filtered_df.groupby(filtered_df.census_tract)['NOPD_Item'].count()\
                .reset_index()
            choro_df = pop_geo[['tract', 'geometry']].merge(choro_df, left_on='tract', right_on='census_tract')
            folium.Choropleth(
                geo_data=choro_df,
                data=choro_df,
                columns=['tract', "NOPD_Item"],
                key_on="feature.properties.tract",
                fill_color='YlGnBu',
                fill_opacity=.7,
                line_opacity=0,
                legend_name="Num. of Calls",
                smooth_factor=1,
                Highlight=True,
                line_color="#0000",
                name="Choropleth",
                show=False,
                overlay=True,
                nan_fill_color="White"
            ).add_to(nola_map)
            folium.LayerControl(collapsed=False).add_to(nola_map)
            display(nola_map)


# event handlers
def tract_filter_event(change):
    filtering(change.new, call_filter.value, time_filter.value, time_grouping.value, maps_selection.value)


def call_filter_event(change):
    filtering(tract_filter.value, change.new, time_filter.value, time_grouping.value, maps_selection.value)


def time_filter_event(change):
    filtering(tract_filter.value, call_filter.value, change.new, time_grouping.value, maps_selection.value)


def time_grouping_event(change):
    filtering(tract_filter.value, call_filter.value, time_filter.value, change.new, maps_selection.value)


def maps_selection_event(change):
    filtering(tract_filter.value, call_filter.value, time_filter.value, time_grouping.value, change.new)


# bind handlers
tract_filter.observe(tract_filter_event, names='value')
call_filter.observe(call_filter_event, names='value')
time_filter.observe(time_filter_event, names='value')
time_grouping.observe(time_grouping_event, names='value')
maps_selection.observe(maps_selection_event, names='value')

top = widgets.HBox([widgets.Label('$Census \space tract \colon$'), tract_filter,
                    widgets.Label('$Call \space type \colon$'), call_filter],
                   layout=widgets.Layout(align_items='stretch', justify_content='space-between'))
middle = widgets.HBox([widgets.Label('$Time\space period \colon$'), time_filter,
                       widgets.Label('$Time \space group \colon$'), time_grouping],
                      layout=widgets.Layout(margin='20px 0 0 0', justify_content='space-between'))
bottom = widgets.HBox([widgets.Label('$Compare \space by \colon$'), widgets.Dropdown(
    options=['None', 'Census tract', 'Call type']), widgets.Label(''), widgets.Dropdown()],
                      layout=widgets.Layout(margin='20px 0 0 0', justify_content='space-between'))
maps = widgets.HBox([widgets.Label('$Map \space Display \colon$'), maps_selection],
                    layout=widgets.Layout(margin='20px 0 0 0', justify_content='space-around'))

# if adding compare by, use bottom in VBox list
input_filters = widgets.VBox([top, middle, maps], layout=widgets.Layout(margin='0 0 50px 0'))

tab = widgets.Tab([output, grouped_output, ts_plot_output, maps_output])
tab.set_title(0, 'Stacked Data')
tab.set_title(1, 'Aggregated Data')
tab.set_title(2, 'Plot')
tab.set_title(3, 'Map')

dashboard = widgets.VBox([input_filters, tab])
# display(dashboard)
