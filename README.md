# GRT2022Vision

This repo stores our vision code for the 2022 season.

[How to run vision for GRT](https://docs.google.com/document/d/1yy8QnhipeAp4VnCuPegOZ6V85CWqvrHIrpeyWl7Jlu4/edit)

## Code Structure

### Main Scripts
Run any of the following 3 scripts to run the vision pipeline depending on your intention. Underlying is the `Main.py` script, which has two boolean flags: `jetson` and `connect_socket`.

If `jetson` is true, it'll stream to the corresponding address and connect to the corresponding socket (if `connect_socket` is also true).

If `connect_socket` is true, it will attempt to connect to the socket (if `jetson`, robot IP. If local, `localhost`). It sends the resulting vision data over the socket.

`JetsonMain.py` runs the socket (great for actual testing with the robot turret), `JetsonMain2.py` doesn't run the socket (this allows you to debug faster, since you can kill the program and rerun it. Once the socket connects once, it can't connect again without a reboot or waiting a couple minutes after a kill command.)

### Vision Pipelines
The actual OpenCV vision pipelines are in `Intake.py` and `Turret.py`.

### Image Sources
For better code structure, video sources (ie. USB camera) are abstracted as "Sources". For working with an actual camera feed, there is a `TurretSource.py` and `IntakeSource.py`. For debugging purposes, there is the `StaticImageSource.py`, allowing you to run vision pipelines on a specific image.

Sources are fed into vision pipelines by the HTTP stream. As we stream, we process frames.

### HTTP Streaming

IIRC, the basic code is from https://gist.github.com/n3wtron/4624820. 

The Main scripts start two threads/GenericHTTPServer objects for streaming (one for turret and one for intake). 

`GenericHTTPServer.py` takes a vision pipeline, a image source, and destination stream address. It runs it all, showing the result on the stream! 

## Jetson Setup

https://github.com/grt192/GRTCommandBased/wiki/Jetson-Setup

## Next Year...

- SolvePNP is probably a pretty reliable method but we never successfully got it working with the rotated camera. It might be worth taking a look at in future years.  
- The trig method for finding angles and distances didn't work/we did not know how to debug it. Not sure why, but with more time better analysis can be done.
- Having multiple methods of calculating angles and distance would be great, like how LigerBots does theirs. They also have a cool code structure that allows for easier testing
- ATM, our home-cooked HTTP streaming code doesn't have particularly low latency, so either use a package (cscore, mjpegstreamer) or figure out how to make it faster. Should consider using `gstreamer` streaming to HTTP (like how Spookies does it)
- Expect to encounter networking issues at competition, so make sure all your IP addresses and port numbers (as well as bandwidth usage) follow the rules.  