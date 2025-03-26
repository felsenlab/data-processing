import os
import argparse
import logging
import contextlib
import pathlib as pl
from data_extraction import PrintSuppressor
try:
    with PrintSuppressor():
        import deeplabcut as dlc
except ImportError:
    dlc = None

# TODO: Make this more intelligent/flexible
def locateDeeplabcutProject(
    ):
    """
    """

    return '/home/polegpolskylab/Documents/DeepLabCut/sacnet/sacnet-josh-2025-01-29/config.yaml'

def collectVideos(
    homeFolder,
    ):
    """
    """
    if type(homeFolder) != pl.Path:
        homeFolder = pl.Path(homeFolder)

    return [str(path) for path in homeFolder.rglob(f"{'[0-9]' * 8}*unit*session*.mp4")]

def analyzeVideosQuietly(*args, **kwargs):
    """
    Call DeepLabCut's analyze_videos function but suppress messaging
    """

    kwargs_ = {}
    kwargs_.update(kwargs)
    with PrintSuppressor():
        return dlc.analyze_videos(*args, **kwargs_)

    # Delete h5 and pickle files
    for video in kwargs_['videos']:
        video = pl.Path(video)
        parent = video.parent
        for file in parent.iterdir():
            if 'DLC' in file.name and (file.suffix == '.h5' or file.suffix == '.pickle'):
                file.unlink()

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    namespace = parser.parse_args()
    videos = collectVideos(namespace.home)
    # for video in videos:
    #     print(video)
    config = locateDeeplabcutProject()
    analyzeVideosQuietly(
        config,
        videos=videos,
        save_as_csv=True
    )