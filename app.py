from flask import Flask, render_template, jsonify
import ctypes
import os

app = Flask(__name__)

dll_path = os.path.join(os.path.dirname(__file__), 'lib', 'libroverfsm.dll')

if not os.path.exists(dll_path):
    raise FileNotFoundError(f"DLL not found at {dll_path}")

rover_lib = ctypes.CDLL(dll_path)

rover_lib.createFSM.restype = ctypes.c_void_p
rover_lib.getState.argtypes = [ctypes.c_void_p]
rover_lib.getState.restype = ctypes.c_int
rover_lib.process.argtypes = [ctypes.c_void_p]  
rover_lib.process.restype = None
rover_lib.reset.argtypes = [ctypes.c_void_p]  # Reset function
rover_lib.reset.restype = None
rover_lib.destroyFSM.argtypes = [ctypes.c_void_p]

fsm_ptr = rover_lib.createFSM()
rover_start = {"onoff": 0}

STATE_NAMES = {
    0: "Idle",
    1: "Prepare",
    2: "PlanTrajectory",
    3: "Moving",
    4: "Pause",
    5: "Failed",
    6: "Success",
    7: "Low_Power_Mode",
    8: "Sleep"
}


@app.route('/')
def index():
    return render_template('index.html', onoff=rover_start["onoff"])

@app.route('/toggle', methods=['POST'])
def toggle():
    
    if rover_start["onoff"] == 0:
        rover_start["onoff"] = 1 
    else:
        rover_lib.reset(fsm_ptr)
        rover_start["onoff"] = 0

    state_value = rover_lib.getState(fsm_ptr)
    state_name = STATE_NAMES.get(state_value, "Unknown")
    return jsonify(onoff=rover_start["onoff"], state=state_name)

@app.route('/get_state', methods=['GET'])
def get_state():
    state_value = rover_lib.getState(fsm_ptr)
    state_name = STATE_NAMES.get(state_value, "Unknown")
    return jsonify(onoff=rover_start["onoff"], state=state_name)

@app.route('/prepare',methods=['GET'])
def prepare():
    if rover_start["onoff"] == 1:
        state_v=rover_lib.process(fsm_ptr)
        state_n = STATE_NAMES.get(state_v, "Unknown")

    return jsonify(onoff=rover_start["onoff"], state=state_n)

@app.route('/reset', methods=['POST'])
def reset():
    rover_lib.reset(fsm_ptr)  # Reset FSM state
    state_value = rover_lib.getState(fsm_ptr)
    state_name = STATE_NAMES.get(state_value, "Unknown")
    return jsonify(onoff=rover_start["onoff"], state=state_name)

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        # Cleanup FSM instance
        rover_lib.destroyFSM(fsm_ptr)
