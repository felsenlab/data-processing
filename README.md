# data-processing
This is a repository for the code used to process data from the Felsen Lab.


### Animal Info
Session-level metadata on animals. 
- **animal_info/description** - 
- **animal_info/name**
- **animal_info/weight**

### Pose
Information from cameras and DeepLabCut
- **frames/[left,right]/timestamps** - (N) - Cumulative frame times from [right, left]Cam_timestamps.txt file for each session.
- **frames/[left,right]/frametimes_clock** - (N) - LabJack timing information for each frame captured from the camera. Units are seconds since starting of the recording.
- **frames/[left,right]/projections** - (N, 2) - Pupil center projected onto the nasal-temporal axis, derived from the Saccade Extraction package. 
- **frames/[left,right]/uncorrected** - Group of (N) datasets. An x-coordinate and a y-coordinate series for each trackpoint out of DeepLabCut. 
	- eye_dorsal
	- eye_nasal
	- eye_temporal
	- eye_ventral
	- pupil_center
	- pupil_dorsal
	- pupil_nasal
	- pupil_temporal
	- pupil_ventral


### Saccades
Information related to putative and real saccade events.
- **saccades/[left,right]/labels** - (N,1) - Binary character labels for each saccade event, generated from Saccade Extraction. b'n' for nasal, b't' for temporal, b'x' for putative that does not pass quality metrics to be deemed a 'real' saccade.
- **saccades/[left,right]/labels_coded** - (N,1) - Labels for each saccade event, generated from Saccade Extraction. '1.' for nasal, '-1.' for temporal, '0.' for putative that does not pass quality metrics to be deemed a 'real' saccade.
- **saccades/[left,right]/onsets** - (N) - Fractional frame indices for the onset of each putative saccade.
- **saccades/[left,right]/offsets** - (N) - Fractional frame indices for the offset of each putative saccade.
- **saccades/[left,right]/saccade_onsets_seconds** - (N) - Onset of each saccade in terms of seconds since LabJack recording. Only present in sessions with LabJack data.
- **saccades/[left,right]/saccade_offsets_seconds** - (N) - Off of each saccade in terms of seconds since LabJack recording. Only present in sessions with LabJack data.
- **saccades/[left,right]/waveforms** - (N, 52) - Extracted waveforms of putative saccades. Derived from **pose/[left,right]/projections** traces.



### Running instructions
- Here are the instructions for running a data session.
- White workstation login credentials : 
	- username : schollab-dion
	- password : H&W,1962
- Make sure that FelsenNAS is connected. Open 'Files' and check that 'the flnas' directory on the left side above 'Other Locations' opens to show the contents of the NAS. If the window is blank upon clicking this location, then the computer is not connected to the NAS over the network.  
	- Reconnection can be done with the following command : `sudo mount -t cifs //140.226.100.108/FelsenNASFolder /mnt/flnas -o username=felsenlab`
- It is recommended that you copy your data from the FelsenNAS to the workstation you're using. Some steps of the pipeline are notably slower over when fetching data over the network.
- Verify that all data is contained in your session.
	- Right click on the session-level directory and select 'Properties'.
	- In the window that pops up, the number of items and total size of the folder should be tallied under 'Contents'.
	- Verify that the 'Contents' information is the same between the FelsenNAS file and the file downloaded to your workstation.
- Running your data.
	- ./process session ../path/to/your/data (data_identity_flag)
	- 0 - default, presumes LabJack and ephys
	- 1 - Presumes, LabJack, ephys, strain gauge
	- 2 - presumes only videos (crystal's data)
	-  The 'process_session' script will execute each stage of the pipeline according to the instructions it has received in the data_identity_flag. 
- What does each module do?
	- Concise recap. This information is in the data description, but putting some lines here is helpful for end-users so they know the steps in the process


- Talking w/ Anna and Crystal about how to use these things.

 Meeting again w/ Gidon 3pm June 19th
 
