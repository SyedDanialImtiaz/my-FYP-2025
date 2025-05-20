# my-FYP-2025

My Final Year Project titled "Anti-Deepfake Watermarking for Video Authentication"

## **TODO LIST:**

- [✅] browse and upload video  
- [✅] get video data
- [✅] display/print video info on terminal/GUI  
- [✅] get videos frames  
- [✅] reattach the frames to get original video  
- [✅] find open source face recognition algorithm  
- [❌] research on watermarking algo  
- [❌] fix audio missing after stitching  
- [❌] put the watermark on faces
- [❌] decrease face detection inaccuracy
- [❌] make own datasets
- [❌] find open source face swapper/deepfake program
- [❌] if faces in frames are less than 0.5 sec, ignore the face

## How to Run Program

1. **Set up the environment**  
    Ensure you have Python 3.8 or higher installed on your system. You can download it from [python.org](https://www.python.org/).

2. **Clone the repository**  

    ```bash
    git clone https://github.com/your-username/my-FYP-2025.git
    cd my-FYP-2025
    ```

3. **Create a virtual environment**  

    ```bash
    python -m venv venv
    source venv/bin/activate   
    # On Windows: 
    venv\Scripts\activate
    ```

4. **Install the required dependencies**  

    ```bash
    pip install -r requirements.txt
    ```

5. **Run the program**  

    ```bash
    python src\main.py
    ```
