import socket
import argparse
import time
import sys
from pylivelinkface import PyLiveLinkFace, FaceBlendShape
from xtest_wheel_pacer import XTestWheelPacer

# Use platform-specific smooth scrolling
if sys.platform == 'win32':
    import win32api
    import win32con
elif sys.platform == 'darwin':
    import Quartz
else:
    # For Linux, we'll use a different approach
    import subprocess

# Constants
DEFAULT_UDP_PORT = 11111
SCROLL_THRESHOLD = 0.15   # Minimum eyebrow movement to trigger scrolling
SCROLL_SPEED = 1         # Multiplier for scroll speed
MAX_SCROLL = 20         # Maximum scroll speed

# Lazily create Linux scroller when needed (Linux only)
_linux_scroller = None

def _get_linux_scroller():
    global _linux_scroller
    if _linux_scroller is None:
        _linux_scroller = XTestWheelPacer(
            min_rate=4.0,
            max_rate=40.0,
            ease_power=2.2,
            hysteresis=0.02,
            max_ticks_per_flush=6,
            flush_hz=50,
            max_input=1.0
        )
    return _linux_scroller



def smooth_scroll(amount):
    """
    Platform-specific smooth scrolling implementation
    """
    if sys.platform == 'win32':
        # Windows: Use win32api for smoother scrolling
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(amount * 120), 0)
    elif sys.platform == 'darwin':
        # macOS: Use Quartz for smooth scrolling
        scroll_unit = amount * 5
        event = Quartz.CGEventCreateScrollWheelEvent(
            None, Quartz.kCGScrollEventUnitLine, 1, int(scroll_unit)
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
    else:
        # Each frame after you compute scroll_amount:
        scroller = _get_linux_scroller()
        scroller.set_amount(amount)
        # Linux: Use xdotool with button numbers (4=up, 5=down)
        #button = "5" if amount < 0 else "4"  # Reversed: 5 = scroll down, 4 = scroll up
        #abs_amount = abs(float(amount))
        #if abs_amount > 0:
        #    scroll_steps = max(1, int(abs_amount))
        #    subprocess.run(["xdotool", "click", "--repeat", str(scroll_steps), "--delay", "1", button])

def start_face_tracking(port=DEFAULT_UDP_PORT):
    print("Starting face tracking. Press Ctrl+C to stop.")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow reuse of the address/port
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        print(f"Starting face tracking on UDP port {port}")
#        print("Move mouse to screen corner to abort")
        # open a UDP socket on all available interfaces with the given port
        s.bind(("", port)) 
        while True: 
            data, addr = s.recvfrom(1024) 
            #print(f"Received {len(data)} bytes from {addr}")
            # decode the bytes data into a PyLiveLinkFace object
            success, live_link_face = PyLiveLinkFace.decode(data)
            #print(f"Decode success: {success}")
            if success:
                # get eyebrow blendshape values
                get_bs = live_link_face.get_blendshape
                brow_down_left = get_bs(FaceBlendShape.BrowDownLeft)
                brow_down_right = get_bs(FaceBlendShape.BrowDownRight)
                brow_inner_up = get_bs(FaceBlendShape.BrowInnerUp)
                brow_outer_up_left = get_bs(FaceBlendShape.BrowOuterUpLeft)
                brow_outer_up_right = get_bs(FaceBlendShape.BrowOuterUpRight)
                
                # Combine the values
                
                brow_up = (
                    brow_inner_up + brow_outer_up_left + brow_outer_up_right
                ) / 3
                # For down movement: average of left and right
                brow_down = (brow_down_left + brow_down_right) / 2
                
                # Calculate scroll amount based on eyebrow movement
                scroll_amount = float(0)
                if brow_up > SCROLL_THRESHOLD:
                    # Scroll up (positive value)
                    scroll_amount = min(
                        SCROLL_SPEED * (brow_up - SCROLL_THRESHOLD),
                        MAX_SCROLL,
                    )
                elif brow_down > SCROLL_THRESHOLD:
                    # Scroll down (negative value)
                    scroll_amount = -min(
                        SCROLL_SPEED * (brow_down - SCROLL_THRESHOLD),
                        MAX_SCROLL,
                    )
                #scroll_amount = 1
                # Apply scrolling if there's movement
                if scroll_amount != 0:
                    smooth_scroll(scroll_amount)
                    # Tiny delay to prevent overwhelming the system
                    time.sleep(1/120)  # approximately 60fps
                
                print(f"Name: {live_link_face.name}")
                print(
                    f"Combined Brow Movement - Up: {brow_up:.2f}, Down: {brow_down:.2f}")
                print(f"Scroll amount: {scroll_amount}")
                print("-" * 40)
    except KeyboardInterrupt:
        print("Stopping face tracking...")
    finally:
        s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Eyebrow-controlled scroll using face tracking')
    parser.add_argument('--port', type=int, default=DEFAULT_UDP_PORT,
                      help=f'UDP port to listen on (default: {DEFAULT_UDP_PORT})')
    args = parser.parse_args()
    
    try:
        start_face_tracking(args.port)
    except KeyboardInterrupt:
        print("\nStopping face tracking...")
    except Exception as e:
        print(f"Error: {e}")
