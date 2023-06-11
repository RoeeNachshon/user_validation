import os
import tkinter as tk
from tkinter import font
import create_train_files
import train_model


def init() -> tuple:
    """
    The main of the UI.
    :return: Tuple of the  window, output_label, output_box2, switch_var, username and  the should_record switch

    """
    username = _get_username()
    should_record = _open_choice_window("Should I record?")
    _make_new_model_available(username, should_record)
    window = _create_window()
    output_frame = _create_frame_for_output_boxes(window)
    output_label = _create_a_status_label(output_frame)
    _create_title(output_frame, "accuracy:")
    output_box2 = _create_an_output_box(output_frame)
    switch_var = _create_switch_button(output_frame, "lock")
    return window, output_label, output_box2, switch_var, username, should_record


def _make_new_model_available(username: str, should_record: str):
    """
    if needed creates new model and train files.
    :param username: A string of the user name
    :param should_record: A string of the user's choice
    :return: None
    """
    if not os.path.exists(f"saved_models/{username}") and should_record == "No":
        create_train_files.create_train_file(username)
        train_model.init_model(username)


def _open_choice_window(title: str) -> str:
    """
    Opens a window with two radio buttons (Yes/No)
    :param title: A string of the title of the window
    :return: A string of the users choice
    """
    def _submit_answer():
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

    button_submit = tk.Button(window, text="Submit", command=_submit_answer)
    button_submit.pack()

    window.mainloop()

    return answer


def _get_username() -> str:
    """
    Opens a window for the input of the username
    :return: A string of the user name
    """
    def _submit_username():
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

    button = tk.Button(window, text="Submit", command=_submit_username)
    button.pack()

    window.mainloop()

    return username


def _close_window(window: tk.Tk):
    """
    Closes the given window.
    :param window: The window to close
    :return: None
    """
    # Function to close the window
    window.destroy()


def _create_window() -> tk.Tk:
    """
    Creates the main window
    :return: The new window
    """
    # Create the main window
    window = tk.Tk()
    window.title("Input and Output Window")
    # Configure the window to open in full screen
    window.attributes('-topmost', True)  # Set the window to be topmost
    # window.wm_attributes('-fullscreen', True)

    # Bind the Escape key to close the window
    window.bind('<Escape>', lambda event: _close_window(window))

    return window


def _create_title(frame: tk.Frame, text: str):
    """
    Creates a title on the window
    :param frame: The frame of the title
    :param text: The text of the title
    :return: None
    """
    # Add a title for the input box
    input_title_label = tk.Label(frame, text=text, font=font.Font(size=20, weight='bold'))
    input_title_label.pack(side=tk.TOP)


def _create_an_output_box(output_frame: tk.Frame) -> tk.Text:
    """
    Creates an output box
    :param output_frame: The frame for the box
    :return: The new box
    """
    # Create the first output screen
    output_textbox_font = font.Font(size=14)  # Define font size for output text boxes
    output_textbox = tk.Text(output_frame, height=5, width=40, font=output_textbox_font)
    output_textbox.pack(side=tk.TOP)
    output_textbox.configure(state='disabled')  # Set output text box as read-only
    return output_textbox


def _create_frame_for_output_boxes(window: tk.Tk) -> tk.Frame:
    """
    Creates a frame for the output box
    :param window: The window to create it on
    :return: The frame
    """
    # Create a frame for the output screens
    output_frame = tk.Frame(window)
    output_frame.pack(side=tk.TOP, padx=10, pady=10, anchor='ne')
    return output_frame


def update_output_box(output_textbox: tk.Text, content: str):
    """
    Updates the box on the window.
    :param output_textbox: The box to update
    :param content: The text to update it with
    :return: None
    """
    # Update the content of the output box
    output_textbox.config(state='normal')
    output_textbox.delete('1.0', tk.END)  # Clear previous content
    output_textbox.insert(tk.END, str(content) + "\n")
    output_textbox.config(state='disabled')


def _create_a_status_label(output_frame: tk.Frame) -> tk.Label:
    """
    Creates the status label
    :param output_frame: The frames for the label
    :return: The label
    """
    # Create a label to display the text "not sure"
    output_label = tk.Label(output_frame, text="not user", font=font.Font(size=24, weight='bold'), fg="red")
    output_label.pack(side=tk.TOP)
    return output_label


def update_status_label(output_label: tk.Label, content: str, color: str):
    """
    Updates the label by the given arguments
    :param output_label: The label to update
    :param content: What to write
    :param color: What color
    :return: None
    """
    # Update the content and color of the output label
    output_label.config(text=str(content), fg=color)


def _create_switch_button(output_frame: tk.Frame, text: str) -> tk.IntVar:
    """
    Creates the switch button on the main window
    :param output_frame: The frame for the switch
    :param text: The text of the switch
    :return: The switch
    """
    # Create a switch button below the output box
    switch_var = tk.IntVar()
    switch_button = tk.Checkbutton(output_frame, text=text, variable=switch_var, font=font.Font(size=20))
    switch_button.pack(side=tk.TOP)
    return switch_var
