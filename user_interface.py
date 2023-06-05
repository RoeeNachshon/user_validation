import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import create_train_files
import train_model


def init():
    username = _get_username()
    should_record = _open_choice_window("Should I record?")
    _init_model(username, should_record)
    window = _create_window()
    window.wm_attributes('-transparentcolor', window['bg'])
    output_frame = _create_frame_for_output_boxes(window)
    output_label = _create_a_status_label(output_frame)
    _create_title(output_frame, "accuracy:")
    output_box2 = _create_an_output_box(output_frame)
    switch_var = _create_switch_button(output_frame, "lock")
    return window, output_label, output_box2, switch_var, username, should_record


def _init_model(username, should_record):
    if not username_in_system_user(username) and should_record == "No":
        create_train_files.create_train_file(username)
        train_model.get_model(username)


def username_in_system_user(username):
    with open("names_for_system.txt", "r") as file:
        names = file.readline()
        return username in names


def _open_choice_window(title):
    def submit_answer():
        nonlocal answer
        if var.get() == 1:
            answer = "Yes"
        else:
            answer = "No"
        window.destroy()

    answer = "No"

    window = tk.Tk()
    window.title(title)

    var = tk.IntVar()

    radio_yes = tk.Radiobutton(window, text="Yes", variable=var, value=1)
    radio_yes.pack()

    radio_no = tk.Radiobutton(window, text="No", variable=var, value=2)
    radio_no.pack()

    button_submit = tk.Button(window, text="Submit", command=submit_answer)
    button_submit.pack()

    window.mainloop()

    return answer


def _get_username():
    def submit_username():
        nonlocal username
        username = entry.get()
        window.destroy()

    username = ""

    window = tk.Tk()
    window.title("Enter Username")

    label = tk.Label(window, text="Username:")
    label.pack()

    entry = tk.Entry(window)
    entry.pack()

    button = tk.Button(window, text="Submit", command=submit_username)
    button.pack()

    window.mainloop()

    return username


def close_window(window):
    # Function to close the window
    window.destroy()


def _create_window():
    # Create the main window
    window = tk.Tk()
    window.title("Input and Output Window")
    # Configure the window to open in full screen
    window.attributes('-topmost', True)  # Set the window to be topmost

    window.attributes('-fullscreen', True)  # Open the window in fullscreen mode

    # Bind the Escape key to close the window
    window.bind('<Escape>', lambda event: close_window(window))

    return window


def _create_title(frame, text):
    # Add a title for the input box
    input_title_label = tk.Label(frame, text=text, font=font.Font(size=20, weight='bold'))
    input_title_label.pack(side=tk.TOP)


def _create_an_output_box(output_frame):
    # Create the first output screen
    output_textbox_font = font.Font(size=14)  # Define font size for output text boxes
    output_textbox = tk.Text(output_frame, height=5, width=40, font=output_textbox_font)
    output_textbox.pack(side=tk.TOP)
    output_textbox.configure(state='disabled')  # Set output text box as read-only
    return output_textbox


def _create_frame_for_output_boxes(window):
    # Create a frame for the output screens
    output_frame = tk.Frame(window)
    output_frame.pack(side=tk.TOP, padx=10, pady=10, anchor='ne')
    return output_frame


def update_output_box(output_textbox, content):
    # Update the content of the output box
    output_textbox.config(state='normal')
    output_textbox.delete('1.0', tk.END)  # Clear previous content
    output_textbox.insert(tk.END, str(content) + "\n")
    output_textbox.config(state='disabled')


def _create_a_status_label(output_frame):
    # Create a label to display the text "not sure"
    output_label = tk.Label(output_frame, text="not user", font=font.Font(size=24, weight='bold'), fg="red")
    output_label.pack(side=tk.TOP)
    return output_label


def update_status_label(output_label, content, color):
    # Update the content and color of the output label
    output_label.config(text=str(content), fg=color)


def _create_switch_button(output_frame, text):
    # Create a switch button below the output box
    switch_var = tk.IntVar()
    switch_button = tk.Checkbutton(output_frame, text=text, variable=switch_var, font=font.Font(size=20))
    switch_button.pack(side=tk.TOP)
    return switch_var
