# my-FYP-2025

My Final Year Project titled "Anti-Deepfake Watermarking for Video Authentication"

## **TODO LIST:**

- [✅] browse and upload video  
- [✅] get video data
- [✅] display/print video info on terminal/GUI  
- [✅] get videos frames  
- [✅] reattach the frames to get original video  
- [✅] find open source face recognition algorithm  
- [✅] research on watermarking algo  
- [❌] fix missing audio after reattaching video  
- [✅] put the watermark on faces
- [❌] find open source face swapper/deepfake program
- [❌] if faces in frames are less than 0.5 sec, ignore the face
- [❌] make sure the face map embedding work
- [✅] verify the watermark on faces
- [❌] tests watermarked videos with deepfake/faceswap programs
- [❌] remove face boundary boxes when finished

## How to Run Program

1. **Set up the environment**  
    Ensure you have Python 3.8 or higher installed on your system. You can download it from [python.org](https://www.python.org/).

2. **Clone the repository**  

    ```bash
    git clone https://github.com/your-username/my-FYP-2025.git
    cd my-FYP-2025
    ```

3. **Install FFmpeg**  
    FFmpeg is required for video processing.  
    - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the `bin` folder to your system PATH. Or install using winget.

      ```bash
      winget install ffmpeg
      ```

    - **macOS (with Homebrew):**  

      ```bash
      brew install ffmpeg
      ```

    - **Linux (Debian/Ubuntu):**  

      ```bash
      sudo apt-get install ffmpeg
      ```

4. **Create a virtual environment**  
    Navigate to the `my-FYP-2025` folder before creating the virtual environment.

    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate
    ```

5. **Install the required dependencies**  

    ```bash
    pip install -r requirements.txt
    ```

6. **Run the program**  

    ```bash
    python src\main.py
    ```
