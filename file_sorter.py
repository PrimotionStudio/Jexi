from tkinter import scrolledtext
import tkinter as tk
import os
import json
import shutil
from datetime import datetime


def get_folder_config():
    folder_config = {}

    if os.path.exists("folder_config.json"):
        with open("folder_config.json", "r") as json_file:
            folder_config = json.load(json_file)
    else:
        folder_config = {
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
                file_info[file] = file_path

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

        for file, file_path in file_info.items():
            _, extension = os.path.splitext(file)
            if extension.startswith("."):
                extension = extension[1:]  # Remove the leading dot

            if extension in extensions:
                new_dir = folder_path
                move_data[file] = {
                    "prev_dir": os.path.dirname(file_path),
                    "file": file,
                    "new_dir": new_dir
                }

    move_logs = {}
    if os.path.exists("move.json"):
        with open("move.json", "r") as move_file:
            move_logs = json.load(move_file)

    move_logs.update({timestamp: move_data})

    with open("move.json", "w") as move_file:
        json.dump(move_logs, move_file, indent=4)

    # Move files based on move.json
    latest_move_data = move_logs.get(timestamp, {})
    for file, file_info in latest_move_data.items():
        prev_dir = file_info["prev_dir"]
        new_dir = file_info["new_dir"]
        file_path = os.path.join(prev_dir, file)
        new_file_path = os.path.join(new_dir, file)
        shutil.move(file_path, new_file_path)


def create_gui():
    root = tk.Tk()
    root.geometry("600x400")
    root.title("Jexi")

    # Create menubar
    menubar = tk.Menu(root)
    actions_menu = tk.Menu(menubar, tearoff=0)
    actions_menu.add_command(label="Move Files", command=lambda: move_files(
        get_selected_folders(downloads_var, documents_var, pictures_var, music_var, videos_var)))
    menubar.add_cascade(label="Actions", menu=actions_menu)
    menubar.add_command(label="Logs")
    menubar.add_command(label="Help")
    root.config(menu=menubar)

    # Create sidebar
    sidebar_frame = tk.Frame(root, width=200, bg="white")
    sidebar_frame.pack(side="left", fill="y")

    downloads_var = tk.BooleanVar(value=True)
    downloads_checkbox = tk.Checkbutton(
        sidebar_frame, text="Downloads", variable=downloads_var, bg="white")
    downloads_checkbox.grid(row=0, sticky="w")

    documents_var = tk.BooleanVar()
    documents_checkbox = tk.Checkbutton(
        sidebar_frame, text="Documents", variable=documents_var, bg="white")
    documents_checkbox.grid(row=1, sticky="w")

    pictures_var = tk.BooleanVar()
    pictures_checkbox = tk.Checkbutton(
        sidebar_frame, text="Pictures", variable=pictures_var, bg="white")
    pictures_checkbox.grid(row=2, sticky="w")

    music_var = tk.BooleanVar()
    music_checkbox = tk.Checkbutton(
        sidebar_frame, text="Music", variable=music_var, bg="white")
    music_checkbox.grid(row=3, sticky="w")

    videos_var = tk.BooleanVar()
    videos_checkbox = tk.Checkbutton(
        sidebar_frame, text="Videos", variable=videos_var, bg="white")
    videos_checkbox.grid(row=4, sticky="w")

    # Create separator
    separator = tk.Frame(root, width=1, bg="gray")
    separator.pack(side="left", fill="y")

    # Create main area with vertical scroll
    main_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    main_area.pack(side="left", fill="both", expand=True)

    sort_button = tk.Button(sidebar_frame, text="Sort", command=lambda: move_files(
        get_selected_folders(downloads_var, documents_var, pictures_var, music_var, videos_var)))

    sort_button.grid(row=5, sticky="nsew", pady=(10, 0), padx=10)

    # Print latest move entry in main area
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

    root.mainloop()


def get_selected_folders(*vars):
    folders = ["Downloads", "Documents", "Pictures", "Music", "Videos"]
    selected_folders = []
    for index, var in enumerate(vars):
        if var.get():
            selected_folders.append(folders[index])
    return selected_folders


if __name__ == "__main__":
    get_folder_config()
    create_gui()
