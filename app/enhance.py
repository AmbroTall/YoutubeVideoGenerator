import subprocess
import os

base_dir = os.path.dirname(os.path.dirname(__file__))
input_audio_path = os.path.join(base_dir,"app", "output_audio","de")
output_audio_path= os.path.join(base_dir,"app", "enhanced_audio")
enhance_executable = "resemble-enhance"
device = 'cpu'
try:
            # Run the enhancement process for each file
            command = [enhance_executable, input_audio_path, output_audio_path, "--device", device]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")
            print(f"Command error: {result.stderr}")
            
except subprocess.CalledProcessError as e:
            print(f"Error running resemble-enhance: {e}")
            print(f"Command output: {e.output}")
