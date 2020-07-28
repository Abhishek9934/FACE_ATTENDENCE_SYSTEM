#! /bin/bash
source /home/usr_2018csb1201_iitrpr_ac_in/faceapp/FACE_ATTENDENCE_SYSTEM/env/bin/activate
cd /home/usr_2018csb1201_iitrpr_ac_in/faceapp/FACE_ATTENDENCE_SYSTEM/
gunicorn -w 2 -b :9999 main:app

