import os
import argparse
import logging
import contextlib
import pathlib as pl
with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
    logging.disable(logging.CRITICAL)  # Disable logging
    try:
        import deeplabcut as dlc
    except ImportError:
        dlc = None
    finally:
        logging.disable(logging.NOTSET)  # Re-enable logging

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
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        logging.disable(logging.CRITICAL)  # Disable logging
        try:
            return dlc.analyze_videos(*args, **kwargs_)
        finally:
            logging.disable(logging.NOTSET)  # Re-enable logging

    # Delete h5 and pickle files
    for video in kwargs_['videos']:
        video = pl.Path(video)
        parent = video.parent
        for file in parent.iterdir():
            if video.stem in file.name and (file.suffix == '.h5' or file.suffix == '.pickle'):
                file.unlink()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    namespace = parser.parse_args()
    videos = collectVideos(namespace.home)
    config = locateDeeplabcutProject()
    # dlc.analyze_videos(
    #     config,
    #     videos=videos,
    #     save_as_csv=True
    # )
    analyzeVideosQuietly(
        config,
        videos=videos,
        save_as_csv=True
    )