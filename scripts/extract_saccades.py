import argparse
import pathlib as pl
from data_extraction import PrintSuppressor
try:
    import saccade_extraction as se
except:
    se = None

# TODO: Make this more intelligent/flexible
def locateSaccadeExtractionProject():
    """
    """

    return '/home/schollab-dion/Projets/sacnet3/config.yaml'

def collectFileSets(
    homeFolder
    ):
    """
    """

    if type(homeFolder) != pl.Path:
        homeFolder = pl.Path(homeFolder)
    poseEstimates = list(homeFolder.rglob('*DLC*.csv'))
    fileSets = list()
    for poseEstimate in poseEstimates:
        fileSet = list()
        fileSet.append(poseEstimate)
        stem = poseEstimate.name.split('DLC')[0].rstrip('-0000')
        result = list(homeFolder.rglob(f'*{stem}*timestamps.txt'))
        if len(result) == 1:
            interframeIntervals = result.pop()
            fileSet.append(interframeIntervals)
        fileSet = tuple(fileSet)
        if len(fileSet) == 2:
            fileSets.append(fileSet)
        else:
            pass

    return fileSets

def extractSaccades(*args, **kwargs):
    """
    """

    kwargs_ = {}
    kwargs_.update(kwargs)
    kwargs_['modelIndex'] = -1
    se.extractRealSaccades(
        *args, **kwargs
    )

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    namespace = parser.parse_args()
    fileSets = collectFileSets(namespace.home)
    config = locateSaccadeExtractionProject()
    with PrintSuppressor():
        extractSaccades(config, fileSets)