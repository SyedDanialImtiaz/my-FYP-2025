import tkinter as tk

def on_button_click():
    print("Button clicked!")

# Create the main window
root = tk.Tk()
root.title("Simple GUI")
root.geometry("300x150")  # Width x Height

# Create a button and place it in the window
button = tk.Button(root, text="Click Me!", command=on_button_click)
button.pack(pady=50)

# Start the GUI event loop
root.mainloop()
