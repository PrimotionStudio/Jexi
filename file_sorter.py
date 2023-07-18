from tkinter import scrolledtext
import tkinter as tk
import os
import json
import shutil
from datetime import datetime
import itertools
import webbrowser
from PIL import Image, ImageTk


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

    if not os.path.exists("move.json"):
        main_area.configure(state="disabled")  # Disable editing
        return  # No logs to display, return early

    move_logs = {}
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

    def clear_logs():
        main_area.configure(state="normal")
        main_area.delete(1.0, tk.END)
        main_area.configure(state="disabled")

    actions_menu.add_command(label="Clear", command=clear_logs)

    def undo_move():
        move_logs = {}
        if os.path.exists("move.json"):
            with open("move.json", "r") as move_file:
                move_logs = json.load(move_file)

        if move_logs:
            latest_timestamp = max(move_logs.keys())

            latest_move_data = move_logs[latest_timestamp]
            # Create a backup of the latest move data
            backup_move_data = latest_move_data.copy()

            for file, file_info in latest_move_data.items():
                prev_dir = file_info["prev_dir"]
                new_dir = file_info["new_dir"]
                file_path = os.path.join(new_dir, file_info["new_file"])
                prev_file_path = os.path.join(prev_dir, file)
                if os.path.exists(file_path):
                    shutil.move(file_path, prev_file_path)

            # Restore the backup entry to move_logs
            move_logs[latest_timestamp] = backup_move_data

            with open("move.json", "w") as move_file:
                json.dump(move_logs, move_file, indent=4)
            update_main_area()

    actions_menu.add_command(label="Undo Move", command=undo_move)

    def delete_logs():
        if os.path.exists("move.json"):
            update_main_area()  # Update the main area first to avoid ValueError
            os.remove("move.json")
        else:
            clear_logs()  # Clear the main area directly if there are no logs # Check if move_logs is empty after deleting move.json
        if not os.path.exists("move.json"):
            update_main_area()  # Update the main area to show no logs
        if os.path.exists("files.json"):
            update_main_area()  # Update the main area first to avoid ValueError
            os.remove("files.json")
        else:
            clear_logs()  # Clear the main area directly if there are no logs # Check if move_logs is empty after deleting move.json
        if not os.path.exists("files.json"):
            update_main_area()  # Update the main area to show no logs

    actions_menu.add_command(label="Delete Logs", command=delete_logs)

    actions_menu.add_separator()

    actions_menu.add_command(label="Exit", command=root.quit)

    menubar.add_cascade(label="Actions", menu=actions_menu)

    menubar.add_command(label="View Logs", command=lambda: [
        update_main_area(),
        view_logs()
    ])

    def view_logs():
        logs_window = tk.Toplevel(root)
        logs_window.title("View Logs")
        logs_window.geometry("400x300")

        def show_selected_logs():
            selected_date = logs_listbox.get(tk.ACTIVE)
            logs_window.destroy()  # Close the popup window

            # Read and display logs from move.json for the selected date
            if os.path.exists("move.json"):
                with open("move.json", "r") as move_file:
                    move_logs = json.load(move_file)
                    sorted_move_logs = sorted(move_logs.items(
                    ), reverse=True, key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"))
                    found_logs = False  # Flag to check if any logs were found for the selected date
                    for timestamp, move_data in sorted_move_logs:
                        formatted_date = datetime.strptime(
                            timestamp, "%Y-%m-%d %H:%M:%S").strftime("%I:%M:%S %p - %A, %B %Y")
                        if formatted_date == selected_date:
                            found_logs = True
                            # Display the selected logs
                            display_logs(move_data)
                            break  # Stop iterating once the logs for the selected date are found
                    if not found_logs:
                        main_area.configure(state="normal")
                        main_area.delete(1.0, tk.END)
                        main_area.insert(
                            tk.END, "No logs found for selected date.\n")
                        main_area.configure(state="disabled")
            else:
                main_area.configure(state="normal")
                main_area.delete(1.0, tk.END)
                main_area.insert(tk.END, "No logs found.\n")
                main_area.configure(state="disabled")

        logs_listbox = tk.Listbox(logs_window, selectmode=tk.SINGLE)
        logs_listbox.pack(fill="both", expand=True)

        # Read and display dates from move.json
        if os.path.exists("move.json"):
            with open("move.json", "r") as move_file:
                move_logs = json.load(move_file)
                sorted_dates = sorted(move_logs.keys(), reverse=True)
                for timestamp in sorted_dates:
                    formatted_date = datetime.strptime(
                        timestamp, "%Y-%m-%d %H:%M:%S").strftime("%I:%M:%S %p - %A, %B %d, %Y")
                    logs_listbox.insert(tk.END, formatted_date)
        else:
            logs_listbox.insert(tk.END, "No logs found.")

        show_logs_button = tk.Button(
            logs_window, text="Show Logs", command=show_selected_logs)
        show_logs_button.pack(pady=10)

        logs_window.mainloop()

    def list_dates():
        dates = []

        if os.path.exists("move.json"):
            with open("move.json", "r") as move_file:
                move_logs = json.load(move_file)
                dates = list(reversed(move_logs.keys()))

        # Create a new Toplevel window to display the list of dates
        date_window = tk.Toplevel()
        date_window.title("Log Dates")
        date_window.geometry("300x200")

        dates_listbox = tk.Listbox(date_window, selectmode=tk.SINGLE)
        dates_listbox.pack(fill=tk.BOTH, expand=True)

        for date in dates:
            datetime_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            formatted_date = datetime_obj.strftime(
                "%I:%M:%S %p - %A, %B %d, %Y")
            dates_listbox.insert(tk.END, formatted_date)

        def view_logs():
            selected_index = dates_listbox.curselection()
            if selected_index:
                selected_date = dates[selected_index[0]]
                selected_logs = move_logs[selected_date]
                display_logs(selected_logs)

        view_button = tk.Button(
            date_window, text="View Logs", command=view_logs)
        view_button.pack(pady=10)

        date_window.mainloop()

    def display_logs(logs):
        global main_area
        main_area.configure(state="normal")
        main_area.delete(1.0, tk.END)

        # for file, file_info in sorted(logs.items(), reverse=True):
        sorted_logs = sorted(logs.items(), reverse=True, key=lambda x: datetime.strptime(
            x[0], "%Y-%m-%d %H:%M:%S"))  # Sort logs based on datetime
        for file, file_info in sorted_logs:
            prev_dir = file_info["prev_dir"]
            new_dir = file_info["new_dir"]

            prev_location = os.path.join(prev_dir, file)
            new_location = os.path.join(new_dir, file)

            main_area.insert(tk.END, f"Previous Location: {prev_location}\n")
            main_area.insert(tk.END, f"File: {file}\n")
            main_area.insert(tk.END, f"New Location: {new_location}\n")
            main_area.insert(tk.END, "\n")

        main_area.configure(state="disabled")

    # Donate menu

    def donate():
        donate_window = tk.Toplevel(root)
        donate_window.title("Donate")
        donate_window.geometry("300x200")
        donate_label = tk.Label(
            donate_window, text="Thank you for considering a donation!")
        donate_label.pack(pady=50)
        webbrowser.open("https://theprimotionstudio.wordpress.com/")

    menubar.add_command(label="Donate", command=donate)

    # Extra menu
    extra_menu = tk.Menu(menubar, tearoff=0)

    def view_help():
        webbrowser.open(
            "https://github.com/PrimotionStudio/Jexi#jexi---file-organizer")

    extra_menu.add_command(label="View Help", command=view_help)

    def about_app():
        about_window = tk.Toplevel(root)
        about_window.title("About Jexi")
        about_window.geometry("400x400")
        about_window.resizable(False, False)

        logo_path = "primotion-studio.png"  # Replace with the actual image path
        logo_image = Image.open(logo_path)
        logo_image = logo_image.resize((100, 100))  # Adjust the size as needed
        logo_photo = ImageTk.PhotoImage(logo_image)

        # Create the header label
        header_label = tk.Label(
            about_window,
            text="Jexi - File Organizer",
            image=logo_photo,
            compound="left",
            font=("Arial", 15, "bold")
        )
        header_label.pack(pady=(10, 5))
        caption_label = tk.Label(
            about_window,
            text="by Primotion Studio",
            font=("Arial", 10)
        )
        caption_label.pack()
        about_text = tk.Text(about_window, wrap=tk.WORD)
        about_text.pack(fill="both", expand=True)
        about_text.configure(state="normal")

        about_text.insert(
            tk.END,
            "Jexi is a powerful file organizer application that helps you manage and sort your files effortlessly.\n\n"
        )
        about_text.insert(tk.END, "Features:\n")
        about_text.insert(
            tk.END,
            "  - Automatic sorting of files based on predefined folder configurations\n"
        )
        about_text.insert(
            tk.END,
            "  - Ability to customize folder configurations to suit your needs\n"
        )
        about_text.insert(
            tk.END,
            "  - Undo move functionality to revert file operations\n"
        )
        about_text.insert(tk.END, "  - View and manage log history\n")
        about_text.insert(
            tk.END,
            "  - Donate to support the development of Jexi\n"
        )

        about_text.configure(state="disabled")

        # Keep a reference to the logo_photo to prevent it from being garbage collected
        about_window.logo_photo = logo_photo

    extra_menu.add_command(label="About Jexi", command=about_app)

    def show_credits():
        credits_window = tk.Toplevel(root)
        credits_window.title("Credits")
        credits_window.geometry("400x200")
        credits_window.resizable(False, False)

        logo_path = "primotion-studio.png"  # Replace with the actual image path
        logo_image = Image.open(logo_path)
        logo_image = logo_image.resize((70, 70))  # Adjust the size as needed
        logo_photo = ImageTk.PhotoImage(logo_image)

        # Create the header label
        header_label = tk.Label(
            credits_window,
            text="Primotion Studio",
            image=logo_photo,
            compound="left",
            font=("Arial", 15, "bold")
        )
        header_label.pack(pady=(10, 5))

        # Create the credits label
        credits_text = "CEO and Chief Software Engineer: Prime Okanlawon"
        credits_label = tk.Label(
            credits_window,
            text=credits_text,
            font=("Arial", 10)
        )
        credits_label.pack(pady=(10, 5))

        # Keep a reference to the logo_photo to prevent it from being garbage collected
        credits_window.logo_photo = logo_photo

    extra_menu.add_command(label="Credits", command=show_credits)

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
