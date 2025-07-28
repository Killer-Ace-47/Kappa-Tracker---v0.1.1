import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import json
import os
import shutil
import tkinter.messagebox as mb
import sys
import webbrowser
import time
import traceback
import ctypes
from tkinter.messagebox import showinfo

# Copyright © 2025 Killer_Ace_47 Developments

app_ready = False  # Flag to block autosave until app is fully initialized

APP_VERSION = "v0.1.1"
KILLER_DEV_LINK = "https://discord.gg/8r5V3cmSWU"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === SETTINGS ===
DATA_FILE = "player_data.json"
MAX_LEVEL = 100
MIN_LEVEL = 1

# === INIT APP ===
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")
app = ctk.CTk()
app.geometry("720x420")
app.title("Kappa Tracker EFT")

icon_path = resource_path("app_icon.ico")

try:
    app.iconbitmap(icon_path)
except Exception as e:
    print(f"Failed to set iconbitmap: {e}")

# Set taskbar icon on Windows (fixes blue square in taskbar)
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("kappa.tracker.app")
    except Exception as e:
        print(f"Failed to set AppUserModelID: {e}")

# === LOAD IMAGES ===
bear_img = ctk.CTkImage(Image.open(resource_path("Bear.png")), size=(100, 115))
usec_img = ctk.CTkImage(Image.open(resource_path("Usec.png")), size=(100, 115))
eft_logo_img = ctk.CTkImage(Image.open(resource_path("EFT_logo.png")), size=(115, 115))
pve_img = ctk.CTkImage(light_image=Image.open(resource_path("PVE.png")), size=(100, 100))
pvp_img = ctk.CTkImage(light_image=Image.open(resource_path("PVP.png")), size=(100, 100))
info_icon_img = ctk.CTkImage(light_image=Image.open(resource_path("info.png")), size=(32, 32))
lightkeeper_img = ctk.CTkImage(light_image=Image.open(resource_path("lightkeeper.png")), size=(100, 100))

# === TRADER IMAGES ===
trader_images = {
    "Prapor": ctk.CTkImage(Image.open(resource_path("prapor.jpg")), size=(100, 100)),
    "Therapist": ctk.CTkImage(Image.open(resource_path("therapist.jpg")), size=(100, 100)),
    "Skier": ctk.CTkImage(Image.open(resource_path("skier.jpg")), size=(100, 100)),
    "Peacekeeper": ctk.CTkImage(Image.open(resource_path("peacekeeper.jpg")), size=(100, 100)),
    "Mechanic": ctk.CTkImage(Image.open(resource_path("mechanic.jpg")), size=(100, 100)),
    "Ragman": ctk.CTkImage(Image.open(resource_path("ragman.jpg")), size=(100, 100)),
    "Jaeger": ctk.CTkImage(Image.open(resource_path("jaeger.jpg")), size=(100, 100)),
    "Fence": ctk.CTkImage(Image.open(resource_path("fence.png")), size=(100, 100)),
}

# === DATA HANDLING ===

def select_game_mode(mode):
    previous_mode = selected_game_mode.get()
    if previous_mode and previous_mode != mode:
        # Save current mode's data before switching
        data["level"][previous_mode] = level_value.get()
        data["checklist"][previous_mode] = {item: var.get() for item, var in checklist_vars.items()}
        data["quest_checklist"][previous_mode] = {quest: var.get() for quest, var in quest_checklist_vars.items()}
        save_data()  # Save changes for previous mode

    # Switch mode
    selected_game_mode.set(mode)
    data["game_mode"] = mode  # Update saved mode in data

    # Load new mode's level (or default)
    level_data = data.get("level", {})
    if not isinstance(level_data, dict):
        data["level"] = {"PVE": 1, "PVP": 1}
        level_data = data["level"]
    level_value.set(level_data.get(mode, 1))

    # Load checklist state for new mode into UI vars
    checklist_data = data.get("checklist", {}).get(mode, {})
    for item, var in checklist_vars.items():
        var.set(checklist_data.get(item, False))

    # Load quest checklist state for new mode into UI vars
    quest_data = data.get("quest_checklist", {}).get(mode, {})
    for quest, var in quest_checklist_vars.items():
        var.set(quest_data.get(quest, False))

    update_progress_labels()

    build_tracker_screen()
    show_screen(tracker_screen)
    update_welcome_message()
    
def load_data():
    default_data = {
        "level": {"PVE": 1, "PVP": 1},
        "checklist": {"PVE": {}, "PVP": {}},
        "quest_checklist": {"PVE": {}, "PVP": {}},
        "username": "",
        "faction": "",
        "game_mode": ""
    }

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                loaded = json.load(f)

            # Ensure level is a dict
            if not isinstance(loaded.get("level"), dict):
                loaded["level"] = {"PVE": 1, "PVP": 1}

            # Ensure checklist and quest_checklist are structured correctly
            for key in ["checklist", "quest_checklist"]:
                if not isinstance(loaded.get(key), dict):
                    loaded[key] = {"PVE": {}, "PVP": {}}
                else:
                    loaded[key].setdefault("PVE", {})
                    loaded[key].setdefault("PVP", {})

            # Ensure other values are present
            for key in ["username", "faction", "game_mode"]:
                loaded.setdefault(key, "")

            return loaded

        except PermissionError:
            mb.showerror(
                "Load Error",
                f"Permission denied when trying to read from '{DATA_FILE}'.\n\n"
                "Please check that the file is not locked or that you have read permissions."
            )
            return default_data
        except Exception as e:
            mb.showerror(
                "Load Error",
                f"Failed to load data due to an unexpected error:\n{e}"
            )
            return default_data

    return default_data

data = load_data()

def trap_if_level_is_invalid():
    if isinstance(data.get("level"), int):
        #print("[CRITICAL] data['level'] has become an int!")
        #print(f"[VALUE] data['level'] = {data['level']}")
        traceback.print_stack()
        
selected_game_mode = ctk.StringVar(value=data.get("game_mode", ""))
selected_faction = ctk.StringVar(value=data.get("faction", ""))
initial_mode = data.get("game_mode", "")
initial_level = data.get("level", {}).get(initial_mode, 1) if isinstance(data.get("level"), dict) else 1
level_value = ctk.IntVar(value=initial_level)

# === Pagination Settings ===
QUESTS_PER_PAGE = 10
quest_page_index = 0  # Global index for current page in 'All Quests'
page_indicator_label = None

# Vars for checklist and quest checklist states (BooleanVars per item)
checklist_vars = {}
quest_checklist_vars = {}

def save_data():
    try:
        current_mode = selected_game_mode.get()
        if not current_mode:
            return

        # Sync current level from UI to data
        if "level" not in data:
            data["level"] = {"PVE": 1, "PVP": 1}
        data["level"][current_mode] = level_value.get()

        # Sync checklist from UI vars to data
        if "checklist" not in data:
            data["checklist"] = {"PVE": {}, "PVP": {}}
        checklist_state = {item: var.get() for item, var in checklist_vars.items()}
        data["checklist"][current_mode] = checklist_state

        # Sync quest checklist from UI vars to data
        if "quest_checklist" not in data:
            data["quest_checklist"] = {"PVE": {}, "PVP": {}}
        quest_state = {item: var.get() for item, var in quest_checklist_vars.items()}
        data["quest_checklist"][current_mode] = quest_state

        # Compose save object — read username and faction from data dict
        data_to_save = {
            "level": data["level"],
            "checklist": data["checklist"],
            "quest_checklist": data["quest_checklist"],
            "username": data.get("username", ""),
            "faction": data.get("faction", ""),
            "game_mode": current_mode
        }

        with open(DATA_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)

    except PermissionError:
        mb.showerror(
            "Save Error",
            f"Permission denied when trying to save data to '{DATA_FILE}'.\n\n"
            "Please ensure the file is not open in another program and that you have write permissions to the folder."
        )
    except Exception as e:
        mb.showerror("Save Error", f"Failed to save data due to an unexpected error:\n{e}")

def reset_data():
    confirm = mb.askyesno("Reset All Data", "Are you sure you want to wipe all saved data and progress?\nThis cannot be undone.")
    if confirm:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        app.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)

def update_progress_labels():
    try:
        # Kappa progress calculation (unchanged)
        if checklist_vars:
            total = len(checklist_vars)
            done = sum(var.get() for var in checklist_vars.values())
            percent = int(done / total * 100) if total > 0 else 0
            kappa_progress_label.configure(text=f"Progress: {percent}%")
        else:
            kappa_progress_label.configure(text="Progress: 0%")

        # Quest progress calculation (use UI vars, not saved data)
        if quest_checklist_vars:
            total = len(quest_checklist_vars)
            done = sum(var.get() for var in quest_checklist_vars.values())
            percent = int(done / total * 100) if total > 0 else 0
            quest_progress_label.configure(text=f"Progress: {percent}%")
        else:
            quest_progress_label.configure(text="Progress: 0%")

    except NameError:
        pass

# === SCREENS ===
faction_screen = ctk.CTkFrame(app, fg_color="transparent")
tracker_screen = ctk.CTkFrame(app, fg_color="transparent")
checklist_screen = ctk.CTkFrame(app, fg_color="transparent")
quest_checklist_screen = ctk.CTkFrame(app, fg_color="transparent")
all_quests_screen = ctk.CTkFrame(app, fg_color="transparent")
game_mode_screen = ctk.CTkFrame(app, fg_color="transparent")
about_screen = ctk.CTkFrame(app, fg_color="transparent")

# === FUNCTIONS ===

def confirm_and_open_url(url, title="Open Link", message="This will open a web page in your browser. Do you want to continue?"):
    def on_yes():
        dialog.destroy()
        webbrowser.open(url)

    def on_no():
        dialog.destroy()

    dialog = ctk.CTkToplevel()
    dialog.title(title)
    dialog.geometry("400x120")
    dialog.resizable(False, False)
    dialog.grab_set()  # Makes this window modal (disables main window until closed)

    label = ctk.CTkLabel(dialog, text=message, wraplength=380, justify="center", font=("Arial", 14))
    label.pack(pady=(20, 10), padx=10)

    button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    button_frame.pack(pady=10)

    yes_btn = ctk.CTkButton(button_frame, text="Yes", command=on_yes, width=80)
    yes_btn.pack(side="left", padx=10)

    no_btn = ctk.CTkButton(button_frame, text="No", command=on_no, width=80)
    no_btn.pack(side="left", padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_no) 

def open_kofi():
    confirm_and_open_url(
        "https://ko-fi.com/killer_ace_47",
        title="Open Ko-fi",
        message="This will open the developers Ko-fi page in your web browser.\nDo you want to continue?"
    )
    
def create_donate_button(parent, command=None, button_size=100, image_size=(100, 100),
                         top_font_size=14, bottom_font_size=10, **place_kwargs):
    container = ctk.CTkFrame(parent, fg_color="transparent")

    top_label = ctk.CTkLabel(container, text="Support the Devs", font=("Arial", top_font_size))
    top_label.pack(pady=(0, 0))

    img = Image.open(resource_path("Bitcoin.png"))
    resized_img = ctk.CTkImage(light_image=img, size=image_size)

    btn = ctk.CTkButton(
        container,
        text="",
        image=resized_img,
        width=button_size,
        height=button_size,
        corner_radius=6,           
        fg_color="transparent",
        hover_color="#2a2a2a",
        border_width=0,
        command=command if command else open_kofi
    )
    btn.pack(padx=0, pady=0)

    bottom_label = ctk.CTkLabel(container, text="*Not actual bitcoin", font=("Arial", bottom_font_size), text_color="gray")
    bottom_label.pack(pady=(0, 0))

    if "place" in place_kwargs:
        container.place(**place_kwargs["place"])
    elif "pack" in place_kwargs:
        container.pack(**place_kwargs["pack"])
    elif "grid" in place_kwargs:
        container.grid(**place_kwargs["grid"])
    else:
        container.pack()

    return container

def update_data_level_from_vars():
    # Just ensure the level for the current mode is updated from the UI
    current_mode = selected_game_mode.get()
    if not current_mode:
        return
    if "level" not in data:
        data["level"] = {"PVE": 1, "PVP": 1}
    data["level"][current_mode] = level_value.get()

def update_data_quest_checklist_from_vars():
    current_mode = selected_game_mode.get()
    if not current_mode:
        return
    quest_state = {quest: var.get() for quest, var in quest_checklist_vars.items()}
    data.setdefault("quest_checklist", {})
    data["quest_checklist"][current_mode] = quest_state

def update_data_checklist_from_vars():
    current_mode = selected_game_mode.get()
    if not current_mode:
        return
    checklist_state = {item: var.get() for item, var in checklist_vars.items()}
    data.setdefault("checklist", {})
    data["checklist"][current_mode] = checklist_state

def open_about_screen_from(source_screen):
    global last_screen
    last_screen = source_screen
    build_about_screen()
    show_screen(about_screen)

def update_data_from_ui():
    # Only update username if entry exists and is visible
    if 'username_entry' in globals() and username_entry.winfo_exists():
        data["username"] = username_entry.get().strip()

    data["faction"] = selected_faction.get()
    data["game_mode"] = selected_game_mode.get()

def save_quest_checklist_state():
    current_mode = selected_game_mode.get()
    if current_mode:
        data.setdefault("quest_checklist", {})[current_mode] = {
            quest: var.get() for quest, var in quest_checklist_vars.items()
        }

def prepare_faction_screen():
    # Set the selected faction to the saved one (or empty if none)
    selected_faction.set(data.get("faction", ""))

    # Update the welcome text label based on faction
    faction = selected_faction.get()
    label.configure(text=f"Welcome, {'my BEAR brother' if faction == 'BEAR' else 'you filthy USEC'}!")

    # Update the faction logo image
    update_faction_logo()

    # Enable or disable the proceed button depending on if username & faction are set
    check_ready_to_proceed()

def load_rounded_image(path, size=(100, 100), radius=20):
    img = Image.open(path).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)

    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)

    img.putalpha(mask)

    # Instead of returning PhotoImage, return CTkImage wrapping PIL Image
    return ctk.CTkImage(img, size=size)
    
killer_dev_img = load_rounded_image(resource_path("Killer_Dev.png"), size=(100, 100), radius=20)

def sync_quest_vars_from_data():
    current_mode = selected_game_mode.get()
    if not current_mode:
        return

    saved_state = data.get("quest_checklist", {}).get(current_mode, {})
    for quest in quest_checklist_vars:
        quest_checklist_vars[quest].set(saved_state.get(quest, False))

def add_footer(parent_frame):
    footer_label = ctk.CTkLabel(
        parent_frame,
        text=f"Version {APP_VERSION} © 2025 Kappa Tracker by Killer_Ace_47 Developments",
        font=("Arial", 10),
        anchor="center",
        fg_color="transparent",
        text_color="gray"
    )
    footer_label.place(relx=0.5, rely=1.0, anchor="s", y=-5)
    
def show_screen(screen):
    for s in (faction_screen, tracker_screen, checklist_screen, quest_checklist_screen, all_quests_screen, game_mode_screen, about_screen):
        s.place_forget()
    screen.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

def switch_and_save(target):
    save_data()
    if callable(target):
        target()  # build the screen
        # Show the appropriate screen based on which builder function was called
        if target == build_tracker_screen:
            show_screen(tracker_screen)
        elif target == build_game_mode_screen:
            show_screen(game_mode_screen)
        elif target == build_about_screen:
            show_screen(about_screen)
        elif target == build_faction_screen:
            show_screen(faction_screen)
        # Add other mappings here as you add more screens
    else:
        show_screen(target)

def update_checklist_vars():
    current_mode = selected_game_mode.get()
    if not current_mode:
        return

    saved_state = data.get("checklist", {}).get(current_mode, {})
    #print(f"[DEBUG] update_checklist_vars() for {current_mode}: {saved_state}")
    for item, var in checklist_vars.items():
        var.set(saved_state.get(item, False))

def update_quest_checklist_vars():
    current_mode = selected_game_mode.get()
    if not current_mode:
        return

    saved_state = data.get("quest_checklist", {}).get(current_mode, {})
    for quest, var in quest_checklist_vars.items():
        var.set(saved_state.get(quest, False))

def change_quest_page(delta):
    global quest_page_index
    quest_page_index += delta
    load_quest_checklist_vars()  # Reload all quests view

# === FACTION SELECTION SCREEN ===

def button_click(faction):
    selected_faction.set(faction)
    label.configure(text=f"Welcome, {'my BEAR brother' if faction == 'BEAR' else 'you filthy USEC'}!")
    check_ready_to_proceed()

def check_ready_to_proceed(*args):
    if username_entry.get().strip() and selected_faction.get():
        proceed_button.configure(state="normal")
    else:
        proceed_button.configure(state="disabled")

def update_faction_logo():
    faction = selected_faction.get()
    if faction == "BEAR":
        faction_logo_label.configure(image=bear_img)
    elif faction == "USEC":
        faction_logo_label.configure(image=usec_img)

def update_welcome_message():
    global welcome_message_label
    try:
        welcome_message_label.configure(text=f"Welcome back to the {selected_game_mode.get().upper()} Kappa tracker")
    except NameError:
        pass  # label not created yet, do nothing

def proceed():
    old_faction = data.get("faction", "")
    new_faction = selected_faction.get()

    # Save username always
    data["username"] = username_entry.get().strip()

    # If faction changed, reset game mode
    if new_faction != old_faction:
        data["faction"] = new_faction
        selected_game_mode.set("")  # Reset game mode selection in UI state
        data["game_mode"] = ""      # Reset saved game mode in data
    else:
        # Faction not changed, keep previous game mode in data
        data["faction"] = new_faction

    update_data_from_ui()
    save_data()

    # ✅ Always go to game mode screen next
    switch_and_save(build_game_mode_screen)

def build_faction_screen():
    global label, username_entry, proceed_button

    #print("Building faction screen...")

    # Clear previous contents
    for widget in faction_screen.winfo_children():
        widget.destroy()

    # Title label
    label = ctk.CTkLabel(faction_screen, text="Choose your faction!", font=("Arial", 32), fg_color="transparent")
    label.pack(pady=(20, 10))

    # Faction image + button frame (only place where images appear now)
    button_frame = ctk.CTkFrame(faction_screen, fg_color="transparent")
    button_frame.pack(pady=(10, 5))

    bear_image_label = ctk.CTkLabel(button_frame, image=bear_img, text="", fg_color="transparent", cursor="hand2")
    bear_image_label.grid(row=0, column=0, padx=10)
    bear_image_label.bind("<Button-1>", lambda e: button_click("BEAR"))

    usec_image_label = ctk.CTkLabel(button_frame, image=usec_img, text="", fg_color="transparent", cursor="hand2")
    usec_image_label.grid(row=0, column=1, padx=10)
    usec_image_label.bind("<Button-1>", lambda e: button_click("USEC"))

    button1 = ctk.CTkButton(button_frame, text="BEAR", command=lambda: button_click("BEAR"))
    button1.grid(row=1, column=0, padx=10, pady=(5, 0))

    button2 = ctk.CTkButton(button_frame, text="USEC", command=lambda: button_click("USEC"))
    button2.grid(row=1, column=1, padx=10, pady=(5, 0))

    # Username entry
    username_entry = ctk.CTkEntry(faction_screen, placeholder_text="Enter your username")
    username_entry.pack(pady=(40, 10))
    saved_username = data.get("username", "")
    if saved_username:
        username_entry.insert(0, saved_username)
    username_entry.bind("<KeyRelease>", check_ready_to_proceed)

    # Proceed button
    proceed_button = ctk.CTkButton(faction_screen, text="Proceed", state="disabled", command=proceed)
    proceed_button.pack(pady=(30, 5))

    # --- Info Button (Bottom Left) ---

    info_button = ctk.CTkButton(
        faction_screen,
        image=info_icon_img,
        text="",
        width=36,
        height=36,
        fg_color="transparent",
        hover_color="gray30",
        command=lambda: open_about_screen_from(faction_screen)
    )
    info_button.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)

    # Prevent garbage collection
    faction_screen.info_icon_img = info_icon_img
    
    # Add donate button container above the info button on left side
    donate_btn_container = create_donate_button(
        faction_screen,
        button_size=105,        # updated param name
        image_size=(100, 100),
        place={"relx": 0.0, "rely": 1.0, "anchor": "sw", "x": 20, "y": -70}  # 50 px above info button at y=-20
    )
    faction_screen.donate_btn_container = donate_btn_container  # keep a reference to avoid garbage collection

    # --- Killer Dev Button ---
    killer_dev_img = load_rounded_image(resource_path("Killer_Dev.png"), size=(100, 100), radius=20)

    def open_link():
        confirm_and_open_url(KILLER_DEV_LINK, "Open Discord Link", "This will open the Killer_Ace_47 Developments Discord link in your browser. Continue?")

    killer_button = ctk.CTkButton(
        faction_screen,
        image=killer_dev_img,
        text="",
        width=100,
        height=100,
        fg_color="transparent",
        hover_color="gray30",
        command=open_link
    )
    killer_button.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    # Prevent garbage collection
    faction_screen.killer_dev_img = killer_dev_img

    # Footer
    add_footer(faction_screen)

    # Re-evaluate proceed button if returning with data filled
    check_ready_to_proceed()

# === GAME MODE SCREEN ===

def proceed_game_mode():
    update_data_from_ui()
    save_data()
    update_welcome_message()
    switch_and_save(build_tracker_screen)

def build_game_mode_screen():
    #print("Building game mode screen...")  # <-- Add this to debug
    # Clear existing widgets
    for widget in game_mode_screen.winfo_children():
        widget.destroy()

    # Game Mode label
    game_mode_label = ctk.CTkLabel(game_mode_screen, text="Select Game Mode", font=("Arial", 28), fg_color="transparent")
    game_mode_label.pack(pady=20)

    # Frame to hold buttons horizontally
    buttons_frame = ctk.CTkFrame(game_mode_screen, fg_color="transparent")
    buttons_frame.pack(pady=10)

    pve_button = ctk.CTkButton(
        buttons_frame,
        text="PVE",
        image=pve_img,
        compound="top",  # Image above text
        command=lambda: select_game_mode("PVE"),
        width=120,
        height=140
    )
    pve_button.pack(side="left", padx=20)

    pvp_button = ctk.CTkButton(
        buttons_frame,
        text="PVP",
        image=pvp_img,
        compound="top",  # Image above text
        command=lambda: select_game_mode("PVP"),
        width=120,
        height=140
    )
    pvp_button.pack(side="left", padx=20)

    # Back to faction button
    back_to_faction_button = ctk.CTkButton(
        game_mode_screen,
        text="← Back",
        command=lambda: switch_and_save(build_faction_screen)
    )
    back_to_faction_button.pack(pady=(40, 5))

    # Reset data button
    reset_button = ctk.CTkButton(
        game_mode_screen,
        text="Reset All Data",
        fg_color="red",
        command=reset_data
    )
    reset_button.pack(pady=(40, 10))

    # Killer Dev image button
    def open_link():
        confirm_and_open_url(KILLER_DEV_LINK, "Open Discord Link", "This will open the Killer_Ace_47 Developments Discord link in your browser. Continue?")

    # Load the image here or ensure it’s loaded globally before calling this function
    # If not loaded globally, uncomment and adjust path:
    # killer_dev_img = load_rounded_image("Killer_Dev.png", size=(100, 100), radius=20)

    my_link_button = ctk.CTkButton(
        game_mode_screen,
        image=killer_dev_img,
        text="",
        width=100,
        height=100,
        fg_color="transparent",
        hover_color="gray30",
        command=open_link
    )
    my_link_button.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
    game_mode_screen.my_link_img = killer_dev_img  # keep ref

    # Add donate button container above the info button on left side
    donate_btn_container = create_donate_button(
        game_mode_screen,
        button_size=105,        # updated param name
        image_size=(100, 100),
        place={"relx": 0.0, "rely": 1.0, "anchor": "sw", "x": 20, "y": -70}  # 50 px above info button at y=-20
    )
    game_mode_screen.donate_btn_container = donate_btn_container  # keep a reference to avoid garbage collection

    # Info button
    info_button = ctk.CTkButton(
        game_mode_screen,
        image=info_icon_img,
        text="",  # No text, just the icon
        width=36,
        height=36,
        fg_color="transparent",
        hover_color="gray30",
        command=lambda: open_about_screen_from(game_mode_screen)
    )
    info_button.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
    game_mode_screen.info_icon_img = info_icon_img  # keep ref

    # Add footer (assuming add_footer is a function you use elsewhere)
    add_footer(game_mode_screen)

# === ABOUT / CREDITS SCREEN ===

def build_about_screen():
    for widget in about_screen.winfo_children():
        widget.destroy()

    title = ctk.CTkLabel(about_screen, text="About This App", font=("Arial", 24, "bold"))
    title.pack(pady=(20, 10))

    description = """This is a fan-made companion app for Escape From Tarkov.

It helps you track quests and Kappa progress in both PVE and PVP modes.

• Trader images and other in-game assets are © Battlestate Games. Used here for informational purposes only. This app is an unofficial fan tool and is not affiliated with or endorsed by Battlestate Games.
• Some images were generated using AI for illustrative purposes only.
• Thanks to ChatGPT, the Escape From Tarkov Wiki and the community for reference material."""

    desc_label = ctk.CTkLabel(about_screen, text=description, font=("Arial", 14), justify="left", wraplength=500)
    desc_label.pack(pady=(0, 20), padx=20)

    # Placeholder for future supporters section
    supporters_title = ctk.CTkLabel(about_screen, text="Supporters", font=("Arial", 18, "bold"))
    supporters_title.pack(pady=(10, 5))

    supporters_label = ctk.CTkLabel(about_screen, text="Coming soon!", font=("Arial", 14))
    supporters_label.pack(pady=(0, 20))

    # Back button to return to the last screen (or game mode screen if none saved)
    back_button = ctk.CTkButton(
        about_screen,
        text="← Back",
        command=lambda: switch_and_save(last_screen if last_screen else build_game_mode_screen)
    )
    back_button.pack(pady=(0, 20))

    add_footer(about_screen)

# === TRACKER SCREEN ===

def build_tracker_screen():
    global down_button, up_button, level_entry
    global quest_progress_label, kappa_progress_label
    global faction_logo_label, eft_logo_label
    global welcome_message_label

    for widget in tracker_screen.winfo_children():
        widget.destroy()

    def update_level_buttons():
        current = level_value.get()
        down_button.configure(state="normal" if current > MIN_LEVEL else "disabled")
        up_button.configure(state="normal" if current < MAX_LEVEL else "disabled")

    def increase_level():
        validate_and_set_level()
        if level_value.get() < MAX_LEVEL:
            level_value.set(level_value.get() + 1)
            level_entry.delete(0, "end")
            level_entry.insert(0, str(level_value.get()))
            update_level_buttons()
            save_data()

    def decrease_level():
        validate_and_set_level()
        if level_value.get() > MIN_LEVEL:
            level_value.set(level_value.get() - 1)
            level_entry.delete(0, "end")
            level_entry.insert(0, str(level_value.get()))
            update_level_buttons()
            save_data()

    def validate_and_set_level(event=None):
        try:
            entered = int(level_entry.get())
            if MIN_LEVEL <= entered <= MAX_LEVEL:
                level_value.set(entered)
                update_level_buttons()
                save_data()
            else:
                raise ValueError
        except ValueError:
            level_entry.delete(0, "end")
            level_entry.insert(0, str(level_value.get()))
        tracker_screen.focus_set()

    # ✅ Dynamic welcome message
    mode = selected_game_mode.get().upper()
    welcome_text = f"Welcome back to the {mode} Kappa tracker" if mode else "Welcome back to the Kappa tracker"
    welcome_message_label = ctk.CTkLabel(
        tracker_screen,
        text=welcome_text,
        font=("Arial", 30),
        fg_color="transparent"
    )
    welcome_message_label.pack(pady=(10, 5))

    username_display_label = ctk.CTkLabel(
        tracker_screen,
        text=f"{data.get('username', '')}",
        font=("Arial", 24),
        fg_color="transparent"
    )
    username_display_label.pack(pady=(15, 10))

    level_label = ctk.CTkLabel(tracker_screen, text="Player Level:", font=("Arial", 18))
    level_label.pack(pady=(15))

    spinner_frame = ctk.CTkFrame(tracker_screen, fg_color="transparent")
    spinner_frame.pack()

    down_button = ctk.CTkButton(spinner_frame, text="▼", width=40, command=decrease_level)
    down_button.grid(row=0, column=0, padx=5, pady=10)

    level_entry = ctk.CTkEntry(spinner_frame, width=80, justify="center", font=("Arial", 18))
    level_entry.grid(row=0, column=1, padx=5, pady=10)
    level_entry.insert(0, str(level_value.get()))
    level_entry.bind("<Return>", validate_and_set_level)
    level_entry.bind("<FocusOut>", validate_and_set_level)

    up_button = ctk.CTkButton(spinner_frame, text="▲", width=40, command=increase_level)
    up_button.grid(row=0, column=2, padx=5, pady=10)

    update_level_buttons()

    add_footer(tracker_screen)

    tracker_footer = ctk.CTkLabel(
        tracker_screen,
        text="Go back to the game mode screen if you wish to change mode or reset data",
        font=("Arial", 12),
        anchor="center",
        fg_color="transparent"
    )
    tracker_footer.pack(side="bottom", fill="x", pady=(0, 25))

    quest_checklist_frame = ctk.CTkFrame(tracker_screen, fg_color="transparent")
    quest_checklist_frame.pack(pady=20, fill="x", padx=20)

    buttons_progress_frame = ctk.CTkFrame(quest_checklist_frame, fg_color="transparent")
    buttons_progress_frame.pack()

    def open_checklist():
        update_data_checklist_from_vars()
        load_checklist_vars()
        show_screen(checklist_screen)

    def open_quest_checklist():
        load_quest_checklist_vars()
        show_screen(quest_checklist_screen)

    quest_list_button = ctk.CTkButton(buttons_progress_frame, text="Quest Checklist", command=open_quest_checklist_selector)
    quest_list_button.grid(row=0, column=0, padx=40, pady=(0, 5))

    checklist_button = ctk.CTkButton(buttons_progress_frame, text="Kappa Items Checklist", command=open_checklist)
    checklist_button.grid(row=0, column=1, padx=40, pady=(0, 5))

    quest_progress_label = ctk.CTkLabel(buttons_progress_frame, text="Progress: 0%", font=("Arial", 14))
    quest_progress_label.grid(row=1, column=0, pady=(0, 0))

    kappa_progress_label = ctk.CTkLabel(buttons_progress_frame, text="Progress: 0%", font=("Arial", 14))
    kappa_progress_label.grid(row=1, column=1, pady=(0, 0))

    back_button = ctk.CTkButton(tracker_screen, text="← Back", command=lambda: switch_and_save(build_game_mode_screen))
    back_button.pack(pady=(10, 10))

    faction_img = bear_img if data.get("faction") == "BEAR" else usec_img
    faction_logo_label = ctk.CTkLabel(tracker_screen, image=faction_img, fg_color="transparent", text="")
    faction_logo_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    # Add donate button container
    donate_btn_container = create_donate_button(
        tracker_screen,
        button_size=65,  # smaller than before for subtlety
        image_size=(60, 60),
        top_font_size=10,
        bottom_font_size=10,
        place={"relx": 0.0, "rely": 1.0, "anchor": "sw", "x": 20, "y": -130}
    )
    tracker_screen.donate_btn_container = donate_btn_container
    
    lightkeeper_button = ctk.CTkButton(
        tracker_screen,
        text="Coming Soon",
        image=lightkeeper_img,
        compound="top",
        width=120,
        height=120,
        font=("Arial", 14),
        fg_color="#2a2a2a",
        hover_color="gray",
        command=lambda: showinfo("Coming Soon", "Lightkeeper tracking is currently in development!")
    )
    lightkeeper_button.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-210)

    eft_logo_label = ctk.CTkLabel(tracker_screen, image=eft_logo_img, fg_color="transparent", text="")
    eft_logo_label.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=-10)

    load_checklist_vars()
    sync_quest_vars_from_data()
    update_progress_labels()

# === KAPPA CHECKLIST SCREEN ===
kappa_items_with_links = {
    "Old firesteel": "https://escapefromtarkov.fandom.com/wiki/Old_firesteel",
    "Antique axe": "https://escapefromtarkov.fandom.com/wiki/Antique_axe",
    "Battered antique book": "https://escapefromtarkov.fandom.com/wiki/Battered_antique_book",
    "#FireKlean gun lube": "https://escapefromtarkov.fandom.com/wiki/FireKlean_gun_lube",
    "Golden rooster figurine in raid": "https://escapefromtarkov.fandom.com/wiki/Golden_rooster",
    "Silver Badge in raid": "https://escapefromtarkov.fandom.com/wiki/Silver_Badge",
    "Deadlyslob's beard oil": "https://escapefromtarkov.fandom.com/wiki/Deadlyslob%27s_beard_oil",
    "Golden 1GPhone smartphone": "https://escapefromtarkov.fandom.com/wiki/1GPhone",
    "Jar of DevilDog mayo": "https://escapefromtarkov.fandom.com/wiki/DevilDog_mayo",
    "Can of sprats": "https://escapefromtarkov.fandom.com/wiki/Can_of_sprats",
    "Fake mustache": "https://escapefromtarkov.fandom.com/wiki/Fake_mustache",
    "Kotton beanie": "https://escapefromtarkov.fandom.com/wiki/Kotton_beanie",
    "Raven figurine": "https://escapefromtarkov.fandom.com/wiki/Raven_figurine",
    "Pestily plague mask": "https://escapefromtarkov.fandom.com/wiki/Pestily_plague_mask",
    "Shroud half-mask": "https://escapefromtarkov.fandom.com/wiki/Shroud_half-mask",
    "Can of Dr. Lupo's coffee beans": "https://escapefromtarkov.fandom.com/wiki/Dr._Lupo%27s_coffee_beans",
    "42 Signature Blend English Tea": "https://escapefromtarkov.fandom.com/wiki/42_Signature_Blend_English_Tea",
    "Veritas guitar pick": "https://escapefromtarkov.fandom.com/wiki/Veritas_guitar_pick",
    "Armband (Evasion)": "https://escapefromtarkov.fandom.com/wiki/Evasion_Armband",
    "Can of RatCola soda": "https://escapefromtarkov.fandom.com/wiki/RatCola",
    "Loot Lord plushie": "https://escapefromtarkov.fandom.com/wiki/Loot_Lord_plushie",
    "WZ Wallet": "https://escapefromtarkov.fandom.com/wiki/WZ_Wallet",
    "LVNDMARK's rat poison": "https://escapefromtarkov.fandom.com/wiki/LVNDMARK%27s_rat_poison",
    "Smoke balaclava": "https://escapefromtarkov.fandom.com/wiki/Smoke_balaclava",
    "Missam forklift key": "https://escapefromtarkov.fandom.com/wiki/Missam_forklift_key",
    "Video cassette with the Cyborg Killer movie": "https://escapefromtarkov.fandom.com/wiki/Video_cassette_with_the_Cyborg_Killer_movie",
    "BakeEzy cook book": "https://escapefromtarkov.fandom.com/wiki/BakeEzy_cook_book",
    "JohnB Liquid DNB glasses": "https://escapefromtarkov.fandom.com/wiki/JohnB_Liquid_DNB_glasses",
    "Glorious E lightweight armored mask": "https://escapefromtarkov.fandom.com/wiki/Glorious_E_lightweight_armored_mask",
    "Baddie's red beard": "https://escapefromtarkov.fandom.com/wiki/Baddie%27s_red_beard",
    "DRD body armor": "https://escapefromtarkov.fandom.com/wiki/DRD_body_armor",
    "Gingy keychain": "https://escapefromtarkov.fandom.com/wiki/Gingy_keychain",
    "Golden egg": "https://escapefromtarkov.fandom.com/wiki/Golden_egg",
    "Press pass (issued for NoiceGuy)": "https://escapefromtarkov.fandom.com/wiki/Press_pass_(issued_for_NoiceGuy)",
    "Axel parrot figurine": "https://escapefromtarkov.fandom.com/wiki/Axel_parrot_figurine",
    "BEAR Buddy plush toy": "https://escapefromtarkov.fandom.com/wiki/BEAR_Buddy_plush_toy",
    "Inseq gas pipe wrench": "https://escapefromtarkov.fandom.com/wiki/Inseq_gas_pipe_wrench",
    "Viibiin sneaker": "https://escapefromtarkov.fandom.com/wiki/Viibiin_sneaker",
    "Tamatthi kunai knife replica": "https://escapefromtarkov.fandom.com/wiki/Tamatthi_kunai_knife_replica",
}

def open_info_link(url):
    confirm_and_open_url(
        url,
        title="Open Wiki Page",
        message="This will open the Escape from Tarkov Wiki page in your browser.\nDo you want to continue?"
    )
# === QUEST CHECKLIST SCREEN ===

trader_quests = {
    "Prapor": [
        "Shooting Cans",
        "Debut",
        "Luxurious Life",
        "Search Mission",
        "Background Check",
        "Shootout Picnic",
        "Delivery From the Past",
        "BP Depot",
        "Bad Rep Evidence",
        "Ice Cream Cones",
        "Postman Pat - Part 1",
        "Shaking Up the Teller",
        "The Punisher - Part 1",
        "The Punisher - Part 2",
        "The Punisher - Part 3",
        "The Punisher - Part 4",
        "The Punisher - Part 5",
        "The Punisher - Part 6",
        "Polikhim Hobo",
        "Big Customer",
        "Grenadier",
        "Perfect Mediator",
        "Test Drive - Part 1",
        "Test Drive - Part 2",
        "Test Drive - Part 3",
        "Test Drive - Part 4",
        "Test Drive - Part 5",
        "Test Drive - Part 6",
        "Regulated Materials",
        "The Bunker - Part 1",
        "The Bunker - Part 2",
        "Anesthesia",
        "Documents",
        "No Place for Renegades",
        "Intimidator",
        "Easy Job - Part 1",
        "Easy Job - Part 2",
        "Reconnaissance",
        "Possessor",
        "Belka and Strelka"
    ],
    "Therapist": [
        "First in Line",
        "Shortage",
        "Sanitary Standards - Part 1",
        "Sanitary Standards - Part 2",
        "Operation Aquarius - Part 1",
        "Operation Aquarius - Part 2",
        "Painkiller",
        "Pharmacist",
        "Supply Plans",
        "General Wares",
        "Car Repair",
        "Health Care Privacy - Part 1",
        "Health Care Privacy - Part 2",
        "Health Care Privacy - Part 3",
        "Health Care Privacy - Part 4",
        "Health Care Privacy - Part 5",
        "Health Care Privacy - Part 6",
        "Postman Pat - Part 2",
        "Out of Curiosity",
        "Athlete",
        "Decontamination Service",
        "Private Clinic",
        "An Apple a Day Keeps the Doctor Away",
        "Colleagues - Part 1",
        "Colleagues - Part 2",
        "Colleagues - Part 3",
        "Disease History",
        "Crisis",
        "Seaside Vacation",
        "Lost Contact",
        "Drug Trafficking",
        "All Is Revealed",
        "A Healthy Alternative",
        "Shipment Tracking",
        "Closer to the People",
        "Abandoned Cargo"
    ],
    "Skier": [
        "Burning Rubber",
        "Supplier",
        "The Extortionist",
        "Stirrup",
        "What’s on the Flash Drive?",
        "Golden Swag",
        "Chemical - Part 1",
        "Chemical - Part 2",
        "Chemical - Part 3",
        "Chemical - Part 4",
        "Loyalty Buyout",
        "Friend From the West - Part 1",
        "Friend From the West - Part 2",
        "Vitamins - Part 1",
        "Vitamins - Part 2",
        "Lend-Lease - Part 1",
        "Informed Means Armed",
        "Chumming",
        "Kind of Sabotage",
        "Setup",
        "Flint",
        "Rigged Game",
        "Safe Corridor",
        "Long Road",
        "Missing Cargo",
        "The Walls Have Eyes",
        "Exit Here",
        "Private Club"
    ],
    "Peacekeeper": [
        "Fishing Gear",
        "Tigr Safari",
        "Scrap Metal",
        "Eagle Eye",
        "Humanitarian Supplies",
        "The Cult - Part 1",
        "The Cult - Part 2",
        "Spa Tour - Part 1",
        "Spa Tour - Part 2",
        "Spa Tour - Part 3",
        "Spa Tour - Part 4",
        "Spa Tour - Part 5",
        "Spa Tour - Part 6",
        "Spa Tour - Part 7",
        "Cargo X - Part 1",
        "Cargo X - Part 2",
        "Cargo X - Part 3",
        "Wet Job - Part 1",
        "Wet Job - Part 2",
        "Wet Job - Part 3",
        "Wet Job - Part 4",
        "Wet Job - Part 5",
        "Wet Job - Part 6",
        "The Guide",
        "Peacekeeping Mission",
        "Lend-Lease - Part 2",
        "Samples",
        "TerraGroup Employee",
        "Revision - Reserve",
        "Revision - Lighthouse",
        "Classified Technologies",
        "Cargo X - Part 4",
        "Insomnia",
        "Overpopulation",
        "One Less Loose End"
    ],
    "Mechanic": [
        "Saving the Mole",
        "Gunsmith - Part 1",
        "Gunsmith - Part 2",
        "Gunsmith - Part 3",
        "Gunsmith - Part 4",
        "Gunsmith - Part 5",
        "Gunsmith - Part 6",
        "Gunsmith - Part 7",
        "Gunsmith - Part 8",
        "Gunsmith - Part 9",
        "Gunsmith - Part 10",
        "Gunsmith - Part 11",
        "Gunsmith - Part 12",
        "Gunsmith - Part 13",
        "Gunsmith - Part 14",
        "Gunsmith - Part 15",
        "Gunsmith - Part 16",
        "Gunsmith - Part 17",
        "Gunsmith - Part 18",
        "Gunsmith - Part 19",
        "Gunsmith - Part 20",
        "Gunsmith - Part 21",
        "Gunsmith - Part 22",
        "Farming - Part 1",
        "Farming - Part 2",
        "Farming - Part 3",
        "Farming - Part 4",
        "Signal - Part 1",
        "Signal - Part 2",
        "Signal - Part 3",
        "Signal - Part 4",
        "Bad Habit",
        "Scout",
        "Insider",
        "Import",
        "Fertilizers",
        "Psycho Sniper",
        "A Shooter Born in Heaven",
        "Introduction",
        "Chemistry Closet",
        "Surplus Goods",
        "Back Door",
        "Corporate Secrets",
        "Energy Crisis",
        "Broadcast - Part 1",
        "Capacity Check",
        "Black Swan",
        "Forklift Certified",
        "Passion for Ergonomics"
    ],
    "Ragman": [
        "Only Business",
        "Make ULTRA Great Again",
        "Big Sale",
        "The Blood of War - Part 1",
        "The Blood of War - Part 2",
        "The Blood of War - Part 3",
        "Dressed to Kill",
        "Gratitude",
        "Sales Night",
        "Hot Delivery",
        "Database - Part 1",
        "Database - Part 2",
        "Minibus",
        "Sew it Good - Part 1",
        "Sew it Good - Part 2",
        "Sew it Good - Part 3",
        "Sew it Good - Part 4",
        "The Key to Success",
        "Living High is Not a Crime - Part 1",
        "Living High is Not a Crime - Part 2",
        "Charisma Brings Success",
        "No Fuss Needed",
        "Supervisor",
        "Scavenger",
        "Inventory Check",
        "A Fuel Matter",
        "Break the Deal"
    ],
    "Jaeger": [
        "Acquaintance",
        "The Survivalist Path - Unprotected but Dangerous",
        "The Survivalist Path - Thrifty",
        "The Survivalist Path - Zhivchik",
        "The Survivalist Path - Wounded Beast",
        "The Survivalist Path - Tough Guy",
        "The Survivalist Path - Junkie",
        "The Survivalist Path - Eagle-Owl",
        "The Survivalist Path - Combat Medic",
        "The Huntsman Path - Secured Perimeter",
        "The Huntsman Path - Trophy",
        "The Huntsman Path - Forest Cleaning",
        "The Huntsman Path - Controller",
        "The Huntsman Path - Sellout",
        "The Huntsman Path - Woods Keeper",
        "The Huntsman Path - Justice",
        "The Huntsman Path - Evil Watchman",
        "The Huntsman Path - Eraser - Part 1",
        "The Huntsman Path - Eraser - Part 2",
        "The Huntsman Path - Sadist",
        "Ambulance",
        "Shady Business",
        "Nostalgia",
        "Fishing Place",
        "Courtesy Visit",
        "Hunting Trip",
        "Reserve",
        "The Tarkov Shooter - Part 1",
        "The Tarkov Shooter - Part 2",
        "The Tarkov Shooter - Part 3",
        "The Tarkov Shooter - Part 4",
        "The Tarkov Shooter - Part 5",
        "The Tarkov Shooter - Part 6",
        "The Tarkov Shooter - Part 7",
        "The Tarkov Shooter - Part 8",
        "Pest Control",
        "The Huntsman Path - Factory Chief",
        "The Hermit",
        "The Huntsman Path - Outcasts",
        "Stray Dogs",
        "The Delicious Sausage",
        "Every Hunter Knows This",
        "Rough Tarkov",
        "Dragnet",
        "Claustrophobia",
        "Work Smarter",
        "Rite of Passage"
    ],
    "Fence": ["Collector"],
}

prapor_quest_links = {
    "Shooting Cans": "https://escapefromtarkov.fandom.com/wiki/Shooting_Cans",
    "Debut": "https://escapefromtarkov.fandom.com/wiki/Debut",
    "Luxurious Life": "https://escapefromtarkov.fandom.com/wiki/Luxurious_Life",
    "Search Mission": "https://escapefromtarkov.fandom.com/wiki/Search_Mission",
    "Background Check": "https://escapefromtarkov.fandom.com/wiki/Background_Check",
    "Shootout Picnic": "https://escapefromtarkov.fandom.com/wiki/Shootout_Picnic",
    "Delivery From the Past": "https://escapefromtarkov.fandom.com/wiki/Delivery_From_the_Past",
    "BP Depot": "https://escapefromtarkov.fandom.com/wiki/BP_Depot",
    "Bad Rep Evidence": "https://escapefromtarkov.fandom.com/wiki/Bad_Rep_Evidence",
    "Ice Cream Cones": "https://escapefromtarkov.fandom.com/wiki/Ice_Cream_Cones",
    "Postman Pat - Part 1": "https://escapefromtarkov.fandom.com/wiki/Postman_Pat_-_Part_1",
    "Shaking Up the Teller": "https://escapefromtarkov.fandom.com/wiki/Shaking_Up_the_Teller",
    "The Punisher - Part 1": "https://escapefromtarkov.fandom.com/wiki/The_Punisher_-_Part_1",
    "The Punisher - Part 2": "https://escapefromtarkov.fandom.com/wiki/The_Punisher_-_Part_2",
    "The Punisher - Part 3": "https://escapefromtarkov.fandom.com/wiki/The_Punisher_-_Part_3",
    "The Punisher - Part 4": "https://escapefromtarkov.fandom.com/wiki/The_Punisher_-_Part_4",
    "The Punisher - Part 5": "https://escapefromtarkov.fandom.com/wiki/The_Punisher_-_Part_5",
    "The Punisher - Part 6": "https://escapefromtarkov.fandom.com/wiki/The_Punisher_-_Part_6",
    "Polikhim Hobo": "https://escapefromtarkov.fandom.com/wiki/Polikhim_Hobo",
    "Big Customer": "https://escapefromtarkov.fandom.com/wiki/Big_Customer",
    "Grenadier": "https://escapefromtarkov.fandom.com/wiki/Grenadier",
    "Perfect Mediator": "https://escapefromtarkov.fandom.com/wiki/Perfect_Mediator",
    "Test Drive - Part 1": "https://escapefromtarkov.fandom.com/wiki/Test_Drive_-_Part_1",
    "Test Drive - Part 2": "https://escapefromtarkov.fandom.com/wiki/Test_Drive_-_Part_2",
    "Test Drive - Part 3": "https://escapefromtarkov.fandom.com/wiki/Test_Drive_-_Part_3",
    "Test Drive - Part 4": "https://escapefromtarkov.fandom.com/wiki/Test_Drive_-_Part_4",
    "Test Drive - Part 5": "https://escapefromtarkov.fandom.com/wiki/Test_Drive_-_Part_5",
    "Test Drive - Part 6": "https://escapefromtarkov.fandom.com/wiki/Test_Drive_-_Part_6",
    "Regulated Materials": "https://escapefromtarkov.fandom.com/wiki/Regulated_Materials",
    "The Bunker - Part 1": "https://escapefromtarkov.fandom.com/wiki/The_Bunker_-_Part_1",
    "The Bunker - Part 2": "https://escapefromtarkov.fandom.com/wiki/The_Bunker_-_Part_2",
    "Anesthesia": "https://escapefromtarkov.fandom.com/wiki/Anesthesia",
    "Documents": "https://escapefromtarkov.fandom.com/wiki/Documents",
    "No Place for Renegades": "https://escapefromtarkov.fandom.com/wiki/No_Place_for_Renegades",
    "Intimidator": "https://escapefromtarkov.fandom.com/wiki/Intimidator",
    "Easy Job - Part 1": "https://escapefromtarkov.fandom.com/wiki/Easy_Job_-_Part_1",
    "Easy Job - Part 2": "https://escapefromtarkov.fandom.com/wiki/Easy_Job_-_Part_2",
    "Reconnaissance": "https://escapefromtarkov.fandom.com/wiki/Reconnaissance",
    "Possessor": "https://escapefromtarkov.fandom.com/wiki/Possessor",
    "Belka and Strelka": "https://escapefromtarkov.fandom.com/wiki/Belka_and_Strelka",
}

therapist_quest_links = {
    "First in Line": "https://escapefromtarkov.fandom.com/wiki/First_in_Line",
    "Shortage": "https://escapefromtarkov.fandom.com/wiki/Shortage",
    "Sanitary Standards - Part 1": "https://escapefromtarkov.fandom.com/wiki/Sanitary_Standards_-_Part_1",
    "Sanitary Standards - Part 2": "https://escapefromtarkov.fandom.com/wiki/Sanitary_Standards_-_Part_2",
    "Operation Aquarius - Part 1": "https://escapefromtarkov.fandom.com/wiki/Operation_Aquarius_-_Part_1",
    "Operation Aquarius - Part 2": "https://escapefromtarkov.fandom.com/wiki/Operation_Aquarius_-_Part_2",
    "Painkiller": "https://escapefromtarkov.fandom.com/wiki/Painkiller",
    "Pharmacist": "https://escapefromtarkov.fandom.com/wiki/Pharmacist",
    "Supply Plans": "https://escapefromtarkov.fandom.com/wiki/Supply_Plans",
    "General Wares": "https://escapefromtarkov.fandom.com/wiki/General_Wares",
    "Car Repair": "https://escapefromtarkov.fandom.com/wiki/Car_Repair",
    "Health Care Privacy - Part 1": "https://escapefromtarkov.fandom.com/wiki/Health_Care_Privacy_-_Part_1",
    "Health Care Privacy - Part 2": "https://escapefromtarkov.fandom.com/wiki/Health_Care_Privacy_-_Part_2",
    "Health Care Privacy - Part 3": "https://escapefromtarkov.fandom.com/wiki/Health_Care_Privacy_-_Part_3",
    "Health Care Privacy - Part 4": "https://escapefromtarkov.fandom.com/wiki/Health_Care_Privacy_-_Part_4",
    "Health Care Privacy - Part 5": "https://escapefromtarkov.fandom.com/wiki/Health_Care_Privacy_-_Part_5",
    "Health Care Privacy - Part 6": "https://escapefromtarkov.fandom.com/wiki/Health_Care_Privacy_-_Part_6",
    "Postman Pat - Part 2": "https://escapefromtarkov.fandom.com/wiki/Postman_Pat_-_Part_2",
    "Out of Curiosity": "https://escapefromtarkov.fandom.com/wiki/Out_of_Curiosity",
    "Athlete": "https://escapefromtarkov.fandom.com/wiki/Athlete",
    "Decontamination Service": "https://escapefromtarkov.fandom.com/wiki/Decontamination_Service",
    "Private Clinic": "https://escapefromtarkov.fandom.com/wiki/Private_Clinic",
    "An Apple a Day Keeps the Doctor Away": "https://escapefromtarkov.fandom.com/wiki/An_Apple_a_Day_Keeps_the_Doctor_Away",
    "Colleagues - Part 1": "https://escapefromtarkov.fandom.com/wiki/Colleagues_-_Part_1",
    "Colleagues - Part 2": "https://escapefromtarkov.fandom.com/wiki/Colleagues_-_Part_2",
    "Colleagues - Part 3": "https://escapefromtarkov.fandom.com/wiki/Colleagues_-_Part_3",
    "Disease History": "https://escapefromtarkov.fandom.com/wiki/Disease_History",
    "Crisis": "https://escapefromtarkov.fandom.com/wiki/Crisis",
    "Seaside Vacation": "https://escapefromtarkov.fandom.com/wiki/Seaside_Vacation",
    "Lost Contact": "https://escapefromtarkov.fandom.com/wiki/Lost_Contact",
    "Drug Trafficking": "https://escapefromtarkov.fandom.com/wiki/Drug_Trafficking",
    "All Is Revealed": "https://escapefromtarkov.fandom.com/wiki/All_Is_Revealed",
    "A Healthy Alternative": "https://escapefromtarkov.fandom.com/wiki/A_Healthy_Alternative",
    "Shipment Tracking": "https://escapefromtarkov.fandom.com/wiki/Shipment_Tracking",
    "Closer to the People": "https://escapefromtarkov.fandom.com/wiki/Closer_to_the_People",
    "Abandoned Cargo": "https://escapefromtarkov.fandom.com/wiki/Abandoned_Cargo"
}

skier_quest_links = {
    "Burning Rubber": "https://escapefromtarkov.fandom.com/wiki/Burning_Rubber",
    "Supplier": "https://escapefromtarkov.fandom.com/wiki/Supplier",
    "The Extortionist": "https://escapefromtarkov.fandom.com/wiki/The_Extortionist",
    "Stirrup": "https://escapefromtarkov.fandom.com/wiki/Stirrup",
    "What’s on the Flash Drive?": "https://escapefromtarkov.fandom.com/wiki/What%E2%80%99s_on_the_Flash_Drive%3F",
    "Golden Swag": "https://escapefromtarkov.fandom.com/wiki/Golden_Swag",
    "Chemical - Part 1": "https://escapefromtarkov.fandom.com/wiki/Chemical_-_Part_1",
    "Chemical - Part 2": "https://escapefromtarkov.fandom.com/wiki/Chemical_-_Part_2",
    "Chemical - Part 3": "https://escapefromtarkov.fandom.com/wiki/Chemical_-_Part_3",
    "Chemical - Part 4": "https://escapefromtarkov.fandom.com/wiki/Chemical_-_Part_4",
    "Loyalty Buyout": "https://escapefromtarkov.fandom.com/wiki/Loyalty_Buyout",
    "Friend From the West - Part 1": "https://escapefromtarkov.fandom.com/wiki/Friend_From_the_West_-_Part_1",
    "Friend From the West - Part 2": "https://escapefromtarkov.fandom.com/wiki/Friend_From_the_West_-_Part_2",
    "Vitamins - Part 1": "https://escapefromtarkov.fandom.com/wiki/Vitamins_-_Part_1",
    "Vitamins - Part 2": "https://escapefromtarkov.fandom.com/wiki/Vitamins_-_Part_2",
    "Lend-Lease - Part 1": "https://escapefromtarkov.fandom.com/wiki/Lend-Lease_-_Part_1",
    "Informed Means Armed": "https://escapefromtarkov.fandom.com/wiki/Informed_Means_Armed",
    "Chumming": "https://escapefromtarkov.fandom.com/wiki/Chumming",
    "Kind of Sabotage": "https://escapefromtarkov.fandom.com/wiki/Kind_of_Sabotage",
    "Setup": "https://escapefromtarkov.fandom.com/wiki/Setup",
    "Flint": "https://escapefromtarkov.fandom.com/wiki/Flint",
    "Rigged Game": "https://escapefromtarkov.fandom.com/wiki/Rigged_Game",
    "Safe Corridor": "https://escapefromtarkov.fandom.com/wiki/Safe_Corridor",
    "Long Road": "https://escapefromtarkov.fandom.com/wiki/Long_Road",
    "Missing Cargo": "https://escapefromtarkov.fandom.com/wiki/Missing_Cargo",
    "The Walls Have Eyes": "https://escapefromtarkov.fandom.com/wiki/The_Walls_Have_Eyes",
    "Exit Here": "https://escapefromtarkov.fandom.com/wiki/Exit_Here",
    "Private Club": "https://escapefromtarkov.fandom.com/wiki/Private_Club"
}

peacekeeper_quest_links = {
    "Fishing Gear": "https://escapefromtarkov.fandom.com/wiki/Fishing_Gear",
    "Tigr Safari": "https://escapefromtarkov.fandom.com/wiki/Tigr_Safari",
    "Scrap Metal": "https://escapefromtarkov.fandom.com/wiki/Scrap_Metal",
    "Eagle Eye": "https://escapefromtarkov.fandom.com/wiki/Eagle_Eye",
    "Humanitarian Supplies": "https://escapefromtarkov.fandom.com/wiki/Humanitarian_Supplies",
    "The Cult - Part 1": "https://escapefromtarkov.fandom.com/wiki/The_Cult_-_Part_1",
    "The Cult - Part 2": "https://escapefromtarkov.fandom.com/wiki/The_Cult_-_Part_2",
    "Spa Tour - Part 1": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_1",
    "Spa Tour - Part 2": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_2",
    "Spa Tour - Part 3": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_3",
    "Spa Tour - Part 4": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_4",
    "Spa Tour - Part 5": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_5",
    "Spa Tour - Part 6": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_6",
    "Spa Tour - Part 7": "https://escapefromtarkov.fandom.com/wiki/Spa_Tour_-_Part_7",
    "Cargo X - Part 1": "https://escapefromtarkov.fandom.com/wiki/Cargo_X_-_Part_1",
    "Cargo X - Part 2": "https://escapefromtarkov.fandom.com/wiki/Cargo_X_-_Part_2",
    "Cargo X - Part 3": "https://escapefromtarkov.fandom.com/wiki/Cargo_X_-_Part_3",
    "Wet Job - Part 1": "https://escapefromtarkov.fandom.com/wiki/Wet_Job_-_Part_1",
    "Wet Job - Part 2": "https://escapefromtarkov.fandom.com/wiki/Wet_Job_-_Part_2",
    "Wet Job - Part 3": "https://escapefromtarkov.fandom.com/wiki/Wet_Job_-_Part_3",
    "Wet Job - Part 4": "https://escapefromtarkov.fandom.com/wiki/Wet_Job_-_Part_4",
    "Wet Job - Part 5": "https://escapefromtarkov.fandom.com/wiki/Wet_Job_-_Part_5",
    "Wet Job - Part 6": "https://escapefromtarkov.fandom.com/wiki/Wet_Job_-_Part_6",
    "The Guide": "https://escapefromtarkov.fandom.com/wiki/The_Guide",
    "Peacekeeping Mission": "https://escapefromtarkov.fandom.com/wiki/Peacekeeping_Mission",
    "Lend-Lease - Part 2": "https://escapefromtarkov.fandom.com/wiki/Lend-Lease_-_Part_2",
    "Samples": "https://escapefromtarkov.fandom.com/wiki/Samples",
    "TerraGroup Employee": "https://escapefromtarkov.fandom.com/wiki/TerraGroup_Employee",
    "Revision - Reserve": "https://escapefromtarkov.fandom.com/wiki/Revision_-_Reserve",
    "Revision - Lighthouse": "https://escapefromtarkov.fandom.com/wiki/Revision_-_Lighthouse",
    "Classified Technologies": "https://escapefromtarkov.fandom.com/wiki/Classified_Technologies",
    "Cargo X - Part 4": "https://escapefromtarkov.fandom.com/wiki/Cargo_X_-_Part_4",
    "Insomnia": "https://escapefromtarkov.fandom.com/wiki/Insomnia",
    "Overpopulation": "https://escapefromtarkov.fandom.com/wiki/Overpopulation",
    "One Less Loose End": "https://escapefromtarkov.fandom.com/wiki/One_Less_Loose_End"
}

mechanic_quest_links = {
    "Saving the Mole": "https://escapefromtarkov.fandom.com/wiki/Saving_the_Mole",
    "Gunsmith - Part 1": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_1",
    "Gunsmith - Part 2": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_2",
    "Gunsmith - Part 3": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_3",
    "Gunsmith - Part 4": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_4",
    "Gunsmith - Part 5": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_5",
    "Gunsmith - Part 6": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_6",
    "Gunsmith - Part 7": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_7",
    "Gunsmith - Part 8": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_8",
    "Gunsmith - Part 9": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_9",
    "Gunsmith - Part 10": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_10",
    "Gunsmith - Part 11": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_11",
    "Gunsmith - Part 12": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_12",
    "Gunsmith - Part 13": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_13",
    "Gunsmith - Part 14": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_14",
    "Gunsmith - Part 15": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_15",
    "Gunsmith - Part 16": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_16",
    "Gunsmith - Part 17": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_17",
    "Gunsmith - Part 18": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_18",
    "Gunsmith - Part 19": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_19",
    "Gunsmith - Part 20": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_20",
    "Gunsmith - Part 21": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_21",
    "Gunsmith - Part 22": "https://escapefromtarkov.fandom.com/wiki/Gunsmith_-_Part_22",
    "Farming - Part 1": "https://escapefromtarkov.fandom.com/wiki/Farming_-_Part_1",
    "Farming - Part 2": "https://escapefromtarkov.fandom.com/wiki/Farming_-_Part_2",
    "Farming - Part 3": "https://escapefromtarkov.fandom.com/wiki/Farming_-_Part_3",
    "Farming - Part 4": "https://escapefromtarkov.fandom.com/wiki/Farming_-_Part_4",
    "Signal - Part 1": "https://escapefromtarkov.fandom.com/wiki/Signal_-_Part_1",
    "Signal - Part 2": "https://escapefromtarkov.fandom.com/wiki/Signal_-_Part_2",
    "Signal - Part 3": "https://escapefromtarkov.fandom.com/wiki/Signal_-_Part_3",
    "Signal - Part 4": "https://escapefromtarkov.fandom.com/wiki/Signal_-_Part_4",
    "Bad Habit": "https://escapefromtarkov.fandom.com/wiki/Bad_Habit",
    "Scout": "https://escapefromtarkov.fandom.com/wiki/Scout",
    "Insider": "https://escapefromtarkov.fandom.com/wiki/Insider",
    "Import": "https://escapefromtarkov.fandom.com/wiki/Import",
    "Fertilizers": "https://escapefromtarkov.fandom.com/wiki/Fertilizers",
    "Psycho Sniper": "https://escapefromtarkov.fandom.com/wiki/Psycho_Sniper",
    "A Shooter Born in Heaven": "https://escapefromtarkov.fandom.com/wiki/A_Shooter_Born_in_Heaven",
    "Introduction": "https://escapefromtarkov.fandom.com/wiki/Introduction",
    "Chemistry Closet": "https://escapefromtarkov.fandom.com/wiki/Chemistry_Closet",
    "Surplus Goods": "https://escapefromtarkov.fandom.com/wiki/Surplus_Goods",
    "Back Door": "https://escapefromtarkov.fandom.com/wiki/Back_Door",
    "Corporate Secrets": "https://escapefromtarkov.fandom.com/wiki/Corporate_Secrets",
    "Energy Crisis": "https://escapefromtarkov.fandom.com/wiki/Energy_Crisis",
    "Broadcast - Part 1": "https://escapefromtarkov.fandom.com/wiki/Broadcast_-_Part_1",
    "Capacity Check": "https://escapefromtarkov.fandom.com/wiki/Capacity_Check",
    "Black Swan": "https://escapefromtarkov.fandom.com/wiki/Black_Swan",
    "Forklift Certified": "https://escapefromtarkov.fandom.com/wiki/Forklift_Certified",
    "Passion for Ergonomics": "https://escapefromtarkov.fandom.com/wiki/Passion_for_Ergonomics"
}

ragman_quest_links = {
    "Only Business": "https://escapefromtarkov.fandom.com/wiki/Only_Business",
    "Make ULTRA Great Again": "https://escapefromtarkov.fandom.com/wiki/Make_ULTRA_Great_Again",
    "Big Sale": "https://escapefromtarkov.fandom.com/wiki/Big_Sale",
    "The Blood of War - Part 1": "https://escapefromtarkov.fandom.com/wiki/The_Blood_of_War_-_Part_1",
    "The Blood of War - Part 2": "https://escapefromtarkov.fandom.com/wiki/The_Blood_of_War_-_Part_2",
    "The Blood of War - Part 3": "https://escapefromtarkov.fandom.com/wiki/The_Blood_of_War_-_Part_3",
    "Dressed to Kill": "https://escapefromtarkov.fandom.com/wiki/Dressed_to_Kill",
    "Gratitude": "https://escapefromtarkov.fandom.com/wiki/Gratitude",
    "Sales Night": "https://escapefromtarkov.fandom.com/wiki/Sales_Night",
    "Hot Delivery": "https://escapefromtarkov.fandom.com/wiki/Hot_Delivery",
    "Database - Part 1": "https://escapefromtarkov.fandom.com/wiki/Database_-_Part_1",
    "Database - Part 2": "https://escapefromtarkov.fandom.com/wiki/Database_-_Part_2",
    "Minibus": "https://escapefromtarkov.fandom.com/wiki/Minibus",
    "Sew it Good - Part 1": "https://escapefromtarkov.fandom.com/wiki/Sew_it_Good_-_Part_1",
    "Sew it Good - Part 2": "https://escapefromtarkov.fandom.com/wiki/Sew_it_Good_-_Part_2",
    "Sew it Good - Part 3": "https://escapefromtarkov.fandom.com/wiki/Sew_it_Good_-_Part_3",
    "Sew it Good - Part 4": "https://escapefromtarkov.fandom.com/wiki/Sew_it_Good_-_Part_4",
    "The Key to Success": "https://escapefromtarkov.fandom.com/wiki/The_Key_to_Success",
    "Living High is Not a Crime - Part 1": "https://escapefromtarkov.fandom.com/wiki/Living_High_is_Not_a_Crime_-_Part_1",
    "Living High is Not a Crime - Part 2": "https://escapefromtarkov.fandom.com/wiki/Living_High_is_Not_a_Crime_-_Part_2",
    "Charisma Brings Success": "https://escapefromtarkov.fandom.com/wiki/Charisma_Brings_Success",
    "No Fuss Needed": "https://escapefromtarkov.fandom.com/wiki/No_Fuss_Needed",
    "Supervisor": "https://escapefromtarkov.fandom.com/wiki/Supervisor",
    "Scavenger": "https://escapefromtarkov.fandom.com/wiki/Scavenger",
    "Inventory Check": "https://escapefromtarkov.fandom.com/wiki/Inventory_Check",
    "A Fuel Matter": "https://escapefromtarkov.fandom.com/wiki/A_Fuel_Matter",
    "Break the Deal": "https://escapefromtarkov.fandom.com/wiki/Break_the_Deal"
}

jaeger_quest_links = {
    "Acquaintance": "https://escapefromtarkov.fandom.com/wiki/Acquaintance",
    "The Survivalist Path - Unprotected but Dangerous": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Unprotected_but_Dangerous",
    "The Survivalist Path - Thrifty": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Thrifty",
    "The Survivalist Path - Zhivchik": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Zhivchik",
    "The Survivalist Path - Wounded Beast": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Wounded_Beast",
    "The Survivalist Path - Tough Guy": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Tough_Guy",
    "The Survivalist Path - Junkie": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Junkie",
    "The Survivalist Path - Eagle-Owl": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Eagle-Owl",
    "The Survivalist Path - Combat Medic": "https://escapefromtarkov.fandom.com/wiki/The_Survivalist_Path_-_Combat_Medic",
    "The Huntsman Path - Secured Perimeter": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Secured_Perimeter",
    "The Huntsman Path - Trophy": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Trophy",
    "The Huntsman Path - Forest Cleaning": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Forest_Cleaning",
    "The Huntsman Path - Controller": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Controller",
    "The Huntsman Path - Sellout": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Sellout",
    "The Huntsman Path - Woods Keeper": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Woods_Keeper",
    "The Huntsman Path - Justice": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Justice",
    "The Huntsman Path - Evil Watchman": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Evil_Watchman",
    "The Huntsman Path - Eraser - Part 1": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Eraser_-_Part_1",
    "The Huntsman Path - Eraser - Part 2": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Eraser_-_Part_2",
    "The Huntsman Path - Sadist": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Sadist",
    "Ambulance": "https://escapefromtarkov.fandom.com/wiki/Ambulance",
    "Shady Business": "https://escapefromtarkov.fandom.com/wiki/Shady_Business",
    "Nostalgia": "https://escapefromtarkov.fandom.com/wiki/Nostalgia",
    "Fishing Place": "https://escapefromtarkov.fandom.com/wiki/Fishing_Place",
    "Courtesy Visit": "https://escapefromtarkov.fandom.com/wiki/Courtesy_Visit",
    "Hunting Trip": "https://escapefromtarkov.fandom.com/wiki/Hunting_Trip",
    "Reserve": "https://escapefromtarkov.fandom.com/wiki/Reserve",
    "The Tarkov Shooter - Part 1": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_1",
    "The Tarkov Shooter - Part 2": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_2",
    "The Tarkov Shooter - Part 3": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_3",
    "The Tarkov Shooter - Part 4": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_4",
    "The Tarkov Shooter - Part 5": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_5",
    "The Tarkov Shooter - Part 6": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_6",
    "The Tarkov Shooter - Part 7": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_7",
    "The Tarkov Shooter - Part 8": "https://escapefromtarkov.fandom.com/wiki/The_Tarkov_Shooter_-_Part_8",
    "Pest Control": "https://escapefromtarkov.fandom.com/wiki/Pest_Control",
    "The Huntsman Path - Factory Chief": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Factory_Chief",
    "The Hermit": "https://escapefromtarkov.fandom.com/wiki/The_Hermit",
    "The Huntsman Path - Outcasts": "https://escapefromtarkov.fandom.com/wiki/The_Huntsman_Path_-_Outcasts",
    "Stray Dogs": "https://escapefromtarkov.fandom.com/wiki/Stray_Dogs",
    "The Delicious Sausage": "https://escapefromtarkov.fandom.com/wiki/The_Delicious_Sausage",
    "Every Hunter Knows This": "https://escapefromtarkov.fandom.com/wiki/Every_Hunter_Knows_This",
    "Rough Tarkov": "https://escapefromtarkov.fandom.com/wiki/Rough_Tarkov",
    "Dragnet": "https://escapefromtarkov.fandom.com/wiki/Dragnet",
    "Claustrophobia": "https://escapefromtarkov.fandom.com/wiki/Claustrophobia",
    "Work Smarter": "https://escapefromtarkov.fandom.com/wiki/Work_Smarter",
    "Rite of Passage": "https://escapefromtarkov.fandom.com/wiki/Rite_of_Passage"
}

fence_quest_links = {
    "Collector": "https://escapefromtarkov.fandom.com/wiki/Collector"
}    

all_quest_links = {}
all_quest_links.update(prapor_quest_links)
all_quest_links.update(therapist_quest_links)
all_quest_links.update(skier_quest_links)
all_quest_links.update(peacekeeper_quest_links)
all_quest_links.update(mechanic_quest_links)
all_quest_links.update(ragman_quest_links)
all_quest_links.update(jaeger_quest_links)
all_quest_links.update(fence_quest_links)

# === QUEST TRADER SELECTOR SCREEN ===

def open_trader_quests(trader):
    load_quest_checklist_vars(trader)
    show_screen(quest_checklist_screen)

def open_all_quests():
    load_quest_checklist_vars()
    show_screen(quest_checklist_screen)

quest_selector_label = ctk.CTkLabel(quest_checklist_screen, text="Select Trader for Quests", font=("Arial", 24))
# We'll add this label on a separate screen if needed

# For the checklist_screen, we don't need extra widgets here, it's handled elsewhere

# === TRADER IMAGES SCREEN for QUEST SELECTION ===
# We'll build this as quest_checklist_screen, but separated by traders with images and clickable buttons

def build_trader_selection_screen():
    for widget in quest_checklist_screen.winfo_children():
        widget.destroy()

    # Back button - top-left
    back_btn = ctk.CTkButton(quest_checklist_screen, text="← Back", command=lambda: switch_and_save(tracker_screen))
    back_btn.place(x=10, y=10)  # Top-left

    # View All Quests button - top-right
    all_quests_btn = ctk.CTkButton(quest_checklist_screen, text="View All Quests", command=open_all_quests)
    all_quests_btn.place(relx=1.0, x=-10, y=10, anchor="ne")  # Top-right

    # Header label - centered at the top
    label = ctk.CTkLabel(quest_checklist_screen, text="Quests by Trader", font=("Arial", 28))
    label.place(relx=0.5, y=10, anchor="n")  # Top center

    # Trader grid (now offset downward slightly)
    traders_frame = ctk.CTkFrame(quest_checklist_screen, fg_color="transparent")
    traders_frame.pack(pady=(45, 0))  # Push content down below top bar

    row = 0
    col = 0
    for i, trader in enumerate(trader_images.keys()):
        def make_cmd(t=trader):
            return lambda: open_trader_quests(t)
        btn = ctk.CTkButton(
            traders_frame,
            image=trader_images[trader],
            text=trader,
            compound="top",
            width=120,
            height=140,
            command=make_cmd()
        )
        btn.grid(row=row, column=col, padx=15, pady=15)
        col += 1
        if col > 3:
            col = 0
            row += 1

    # Add footer at bottom
    add_footer(quest_checklist_screen)

# We'll call this function before showing the quest checklist trader selector screen
def open_quest_checklist_selector():
    build_trader_selection_screen()
    show_screen(quest_checklist_screen)

# === ON APP STARTUP ===

def init_app():
    global app_ready

    # Set saved values in UI variables
    selected_game_mode.set(data.get("game_mode", ""))
    selected_faction.set(data.get("faction", ""))

    gm = selected_game_mode.get()
    level_data = data.get("level", {})
    if isinstance(level_data, dict) and gm in level_data:
        level_value.set(level_data[gm])
    else:
        level_value.set(1)

    # Show the correct screen
    if not data.get("username") or not data.get("faction"):
        switch_and_save(build_faction_screen)
    elif not gm:
        switch_and_save(build_game_mode_screen)
    else:
        # Load checklist vars from saved data
        load_checklist_vars()
        load_quest_checklist_vars()

        # Update UI variables based on saved data for current mode
        update_checklist_vars()
        update_quest_checklist_vars()

        # Update progress labels to reflect loaded state
        update_progress_labels()

        # Update welcome message UI
        update_welcome_message()
        
        #print(f"Starting tracker screen with mode: {selected_game_mode.get()}")
        switch_and_save(build_tracker_screen)

    app_ready = True

# Load checklist vars for current mode
def load_checklist_vars():
    #print(f"[DEBUG] load_checklist_vars() called. Current mode: {selected_game_mode.get()}")

    checklist_vars.clear()
    for widget in checklist_screen.winfo_children():
        widget.destroy()

    # Back button - fixed top-left with place()
    back_btn = ctk.CTkButton(
        checklist_screen,
        text="← Back",
        command=lambda: [save_data(), switch_and_save(tracker_screen)]
    )
    back_btn.place(x=10, y=10)

    # Title label - centered
    checklist_screen_label = ctk.CTkLabel(
        checklist_screen,
        text="Kappa Items Checklist",
        font=("Arial", 24),
        fg_color="transparent"
    )
    checklist_screen_label.pack(pady=(10, 20))

    # Container frame for scrollable + footer
    content_frame = ctk.CTkFrame(checklist_screen, fg_color="transparent")
    content_frame.pack(expand=True, fill="both", padx=20, pady=(0, 20))

    # Scrollable frame inside container with fixed height (like quest screen)
    scrollable_frame = ctk.CTkScrollableFrame(content_frame, height=305)
    scrollable_frame.pack(expand=False, fill="x", pady=(0,10))  # fixed height, width fills container

    for item, url in kappa_items_with_links.items():
        var = ctk.BooleanVar()
        checklist_vars[item] = var

        item_frame = ctk.CTkFrame(scrollable_frame)
        item_frame.pack(fill="x", pady=3)

        checkbox = ctk.CTkCheckBox(
            item_frame,
            text=item,
            variable=var,
            command=lambda: [update_progress_labels(), save_data()]
        )
        checkbox.pack(side="left", padx=(5, 15))

        info_button = ctk.CTkButton(
            item_frame,
            text="Info",
            width=50,
            command=lambda url=url: open_info_link(url)
        )
        info_button.pack(side="right", padx=5)

    update_checklist_vars()
    update_progress_labels()

    add_footer(checklist_screen)

def load_quest_checklist_vars(trader=None):
    global quest_page_index, page_indicator_label

    current_mode = selected_game_mode.get()
    if not current_mode:
        return

    # === DEBUG PRINTS ===
    #print(f"[DEBUG] Loading quest checklist for mode: {current_mode}")
    saved_state = data.get("quest_checklist", {}).get(current_mode, {})
    #print(f"[DEBUG] Saved quests checked: {[k for k,v in saved_state.items() if v]}")
    # ====================

    # Clear existing UI
    for widget in quest_checklist_screen.winfo_children():
        widget.destroy()

    # --- Back button in top-left corner using .place() like trader screen ---
    back_btn = ctk.CTkButton(
        quest_checklist_screen, text="← Back",
        command=lambda: switch_and_save(build_trader_selection_screen)
    )
    back_btn.place(x=10, y=10)  # 10px from top and left

    # Load state (already loaded above for debug)
    # saved_state = data.get("quest_checklist", {}).get(current_mode, {})

    # Ensure all quest vars exist
    all_quests = []
    for quests in trader_quests.values():
        all_quests.extend(quests)
    for quest in all_quests:
        if quest not in quest_checklist_vars:
            quest_checklist_vars[quest] = ctk.BooleanVar()
        quest_checklist_vars[quest].set(saved_state.get(quest, False))

    # Determine quests to show
    if trader:
        quest_items_to_show = trader_quests.get(trader, [])
        screen_title = f"{trader} Quests - Mode: {current_mode}"
        trader_links = {
            "Prapor": prapor_quest_links,
            "Therapist": therapist_quest_links,
            "Skier": skier_quest_links,
            "Peacekeeper": peacekeeper_quest_links,
            "Mechanic": mechanic_quest_links,
            "Ragman": ragman_quest_links,
            "Jaeger": jaeger_quest_links,
            "Fence": fence_quest_links
        }.get(trader, {})
    else:
        quest_items_to_show = all_quests
        screen_title = f"All Quests - Mode: {current_mode}"
        trader_links = all_quest_links

        # Clamp page index
        total_pages = (len(quest_items_to_show) - 1) // QUESTS_PER_PAGE + 1
        quest_page_index = max(0, min(quest_page_index, total_pages - 1))

        start = quest_page_index * QUESTS_PER_PAGE
        end = start + QUESTS_PER_PAGE
        quest_items_to_show = quest_items_to_show[start:end]

    # Title label centered using .pack()
    label = ctk.CTkLabel(quest_checklist_screen, text=screen_title, font=("Arial", 24))
    label.pack(pady=(10, 0))  # top padding 10, bottom 0

    # Scrollable quest checklist
    scrollable_frame = ctk.CTkScrollableFrame(quest_checklist_screen, height=280)
    scrollable_frame.pack(fill="x", padx=20, pady=(10, 10))

    for quest in quest_items_to_show:
        var = quest_checklist_vars[quest]

        row_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        cb = ctk.CTkCheckBox(
            row_frame,
            text=quest,
            variable=var,
            command=lambda q=quest: [update_progress_labels(), save_quest_checklist_state(), save_data()]  # <-- Updated here
        )
        cb.pack(side="left", anchor="w")

        if trader_links and quest in trader_links:
            info_btn = ctk.CTkButton(
                row_frame,
                text="Info",
                width=60,
                height=24,
                command=lambda url=trader_links[quest]: open_info_link(url)
            )
            info_btn.pack(side="right")

    # Pagination for "All Quests"
    nav_frame = ctk.CTkFrame(quest_checklist_screen, fg_color="transparent")
    nav_frame.pack(pady=5)

    if not trader:
        total_pages = (len(all_quests) - 1) // QUESTS_PER_PAGE + 1
        current_page = quest_page_index + 1

        prev_btn = ctk.CTkButton(nav_frame, text="← Prev", command=lambda: change_quest_page(-1))
        prev_btn.pack(side="left", padx=10)
        if quest_page_index == 0:
            prev_btn.configure(state="disabled")

        page_indicator_label = ctk.CTkLabel(
            nav_frame,
            text=f"Page {current_page} of {total_pages}",
            font=("Arial", 16)
        )
        page_indicator_label.pack(side="left", padx=10)

        next_btn = ctk.CTkButton(nav_frame, text="Next →", command=lambda: change_quest_page(1))
        next_btn.pack(side="left", padx=10)
        if current_page >= total_pages:
            next_btn.configure(state="disabled")

    update_progress_labels()

    # Add footer
    add_footer(quest_checklist_screen)

# === AUTOSAVE every 30 seconds ===
def autosave():
    if app_ready:
        save_data()
    else:
        app.after(int(0.5 * 60 * 1000), autosave)  # 30 seconds in ms

autosave()

def on_app_close():
    update_data_level_from_vars()
    update_data_checklist_from_vars()       
    update_data_quest_checklist_from_vars() 
    save_data()
    app.destroy()

# === START ===
init_app()
app.mainloop()
