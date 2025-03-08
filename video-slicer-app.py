import streamlit as st
import subprocess
import os
import signal

# Function to cut the video using ffmpeg
def cut_video(input_path, segment_length, output_dir, base_name):
    try:
        # Get video duration using ffmpeg
        command = f"ffmpeg -i \"{input_path}\""
        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        video_duration = 0
        for line in result.stderr.splitlines():
            if "Duration" in line:
                duration_str = line.split('Duration:')[1].split(',')[0].strip()
                hours, minutes, seconds = map(float, duration_str.split(':'))
                video_duration = hours * 3600 + minutes * 60 + seconds
                break

        # Create the output folder named after the input video with segment length
        output_folder = os.path.join(output_dir, f"{base_name}_{segment_length}")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Calculate total number of slices needed
        total_slices = int(video_duration // segment_length) + (1 if video_duration % segment_length != 0 else 0)

        # Show estimated number of slices to the user
        st.write(f"Total slices to be created: {total_slices}")

        # Initialize the progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Create a loop to cut the video into segments
        start_time = 0
        segment_number = 1

        # Check for cancel flag in session state
        cancel_button = st.button("Cancel Cutting")
        if "cancelled" not in st.session_state:
            st.session_state.cancelled = False

        while start_time < video_duration and not st.session_state.cancelled:
            # Calculate end time for this segment
            end_time = min(start_time + segment_length, video_duration)
            
            # Define the output file name for each part in the format Name_Length_Number.mp4
            output_file = os.path.join(output_folder, f"{base_name}_{segment_length}_{segment_number:02d}.mp4")
            
            # Construct the ffmpeg command to cut the video
            ffmpeg_command = [
                "ffmpeg", "-i", input_path, "-ss", str(start_time), "-to", str(end_time),
                "-c", "copy", output_file
            ]
            
            # Run the ffmpeg command asynchronously
            process = subprocess.Popen(ffmpeg_command)

            # Wait for the process to finish (without checking continuously for cancel)
            process.wait()

            # After the process completes, update the progress bar
            progress = int((segment_number / total_slices) * 100)
            progress_bar.progress(progress)

            # Update status text
            status_text.text(f"Processing slice {segment_number} of {total_slices}...")
            
            # Update start time and segment number
            start_time = end_time
            segment_number += 1

            # Check if the user clicked the cancel button
            if st.session_state.cancelled:
                process.terminate()  # Terminate the ffmpeg process if cancel is requested
                st.write("Cutting process cancelled.")
                return

        st.success("Video successfully cut into segments and saved.")

    except Exception as e:
        st.error(f"An error occurred: {e}")


# Streamlit UI setup
st.title("Video Cutter with Streamlit")

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# Length selection for cutting (slider instead of selectbox)
segment_length = st.slider("Select segment length", min_value=1, max_value=600, value=30, step=1)

# Folder selection for saving output
output_folder = st.text_input("Enter the folder to save clips", "/path/to/output/folder")

# Start the cutting process when the button is clicked
if st.button("Cut Video"):
    if uploaded_file is not None and output_folder:
        # Save the uploaded file to a temporary location
        uploaded_video_path = "uploaded_video.mp4"
        with open(uploaded_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract base name of the uploaded video (without extension)
        base_name = os.path.splitext(uploaded_file.name)[0]

        # Start the video cutting process
        cut_video(uploaded_video_path, segment_length, output_folder, base_name)

    else:
        st.warning("Please upload a video file and specify the output folder.")
