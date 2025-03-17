import os
import argparse
import logging
import contextlib
import pathlib as pl
try:
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

    return list(homeFolder.rglob("[0-9]" * 8 + "_unit*_session* *.mp4"))

def analyzeVideosQuietly(*args, **kwargs):
    """
    Call DeepLabCut's analyze_videos function but suppress messaging
    """

    kwargs_ = {}
    kwargs_.update(kwargs)
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        logging.disable(logging.CRITICAL)  # Disable logging
        try:
            return dlc.analyze_videos(*args, **kwargs_)
        finally:
            logging.disable(logging.NOTSET)  # Re-enable logging

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    args = parser.parse_args()
    videos = collectVideos(args.home)
    config = locateDeeplabcutProject()
    analyzeVideosQuietly(
        config,
        videos=videos,
        save_as_csv=True
    )