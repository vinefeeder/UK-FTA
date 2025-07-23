# Edit the paths below
## WVDPATH is the  full location of your wvd file created by 'pywidevine create device...'
# windows start r"C:/  and use forward slashes in python style

#WVDPATH = r"/home/angela/devices/WVD/amlogic_mbox_v4.1.0-android_b71e4420_4445_l3.wvd"

##################################################
# Note This CDM is INSTALLED and  WORKING 

# Only edit WVDPATH if you want to use your own CDM!
##################################################
# this is set for the included emulator

WVDPATH = r"./WVD/google_aosp_on_ia_emulator_14.0.0_dcd562de_4464_l3.wvd"

# A base-directory for storage of downloaded videos. 
# The storage path will be extended by channel name and series 
# DO NOT USE A  TRAILING SLASH ON THIS PATH
# this for example is my SAVEPATH - change it to your own:  

SAVEPATH =  r"/home/angela/Programming/GET-KEYS/output"

# set line below to true to create a batch file to 
# download all available episodes.

BATCH_DOWNLOAD = False


# These paths apply to all UK-FTA scripts


C4_USES_N_m3u8DLRE = True      # Do not change
