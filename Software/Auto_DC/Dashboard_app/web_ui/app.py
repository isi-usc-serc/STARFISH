from flask import Flask, render_template, redirect, url_for
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start_host")
def start_host():
    subprocess.Popen(["python3", "../PC_Host/Host_Receiver.py"])
    return redirect(url_for("index"))

@app.route("/run_plotting")
def run_plotting():
    subprocess.Popen(["python3", "../Plotting/plot_results.py"])
    return redirect(url_for("index"))

@app.route("/run_calibration")
def run_calibration():
    subprocess.Popen(["python3", "../Calibration/calibrate_cameras.py"])
    return redirect(url_for("index"))

@app.route("/run_pi_client")
def run_pi_client():
    subprocess.Popen(["python3", "../Pi_Client/Pi_Client.py"])
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
