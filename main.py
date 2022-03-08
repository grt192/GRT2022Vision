#!/usr/bin/env python3

import cv2
import socket
from turret import Turret
from intake import Intake
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


HOST = ''  # Empty string to accept connections on all available IPv4 interfaces
PORT = 5800  # Port to listen on (non-privileged ports are > 1023)


# Function to initialize video captures
stream_res = (160, 120)
fps = 30

turret_cap = None
intake_cap = None


def init_turret_cap():
    global turret_cap

    is_turret_cap = turret_cap is not None and turret_cap.isOpened()

    if not is_turret_cap:
        print('turret cap not initialized, trying again')
        turret_cap = cv2.VideoCapture('/dev/cam/turret', cv2.CAP_V4L)
        turret_cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        turret_cap.set(cv2.CAP_PROP_EXPOSURE, 10)  # 5 to 2000

        turret_cap.set(cv2.CAP_PROP_FRAME_WIDTH, stream_res[0])
        turret_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, stream_res[1])


def init_intake_cap():
    global intake_cap

    is_intake_cap = intake_cap is not None and intake_cap.isOpened()

    if not is_intake_cap:
        print('intake cap not initialized, trying again')
        intake_cap = cv2.VideoCapture('/dev/cam/intake', cv2.CAP_V4L)

        intake_cap.set(cv2.CAP_PROP_FRAME_WIDTH, stream_res[0])
        intake_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, stream_res[1])


# Init pipelines
turret = Turret()
intake = Intake()


# Constants
turret_address = '10.1.92.94'
turret_port = 5801

intake_address = '10.1.92.94'
intake_port = 5802


# Start intake and turret camera servers
def start_turret_stream():

    print('starting turret stream THREAD')
    server = ThreadedHTTPServer((turret_address, turret_port), TurretCamHandler)
    print('server started at http://' + turret_address + ':' + str(turret_port) + '/cam.html')
    server.serve_forever()

    while True:
        if stop.isSet():
            server.socket.close()


def start_intake_stream():

    print('starting intake stream THREAD')
    server = ThreadedHTTPServer((intake_address, intake_port), IntakeCamHandler)
    print('server started at http://' + intake_address + ':' + str(intake_port) + '/cam.html')
    server.serve_forever()

    while True:
        if stop.isSet():
            server.socket.close()

turret_frame = None
intake_frame = None

turret_vision_status = False
turret_theta = 0
hub_distance = 0
ball_detected = False

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class TurretCamHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global turret_vision_status, turret_theta, hub_distance
        global turret_frame

        # If getting a camera frame
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header(
                'Content-type',
                'multipart/x-mixed-replace; boundary=--jpgboundary'
            )
            self.end_headers()

            # Split up HTTP URL to get camera requested
            path_args = self.path.split('/')
            arg = path_args[len(path_args) - 1]  # eg. "cam" of cam.mjpg
            arg = arg[0:(len(path_args) - 7)]

            global turret_cap
            while True:
                try:
                    init_turret_cap()

                    # Run turret pipeline
                    ret, turret_frame = turret_cap.read()

                    if not ret:
                        turret_vision_status = False
                        turret_theta = 0
                        hub_distance = 0
                        continue

                    # Do this out here instead of in turret.py so that the frame gets preserved
                    turret_frame = cv2.rotate(turret_frame, cv2.ROTATE_90_CLOCKWISE)
                    turret_vision_status, turret_theta, hub_distance = turret.process(turret_frame)
                    print((turret_vision_status, turret_theta, hub_distance))

                    if arg == 'cam':
                        img_str = cv2.imencode('.jpg', turret_frame)[1].tobytes()
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', len(img_str))
                        self.end_headers()
                        self.wfile.write(img_str)

                    elif arg == 'cam2':
                        mask_img_str = cv2.imencode('.jpg', turret.masked_frame)[1].tobytes()
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', len(mask_img_str))
                        self.end_headers()
                        self.wfile.write(mask_img_str)

                    self.wfile.write(b"\r\n--jpgboundary\r\n")

                except KeyboardInterrupt:
                    self.wfile.write(b"\r\n--jpgboundary--\r\n")
                    break
                except BrokenPipeError:
                    continue

            return

        if self.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>'.encode('UTF-8'))
            self.wfile.write(('<img style="margin-right: 20px;" src="http://' + turret_address + ':' + str(turret_port) + '/cam.mjpg"/>').encode('UTF-8'))
            self.wfile.write(('<img src="http://' + turret_address + ':' + str(turret_port) + '/cam2.mjpg"/>').encode('UTF-8'))

            # Add data via paragraph
            self.wfile.write(('<p>Status: ' + str(turret_vision_status) + '</p>').encode('UTF-8'))
            self.wfile.write(('<p>Turret theta: ' + str(turret_theta) + '</p>').encode('UTF-8'))
            self.wfile.write(('<p>Hub dist: ' + str(hub_distance) + '</p>').encode('UTF-8'))

            self.wfile.write('</body></html>'.encode('UTF-8'))
            return


class IntakeCamHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global ball_detected
        global intake_frame

        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header(
                'Content-type',
                'multipart/x-mixed-replace; boundary=--jpgboundary'
            )
            self.end_headers()

            while True:
                try:
                    init_intake_cap()

                    # Run intake pipeline
                    ret, intake_frame = intake_cap.read()

                    if not ret:
                        ball_detected = False
                        continue

                    ball_detected = intake.process(intake_frame)

                    img_str = cv2.imencode('.jpg', intake_frame)[1].tobytes()

                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', len(img_str))
                    self.end_headers()

                    self.wfile.write(img_str)
                    self.wfile.write(b"\r\n--jpgboundary\r\n")

                except KeyboardInterrupt:
                    self.wfile.write(b"\r\n--jpgboundary--\r\n")
                    break
                except BrokenPipeError:
                    continue
            return

        if self.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>'.encode('UTF-8'))
            self.wfile.write(('<img src="http://' + intake_address + ':' + str(intake_port) + '/cam.mjpg"/>').encode('UTF-8'))
            self.wfile.write(('<p>Balls? ' + str(ball_detected) + '</p>').encode('UTF-8'))
            self.wfile.write('</body></html>'.encode('UTF-8'))
            return


# Loop to connect to socket
stop = threading.Event()
while True:
    try:
        print('Attempting to connect')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use
            s.bind((HOST, PORT))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)

                # Start threads for streams
                turret_thread = threading.Thread(target=start_turret_stream)
                turret_thread.start()

                intake_thread = threading.Thread(target=start_intake_stream)
                intake_thread.start()

                # Loop to run everything
                while True:
                    # Send data
                    conn.send(bytes(str((turret_vision_status, turret_theta, hub_distance, ball_detected)) + "\n", "UTF-8"))

    except (BrokenPipeError, ConnectionResetError, ConnectionRefusedError) as e:
        print("Connection lost... retrying")
    except KeyboardInterrupt as e:
        stop.set()
        print('KeyboardInterrupt detected in outer socket loop... breaking')
        break
