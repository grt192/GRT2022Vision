# jetson-vision

Copy files from laptop to Jetson w/o copying subfolders.

`scp GRT2022Vision/* grt@10.1.92.94:~/GRT2022Vision`
`fuser -k 5800/tcp`
- fix by removing outliers outside of where most of the contours are positioned x-wise 
- debug angles code w/ the calib function in turret.py
- udev by position on usb hub (jetson) in case first camera dies

other things
- test w/ different object points
- try regular solvepnp not solvep3p and see how it is
- ligerbots for their solvepnp procedure (also open on my phone)
- any way to wrap socket code 
- any way to abstract the local vs jetson; image vs video capture testing?