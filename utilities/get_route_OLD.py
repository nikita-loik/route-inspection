import os
import sys
import json
import pandas as pd
import geopandas as gpd
import numpy as np
import shapely as sh
from shapely.ops import transform
from shapely import wkt
import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import networkx as nx
import copy
import dropbox
import datetime

import string

import pdb

import route.graph_functions as gf
import dynpl.pa_global_parameters as pa_global_parameters

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('dropbox').setLevel(logging.WARNING)

GPX_FRAGMENT_THRESHOLD = 25000
GPX_MINI_FRAGMENT_THRESHOLD = 5000
WEIGHT_THRESHOLD = 10
ROUTE_COVERAGE = 0.99
GRAPH_SIZE_THRESHOLD = 80000


# RECONSTRUCT DRIVING ROUTE ===================================================
def swap_virtual_edge_for_real_path(
        virtual_eulerian_route: list,
        virtual_edges: list,
        super_g: nx.DiGraph()):
    """
    
    """
    real_route = []
    for e in virtual_eulerian_route:
        if e not in virtual_edges:
            real_route.append(e)
        else:
            added_path = gf.get_shortest_path(super_g, e[0], e[1])[1]
            for added_e in added_path:
                real_route.append(added_e)
    return real_route


def make_edge_list(route, g):
    '''
    Create the edgelist without parallel edge for the visualization
    Combine duplicate edges and keep track of their sequence and # of walks
    Parameters:
        euler_route: list[tuple] from create_eulerian_route
    '''
    edges_dict = {}

    for i, e in enumerate(route):
        if e in edges_dict:
            edges_dict[e][2]['sequence'] += ', ' + str(i)
            edges_dict[e][2]['visits'] += 1

        else:
            edges_dict[e] = (e[0], e[1], g.get_edge_data(e[0], e[1]))
            edges_dict[e][2]['sequence'] = str(i)
            edges_dict[e][2]['visits'] = 1

    return list(edges_dict.values())


# GET ROUTE FOR SELECTED POLYGON ==============================================
def get_graph_for_polygon(
        df_geo: gpd.geodataframe.GeoDataFrame,
        polygon: sh.geometry.polygon.Polygon):
    '''
    Creates a graph, which covers the area framed by a polygon
    '''
    # A. select segments within polygon
    df = df_geo[
        df_geo['geometry'].intersection(polygon).length / df_geo['length'] >= 0.5]
    df = df.reset_index(drop=True)

    # B. convert dataframe to graph
    g = gf.df_to_graph(df)

    # C. select only the largest SCC (strongly connected component) of the g
    g = g.subgraph(
        sorted(
            nx.strongly_connected_components(g),
            key=len,
            reverse=True)[0]).copy()
    # D. get graph statistics
    gf.get_graph_statistics(g)
    return g


def prune_graph(
        g: nx.DiGraph()):
    '''
    Creates a graph, which covers the area framed by a polygon
    '''
    # A. remove u/left-turn edges from g
    g = gf.remove_u_turns_and_left_turns(g)

    # B. remove unbalanced edges from g
    g = gf.iteratively_remove_unbalanced_edges(g)
    return g


def get_route_for_polygon(
        g: nx.DiGraph(),
        super_g: nx.DiGraph()):

    virtual_graph_and_edges = gf.balance_nodes(g, super_g)
    virtual_g = virtual_graph_and_edges['virtual_g']
    virtual_edges = virtual_graph_and_edges['virtual_edges']
    virtual_eulerian_route = list(nx.eulerian_circuit(virtual_g))

    route_by_edge = swap_virtual_edge_for_real_path(
        virtual_eulerian_route,
        virtual_edges,
        super_g)
    route_by_node = [edge[0] for edge in route_by_edge]
    gf.get_route_by_node_statistics(
        route_by_edge,
        route_by_node,
        super_g,
        g)

    return {'route_by_edge': route_by_edge,
            'route_by_node': route_by_node,
            }


# GET ROUTE FOR SELECTED SEGMENTS ============================================
def get_weight_threshold(
        super_g: nx.DiGraph(),
        selected_segments: list,
        weight: str = 'combined_weight',
        coverage: float = ROUTE_COVERAGE,
        graph_size_threshold: int = GRAPH_SIZE_THRESHOLD):

    weight_threshold = 1
    virtual_edges = get_virtual_edges(
        super_g,
        selected_segments,
        weight,
        weight_threshold)
    g = get_graph_to_drive(
        virtual_edges)
    while ((len(g.nodes()) / len(selected_segments)) < coverage):
        weight_threshold += 1
        virtual_edges = get_virtual_edges(
            super_g,
            selected_segments,
            weight,
            weight_threshold)
        g = get_graph_to_drive(
            virtual_edges)
        if len(g.edges()) >= graph_size_threshold:
            break
    logger.info(f"\toptimised weight threshold: {weight_threshold}")
    return weight_threshold


def get_one_way_segments(
        df_geo: gpd.geodataframe.GeoDataFrame,
        polygon):

    df_geo = df_geo[
        df_geo['geometry'].intersection(polygon).length / df_geo['length'] >= 0.5]
    one_way_segments = [
        s for s in df_geo['gh_id'].tolist()
        if -s not in df_geo['gh_id'].tolist()]

    logger.info(f"\t{len(one_way_segments)} one way segments")
    return one_way_segments


def get_all_segments_within_polygon(
        df_geo: gpd.geodataframe.GeoDataFrame,
        polygon):

    df_geo = df_geo[
        df_geo['geometry'].intersection(polygon).length / df_geo['length'] >= 0.5]
    segments_within_polygon = df_geo['gh_id'].tolist()

    logger.info(f"\t{len(segments_within_polygon)} segments within polygon")
    return segments_within_polygon


def get_virtual_edges(
        super_g: nx.DiGraph(),
        selected_segments: list,
        weight: str = 'combined_weight',
        weight_threshold: int = WEIGHT_THRESHOLD,
        ) -> dict:

    virtual_edges = {}
    for source in selected_segments:
        targets_dict = nx.multi_source_dijkstra_path_length(
            super_g,
            [source],
            cutoff=weight_threshold,
            weight=weight)
        targets_list = list(targets_dict.keys())
        for target in targets_list:
            if ((target not in selected_segments)
                or (target == source)):
                del targets_dict[target]
        virtual_edges.update({(source, target): targets_dict[target]
                              for target in list(targets_dict.keys())})

    return virtual_edges


def get_graph_to_drive(
        virtual_edges: dict  # {(tail, head): combined_weight}
        ):
    g = nx.DiGraph()
    for e in virtual_edges.items():
        g.add_edge(*(e[0]), weight=e[1])

    sub_g = g.subgraph(sorted(nx.strongly_connected_components(g),
                              key=len,
                              reverse=True)[0]).copy()

    return sub_g


def remove_non_essential_edges(
        g: nx.classes.digraph.DiGraph,
        super_g:  nx.classes.digraph.DiGraph):

    paths_lengths_list = [(e, nx.dijkstra_path_length(
        super_g,
        *e,
        weight='length'))
                          for e in list(g.edges())]
    paths_list_sorted = sorted(paths_lengths_list,
                               key=lambda e: e[1],
                               reverse=True)
    paths_list_sorted = [e[0] for e in paths_list_sorted]

    working_g = g.copy()

    for e in paths_list_sorted:
        test_g = working_g.copy()
        test_g.remove_edge(*e)
        if nx.is_strongly_connected(test_g):
            working_g.remove_edge(*e)

    gf.get_graph_statistics(working_g)
    gf.get_turns_statistics(working_g)
    return working_g


def get_route_for_selected_segments(
        super_g: nx.DiGraph(),
        selected_segments: list,
        weight: str = 'combined_weight',
        ) -> dict:
    # A. check all selected segments are within super_g
    selected_segments = [s for s in selected_segments
        if s in list(super_g.nodes())]
    # B. get weight threshold
    weight_threshold = get_weight_threshold(
        super_g,
        selected_segments,
        weight='combined_weight',
        coverage=ROUTE_COVERAGE,
        graph_size_threshold=GRAPH_SIZE_THRESHOLD)
    # C. get virtual edges
    virtual_edges = get_virtual_edges(
        super_g,
        selected_segments,
        weight,
        weight_threshold)
    # D. get graph to drive
    g = get_graph_to_drive(
        virtual_edges)
    # E. get graph statistics
    gf.get_graph_statistics(g)
    # F. remove non-essential edges from graph
    g = remove_non_essential_edges(g, super_g)
    
    virtual_graph_and_edges = gf.balance_nodes(g, super_g)
    if virtual_graph_and_edges['node_to_remove'] is not None:
        node_to_remove = virtual_graph_and_edges['node_to_remove']
        selected_segments.remove(node_to_remove)
        logger.info(
            f"\tsegment removed from the route: {node_to_remove}\n")
        return get_route_for_selected_segments(
            super_g,
            selected_segments,
            weight,
            )
    virtual_g = virtual_graph_and_edges['virtual_g']
    virtual_edges = virtual_g.edges()
    virtual_eulerian_route = list(nx.eulerian_circuit(virtual_g))
    route_by_edge = swap_virtual_edge_for_real_path(
        virtual_eulerian_route,
        virtual_edges,
        super_g)
    route_by_node = [edge[0] for edge in route_by_edge]
    gf.get_route_by_node_statistics(
        route_by_edge,
        route_by_node,
        super_g,
        g)

    return {'route_by_edge': route_by_edge,
            'route_by_node': route_by_node,
            'g': g}


# EXPORT DRIVING ROUTE ========================================================
def route_to_df(
        route_by_node: list,
        df_geo,
        crs_city,
        crs_init: dict=pa_global_parameters.CRS_INIT):
    route_data = []
    try:
        for i, gh_id in enumerate(route_by_node):
            segment_data = df_geo[df_geo['gh_id'] == gh_id]
            segment = {}
            segment['sequence'] = i
            segment['gh_id'] = gh_id
            segment['geometry'] = segment_data['geometry'].values[0]
            segment['street'] = segment_data['street'].values[0]
            route_data.append(segment)
    except:
        for i, gh_id in enumerate(route_by_node):
            segment_data = df_geo[df_geo['gh_id'] == gh_id]
            segment = {}
            segment['sequence'] = i
            segment['gh_id'] = gh_id
            segment['geometry'] = segment_data['geometry'].values[0]
            route_data.append(segment)

    route_df = pd.DataFrame(route_data)
    route_df_geo = gpd.GeoDataFrame(route_df, crs=crs_city)
    route_df_geo = route_df_geo.to_crs(crs_init)

    return {
        'route_df_geo': route_df_geo,
        'route_data': route_data}


def df_to_geojson(df_geo, crs, output_geojson):
    '''
    Takes GEO dataframe,
    crs in the format {'init': 'epsg:25832'},
    and output_file_name.geojson.
    Outputs a geojson file.
    NB! QGIS doesn't like NaN (np.nan).
    '''
    feature_list = list(df_geo)
    feature_list.remove('geometry')

    geojson = {'type': 'FeatureCollection',
               'crs': {
                   'type': 'name',
                   'properties': {
                       'name': 'urn:ogc:def:crs:EPSG::{}'.format(crs['init'][5:])}},
               'features': []}
    for i, row in df_geo.iterrows():
        feature = {
            'type': 'Feature',
            'properties': {},
            'geometry': {'type': 'LineString',
            'coordinates': []}}
        for f in feature_list:
            feature['properties'][f] = row[f]
            feature['geometry']['coordinates'] = list(row['geometry'].coords)

        geojson['features'].append(feature)
    with open(output_geojson, 'w') as output_file:
        json.dump(geojson, output_file)


def df_to_gpx(df_geo, output_gpx_path):
    with open(output_gpx_path, 'w') as output_gpx:
        output_gpx.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
        )
        output_gpx.write(
            '<gpx version="1.1" '
            'creator="GDAL 2.3.2" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:ogr="http://osgeo.org/gdal" '
            'xmlns="http://www.topografix.com/GPX/1/1" '
            'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
            'http://www.topografix.com/GPX/1/1/gpx.xsd">\n'
        )
        output_gpx.write(
            '<metadata>\n'
            f'<name>{output_gpx_path[6:-4]}</name>\n'
            '<desc>Export from GpsPrune</desc>\n'
            '</metadata>\n'
            '<trk>\n'
            f'<name>{output_gpx_path[6:-4]}</name>\n'
            '<number>1</number>\n'
            '<trkseg>\n')

        for _, row in df_geo.iterrows():
            for coordinates in list(row['geometry'].coords):
                output_gpx.write(
                    f'<trkpt lat="{coordinates[1]}" lon="{coordinates[0]}">\n'
                    '</trkpt>')
        output_gpx.write(
            '</trkseg>\n'
            '</trk>\n'
            '</gpx>')


def export_route_fragments(
        route: list,
        basic_gpx_path: str,
        city_geo: pd.DataFrame,
        city: str,
        crs_city: dict,
        ):

    route_fragments = []
    route_fragment = []
    route_fragment_length = 0
    for gh_id in route:
        segment_lenght = city_geo[
            city_geo['gh_id'] == gh_id]['length'].values[0]
        route_fragment_length += segment_lenght
        route_fragment.append(gh_id)
        if route_fragment_length >= GPX_FRAGMENT_THRESHOLD:
            route_fragments.append(route_fragment)
            route_fragment = []
            route_fragment_length = 0
    route_fragments.append(route_fragment)

    route_nested_fragments = []
    for route_fragment in route_fragments:
        route_mini_fragments = []
        route_mini_fragment = []
        route_mini_fragment_length = 0
        for gh_id in route_fragment:
            segment_lenght = city_geo[
                city_geo['gh_id'] == gh_id]['length'].values[0]
            route_mini_fragment_length += segment_lenght
            route_mini_fragment.append(gh_id)
            if route_mini_fragment_length >= GPX_MINI_FRAGMENT_THRESHOLD:
                route_mini_fragments.append(route_mini_fragment)
                route_mini_fragment = []
                route_mini_fragment_length = 0
        if len(route_mini_fragment) > 0:
            route_mini_fragments.append(route_mini_fragment)
        route_nested_fragments.append(route_mini_fragments)

    for i, route_fragment in enumerate(route_fragments):
        df_geo = route_to_df(
            route_fragment,
            city_geo,
            crs_city)['route_df_geo']
        output_gpx_path = f'{basic_gpx_path}_{i+1}.gpx'
        df_to_gpx(df_geo, output_gpx_path)

    for j, route_mini_fragments in enumerate(route_nested_fragments):
        for k, route_mini_fragment in enumerate(route_mini_fragments):
            alphabet = list(string.ascii_uppercase)
            df_geo = route_to_df(
                route_mini_fragment,
                city_geo,
                crs_city)['route_df_geo']
            output_gpx_path = f'{basic_gpx_path}_{j+1}_{alphabet[k]}.gpx'
            df_to_gpx(df_geo, output_gpx_path)


def export_route_for_polygon(
        g: nx.DiGraph(),
        super_g: nx.DiGraph(),
        city_geo: gpd.GeoDataFrame(),
        city: str,
        crs_city: dict,
        crs_init: dict,
        geojson_path: str,
        basic_gpx_path: str,
        ):
    # 1. get routes
    route = get_route_for_polygon(g, super_g)
    route_by_edge = route['route_by_edge']
    route_by_node = route['route_by_node']

    # 2. export route and route fragments
    df_geo = route_to_df(
        route_by_node,
        city_geo,
        crs_city)['route_df_geo']

    df_to_geojson(df_geo, crs_init, geojson_path)

    export_route_fragments(
        route_by_node,
        basic_gpx_path,
        city_geo,
        city,
        crs_city)

def export_route_for_selected_segments(
        g: nx.DiGraph(),
        super_g: nx.DiGraph(),
        city_geo: gpd.GeoDataFrame(),
        city: str,
        crs_city: dict,
        crs_init: dict,
        geojson_path: str,
        basic_gpx_path: str,
        selected_segments: list,
):
    # 1. get routes
    selected_segments_route = get_route_for_selected_segments(
        super_g,
        selected_segments,
        weight='combined_weight',
        )

    selected_segments_route_by_node = selected_segments_route['route_by_node']

    # 2. export route and route fragments
    df_geo = route_to_df(
        selected_segments_route_by_node,
        city_geo,
        crs_city)['route_df_geo']

    df_to_geojson(df_geo, crs_init, geojson_path)
    export_route_fragments(
        selected_segments_route_by_node,
        basic_gpx_path,
        city_geo,
        city,
        crs_city)
    

# EXPORT TO SERVER ============================================================
def upload_to_dropbox(
        city: str,
        task_tag: str,
        camera_tag: str,
        route_dir: str):
    
    DROPBOX_ACCESS_TOKEN = '1lBaxt0_gPAAAAAAAAAAFGADXq8Jga1FYm0ki3OD_-qapkDyYdfjdxbIjGS9m7Bp'
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    for file in os.listdir(route_dir):
        local_file_path = os.path.join(route_dir, file)
        date_tag = datetime.datetime.today().strftime('%Y%m%d') + '_'
        dbx_file_path = f'/routes/{date_tag}{city}{task_tag}{camera_tag}/{file}'
        with open(local_file_path, 'rb') as f:
            dbx.files_upload(f.read(), dbx_file_path, mute=True)
    logger.info(f"\troutes are saved to {date_tag}{city}{task_tag}{camera_tag}")