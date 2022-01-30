from typing import Union
import cv2


class PipelineInterface:
    def __init__(self, name: str = '0', device_num: Union[int, str] = 0, is_local: bool = True):
        self.name = name
        self.cap = None
        self.frame = None
        self.device_num = device_num
        self.is_local = is_local

    '''
    Process a frame, returning a tuple:
    (Adjusted frame to send to camera stream, {dictionary: fields to send to network tables})
    '''
    def process(self):
        return None, self.process_frame()

    '''
    Process self.frame, returning data. Called privately
    '''
    def process_frame(self):
        return {}

    '''
    Returns the stream's FPS.
    '''
    def fps(self):
        return 30

    '''
    Returns the stream resolution.
    '''
    def stream_res(self):
        # List possible camera resolutions using `v4l2-ctl --list-formats-ext`
        return 160, 120

    '''
    Returns the name of this pipeline.
    '''
    def get_name(self):
        return 'Generic Pipeline Name'

    def get_device_num(self):
        return self.device_num

    '''
    Returns a VideoCapture with pipeline's device number and resolution.
    '''
    def get_capture(self):
        if self.is_local:
            self.cap = cv2.VideoCapture(self.get_device_num())
        else:
            self.cap = cv2.VideoCapture(self.get_device_num(), cv2.CAP_V4L)

        # Set video resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.stream_res()[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.stream_res()[1])

    def get_frame(self):
        return self.frame