# New-Orleans-Crime-Calls
A quick jupyter notebook visualization with `plotly` and `folium` of crime calls in New Orleans.

## Environment
This notebook uses an environment with geolocation tools such as `geopandas`, please set up a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file)
with `geo_env.yml`.

## Set up
After creating the `geo_env`:
1. extract `Data.zip` for the following directory structure: 
```
./Data
    nola_cameras.geojson
    nola_crime_calls.geojson
    pop_geo.geojson

./Code
    minidash.py
    nola_911_explorer.ipynb
```
2. run jupyter notebook and load `nola_911_explorer.ipynb`.
3. execute the cells
4. use the dashboard (note: large data selections may not display properly for the default map.)
