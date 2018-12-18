from biom import load_table
import pandas as pd
import numpy as np
from skbio import  OrdinationResults, stats
import os
import click
import json 
from skbio.util import get_data_path
from shutil import copyfile
import os
from rankratioviz.generate import process_input,gen_rank_plot,gen_sample_plot

@click.command()
@click.option('--ranks', help='(str) Path to ordiantion \
                                         output from deicode & minstel')
@click.option('--in_biom', help='BIOM table describing taxon abundances for samples.')
@click.option('--in_taxonomy', default=None, help='Metadata table file for taxonomy.')
@click.option('--in_metadata', help='Metadata table file for samples.')
@click.option('--in_catagory', help='Metadata table catagory to plot.')
@click.option('--output_dir', help='Location of output files.')

def rank_plots(ranks: str, in_biom: str, in_metadata: str, 
               output_dir: str, in_taxonomy: str , in_catagory: str) -> None:

    U, V, table, metadata = process_input(ranks, in_biom, in_metadata, in_taxonomy)
    rank_plot_chart = gen_rank_plot(U, V, 0)
    sample_plot_json = gen_sample_plot(table, metadata, in_catagory)
    os.makedirs(output_dir, exist_ok=True)
    #write 
    os.mkdir(os.path.join(output_dir,'rank_plot_'+in_catagory))
    # copy files for viz
    loc_ = os.path.dirname(os.path.realpath(__file__))
    for file_ in os.listdir(os.path.join(loc_,'data')):
        if file_ != '.DS_Store':
            copyfile(get_data_path(file_), 
                     os.path.join(output_dir,'rank_plot_'+in_catagory,file_))
    #write new filez
    rank_plot_loc = os.path.join(output_dir,'rank_plot_'+in_catagory, 
                                 "rank_plot.json")
    sample_plot_loc = os.path.join(output_dir,'rank_plot_'+in_catagory,
                                   "sample_logratio_plot.json")

    rank_plot_chart.save(rank_plot_loc)
    # For reference: https://stackoverflow.com/a/12309296
    with open(sample_plot_loc, "w") as jfile:
        json.dump(sample_plot_json, jfile)
    return 

if __name__ == '__main__':
    rank_plots()

