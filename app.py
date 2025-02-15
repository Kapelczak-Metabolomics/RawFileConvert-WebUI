import os
import sys
import shutil
import subprocess
import zipfile
import requests
import streamlit as st

# Set page title and description
st.title("Thermo .raw to .mzML Converter")
st.write("Upload your Thermo .raw files for conversion to .mzML format using ThermoRawFileParser.")

def install_thermo_raw_file_parser():
	"""
	Check if ThermoRawFileParser is installed.
	If not, download and extract the pre-built binary from GitHub.
	"""
	exe_name = "ThermoRawFileParser"
	if sys.platform.startswith("win"):
		exe_name += ".exe"

	# If already installed, return its path
	existing_path = shutil.which(exe_name)
	if existing_path:
		st.info("ThermoRawFileParser is already installed at: " + existing_path)
		return existing_path

	st.info("ThermoRawFileParser not found. Downloading and installing now...")

	# Define the GitHub download URL for the pre-built binary.
	# NOTE: Ensure that the URL points to a valid release for your operating system.
	download_url = "https://github.com/compomics/ThermoRawFileParserGUI/releases/download/v1.0.0/ThermoRawFileParser_Linux_64bit.zip"
	zip_filename = "ThermoRawFileParser.zip"
	install_dir = os.path.join(os.getcwd(), "ThermoRawFileParser_bin")
	os.makedirs(install_dir, exist_ok=True)

	try:
		# Download the zip file
		r = requests.get(download_url, stream=True)
		r.raise_for_status()  # Ensure we got a valid response
		with open(zip_filename, "wb") as f:
			for chunk in r.iter_content(chunk_size=8192):
				if chunk:
					f.write(chunk)
		st.success("Downloaded ThermoRawFileParser binary.")

		# Extract the zip file to the install_dir
		with zipfile.ZipFile(zip_filename, "r") as zip_ref:
			zip_ref.extractall(install_dir)
		st.success("Extracted ThermoRawFileParser.")

		# Locate the executable inside the extracted folder
		exe_path = None
		for root, dirs, files in os.walk(install_dir):
			for file in files:
				if file == exe_name:
					exe_path = os.path.join(root, file)
					break
			if exe_path:
				break

		if exe_path is None:
			st.error("ThermoRawFileParser binary not found in the extracted files.")
			return None

		# Make sure the executable has execution permissions (Linux/Mac)
		if not sys.platform.startswith("win"):
			os.chmod(exe_path, 0o755)

		# Add the directory containing the executable to the PATH
		os.environ["PATH"] += os.pathsep + os.path.dirname(exe_path)

		st.success("ThermoRawFileParser installed at: " + exe_path)
		return exe_path

	except Exception as e:
		st.error("Could not install ThermoRawFileParser. Error: " + str(e))
		return None

# Install or locate the ThermoRawFileParser
converter_path = install_thermo_raw_file_parser()

# File uploader for .raw files
uploaded_files = st.file_uploader("Choose .raw file(s)", type=["raw"], accept_multiple_files=True)

# Temporary directory for saving uploaded files and outputs
temp_dir = "temp_files"
os.makedirs(temp_dir, exist_ok=True)

if st.button("Convert"):
	if converter_path is None:
		st.error("ThermoRawFileParser is not installed. Please check the logs above.")
	elif not uploaded_files:
		st.error("Please upload at least one .raw file.")
	else:
		converted_files = []
		for uploaded_file in uploaded_files:
			# Save the uploaded file locally
			upload_path = os.path.join(temp_dir, uploaded_file.name)
			with open(upload_path, "wb") as f:
				f.write(uploaded_file.getbuffer())

			# Define output directory for the conversion result
			output_dir = os.path.join(temp_dir, "converted")
			os.makedirs(output_dir, exist_ok=True)

			# Build the command to run ThermoRawFileParser
			command = [converter_path, "-i", upload_path, "-o", output_dir, "-f", "mzML"]

			try:
				subprocess.run(command, check=True)
				# Construct the expected output filename
				mzml_filename = os.path.splitext(uploaded_file.name)[0] + ".mzML"
				mzml_filepath = os.path.join(output_dir, mzml_filename)
				if os.path.exists(mzml_filepath):
					converted_files.append(mzml_filepath)
				else:
					st.error("Conversion failed for " + uploaded_file.name)
			except subprocess.CalledProcessError as e:
				st.error("An error occurred while converting " + uploaded_file.name)
				st.error(str(e))

		# Provide download links for successfully converted files.
		if converted_files:
			st.success("Conversion successful!")
			for file in converted_files:
				with open(file, "rb") as f:
					st.download_button(
						label="Download " + os.path.basename(file),
						data=f,
						file_name=os.path.basename(file),
						mime="application/octet-stream"
					)