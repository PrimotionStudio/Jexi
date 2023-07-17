from tkinter import scrolledtext
import tkinter as tk
import os
import json
import shutil
from datetime import datetime
import itertools


def get_folder_config():
    folder_config = {}

    if os.path.exists("folder_config.json"):
        with open("folder_config.json", "r") as json_file:
            folder_config = json.load(json_file)
    else:
        folder_config = {
            "Desktop": {
                "ext": [],
                "path": os.path.join(os.path.expanduser("~"), "Desktop")
            },
            "Pictures": {
                "ext": ["jpg", "png", "jpeg"],
                "path": os.path.join(os.path.expanduser("~"), "Pictures")
            },
            "Music": {
                "ext": ["mp3", "wav", "flac"],
                "path": os.path.join(os.path.expanduser("~"), "Music")
            },
            "Videos": {
                "ext": ["mp4", "avi", "mkv"],
                "path": os.path.join(os.path.expanduser("~"), "Videos")
            },
            "Documents": {
                "ext": ["doc", "docx", "pdf", "txt"],
                "path": os.path.join(os.path.expanduser("~"), "Documents")
            }
        }

        with open("folder_config.json", "w") as json_file:
            json.dump(folder_config, json_file, indent=4)

    return folder_config


def move_files(selected_folders):
    data = {}

    if os.path.exists("files.json"):
        with open("files.json", "r") as json_file:
            data = json.load(json_file)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_info = {}

    for folder in selected_folders:
        folder_path = os.path.expanduser(f"~/{folder}")
        files = os.listdir(folder_path)

        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):  # Check if it's a file
                if file not in file_info:
                    file_info[file] = []
                file_info[file].append(file_path)

    data[timestamp] = file_info

    with open("files.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    # Compare extensions with folder_config.json
    move_data = {}
    with open("folder_config.json", "r") as config_file:
        folder_config = json.load(config_file)

    for folder, folder_info in folder_config.items():
        folder_path = folder_info["path"]
        extensions = folder_info["ext"]

        for file, file_paths in file_info.items():
            _, extension = os.path.splitext(file)
            if extension.startswith("."):
                extension = extension[1:]  # Remove the leading dot

            if (
                extension in extensions
                and folder_path != os.path.dirname(file_paths[0])
            ):
                new_dir = folder_path
                new_file = file
                i = 1

                # Check for duplicates in the destination folder
                while new_file in os.listdir(new_dir):
                    file_name, file_ext = os.path.splitext(file)
                    new_file = f"{file_name} jexi_copy{i}{file_ext}"
                    i += 1

                move_data[file] = {
                    "prev_dir": os.path.dirname(file_paths[0]).replace("/", "\\"),
                    "file": file,
                    "new_dir": new_dir.replace("/", "\\"),
                    "new_file": new_file,
                }

    move_logs = {}
    if os.path.exists("move.json"):
        with open("move.json", "r") as move_file:
            move_logs = json.load(move_file)

    move_logs.update({timestamp: move_data})

    with open("move.json", "w") as move_file:
        json.dump(move_logs, move_file, indent=4)

    # Move or copy files based on move.json
    latest_move_data = move_logs.get(timestamp, {})
    for file, file_info in latest_move_data.items():
        prev_dir = file_info["prev_dir"]
        new_dir = file_info["new_dir"]
        file_path = os.path.join(prev_dir, file)
        new_file_path = os.path.join(new_dir, file_info["new_file"])

        if file_path != new_file_path:
            shutil.move(file_path, new_file_path)

    update_main_area()


def update_main_area():
    global main_area  # Access the global main_area variable
    main_area.configure(state="normal")  # Enable editing
    main_area.delete(1.0, tk.END)  # Clear existing content

    move_logs = {}
    if os.path.exists("move.json"):
        with open("move.json", "r") as move_file:
            move_logs = json.load(move_file)

    latest_move_entry = move_logs.get(max(move_logs.keys()), {})

    for file, file_info in latest_move_entry.items():
        prev_dir = file_info["prev_dir"]
        new_dir = file_info["new_dir"]

        prev_location = os.path.join(prev_dir, file)
        new_location = os.path.join(new_dir, file)

        main_area.insert(tk.END, f"Previous Location: {prev_location}\n")
        main_area.insert(tk.END, f"File: {file}\n")
        main_area.insert(tk.END, f"New Location: {new_location}\n")
        # Add a line break between each file entry
        main_area.insert(tk.END, "\n")

    main_area.configure(state="disabled")  # Disable editing


# def create_gui():
#     global main_area  # Declare main_area as a global variable
#     root = tk.Tk()
#     root.geometry("600x400")
#     root.title("Jexi")
#     root.resizable(False, False)  # Make the window unresizable

#     # Create menubar
#     menubar = tk.Menu(root)
#     actions_menu = tk.Menu(menubar, tearoff=0)
#     actions_menu.add_command(label="Move Files", command=lambda: [
#         move_files(get_selected_folders(desktop_var, downloads_var,
#                    documents_var, pictures_var, music_var, videos_var)),
#         update_main_area()
#     ])
#     menubar.add_cascade(label="Actions", menu=actions_menu)
#     menubar.add_command(label="Logs")
#     menubar.add_command(label="Help")
def create_gui():
    global main_area  # Declare main_area as a global variable
    root = tk.Tk()
    root.geometry("600x400")
    root.title("Jexi")
    root.resizable(False, False)  # Make the window unresizable

    # Create menubar
    menubar = tk.Menu(root)

    # Actions menu
    actions_menu = tk.Menu(menubar, tearoff=0)
    actions_menu.add_command(label="Move Files", command=lambda: [
        move_files(get_selected_folders(desktop_var, downloads_var,
                                        documents_var, pictures_var, music_var, videos_var)),
        update_main_area()
    ])
    menubar.add_cascade(label="Actions", menu=actions_menu)

    # View Logs menu
    def view_logs():
        logs_window = tk.Toplevel(root)
        logs_window.title("View Logs")
        logs_window.geometry("400x300")
        logs_text = tk.Text(logs_window, wrap=tk.WORD)
        logs_text.pack(fill="both", expand=True)

        # Read and display logs from move.json
        if os.path.exists("move.json"):
            with open("move.json", "r") as move_file:
                move_logs = json.load(move_file)
                for timestamp, move_data in move_logs.items():
                    logs_text.insert(tk.END, f"Timestamp: {timestamp}\n")
                    for file, file_info in move_data.items():
                        prev_dir = file_info["prev_dir"]
                        new_dir = file_info["new_dir"]
                        prev_location = os.path.join(prev_dir, file)
                        new_location = os.path.join(
                            new_dir, file_info["new_file"])
                        logs_text.insert(
                            tk.END, f"Previous Location: {prev_location}\n")
                        logs_text.insert(tk.END, f"File: {file}\n")
                        logs_text.insert(
                            tk.END, f"New Location: {new_location}\n\n")
                    logs_text.insert(tk.END, "-" * 50 + "\n\n")
        else:
            logs_text.insert(tk.END, "No logs found.\n")

        logs_text.configure(state="disabled")

    menubar.add_command(label="View Logs", command=view_logs)

    # Donate menu
    def donate():
        donate_window = tk.Toplevel(root)
        donate_window.title("Donate")
        donate_window.geometry("300x200")
        donate_label = tk.Label(
            donate_window, text="Thank you for considering a donation!")
        donate_label.pack(pady=50)

    menubar.add_command(label="Donate", command=donate)

    # Extra menu
    extra_menu = tk.Menu(menubar, tearoff=0)
    extra_menu.add_command(label="Extra Menu Item 1")
    extra_menu.add_command(label="Extra Menu Item 2")
    menubar.add_cascade(label="Extra", menu=extra_menu)

    root.config(menu=menubar)

    # Create sidebar
    sidebar_frame = tk.Frame(root, width=200, bg="white")
    sidebar_frame.pack(side="left", fill="y")

    desktop_var = tk.BooleanVar(value=True)
    desktop_checkbox = tk.Checkbutton(
        sidebar_frame, text="Desktop", variable=desktop_var, bg="white")
    desktop_checkbox.grid(row=0, sticky="w")

    downloads_var = tk.BooleanVar(value=True)
    downloads_checkbox = tk.Checkbutton(
        sidebar_frame, text="Downloads", variable=downloads_var, bg="white")
    downloads_checkbox.grid(row=1, sticky="w")

    documents_var = tk.BooleanVar()
    documents_checkbox = tk.Checkbutton(
        sidebar_frame, text="Documents", variable=documents_var, bg="white")
    documents_checkbox.grid(row=2, sticky="w")

    pictures_var = tk.BooleanVar()
    pictures_checkbox = tk.Checkbutton(
        sidebar_frame, text="Pictures", variable=pictures_var, bg="white")
    pictures_checkbox.grid(row=3, sticky="w")

    music_var = tk.BooleanVar()
    music_checkbox = tk.Checkbutton(
        sidebar_frame, text="Music", variable=music_var, bg="white")
    music_checkbox.grid(row=4, sticky="w")

    videos_var = tk.BooleanVar()
    videos_checkbox = tk.Checkbutton(
        sidebar_frame, text="Videos", variable=videos_var, bg="white")
    videos_checkbox.grid(row=5, sticky="w")

    # Create separator
    separator = tk.Frame(root, width=1, bg="gray")
    separator.pack(side="left", fill="y")

    # Create header in the main area
    header_label = tk.Label(root, text="Last Moved",
                            font=("Arial", 16, "bold"))
    header_label.pack(pady=(10, 5))

    # Create main area with vertical scroll
    main_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    main_area.pack(side="left", fill="both", expand=True)

    sort_button = tk.Button(sidebar_frame, text="Sort", command=lambda: [
        move_files(get_selected_folders(desktop_var, downloads_var,
                   documents_var, pictures_var, music_var, videos_var)),
        update_main_area()
    ])

    sort_button.grid(row=6, sticky="nsew", pady=(10, 0), padx=10)

    main_area.configure(state="disabled")  # Make the text uneditable

    root.mainloop()


def get_selected_folders(*vars):
    folders = ["Desktop", "Downloads",
               "Documents", "Pictures", "Music", "Videos"]
    selected_folders = []
    for index, var in enumerate(vars):
        if var.get():
            selected_folders.append(folders[index])
    return selected_folders


if __name__ == "__main__":
    get_folder_config()
    create_gui()
