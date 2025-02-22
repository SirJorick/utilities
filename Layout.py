import os
import shutil
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinter import ttk

# Predefined project layout (directories and files)
PROJECT_DIRECTORIES = [
    "core",
    os.path.join("core", "gui"),
    os.path.join("core", "processing"),
    os.path.join("core", "utils"),
    "assets",
    os.path.join("assets", "images"),
    os.path.join("assets", "icons"),
    "docs",
    "tests",
    "config",
    "data",
    "scripts",
    "logs"
]

PROJECT_FILES = {
    os.path.join("core", "__init__.py"): "",
    os.path.join("core", "main.py"): "# Entry point for your application\n",
    os.path.join("core", "gui", "__init__.py"): "",
    os.path.join("core", "gui", "interface.py"): "# Contains the GUI-related classes and functions\n",
    os.path.join("core", "processing", "__init__.py"): "",
    os.path.join("core", "processing", "tasks.py"): "# Contains heavy processing functions\n",
    os.path.join("core", "utils", "__init__.py"): "",
    os.path.join("core", "utils", "helper.py"): "# Contains utility functions\n",
    # Example: a blank log file (could be used for other logging)
    os.path.join("logs", "log.txt"): ""
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Structure Builder")
        self.geometry("800x800")
        # The project root will be set using the editable input field.
        self.project_root = ""
        # This variable stores the browsed folder (used only for navigation).
        self.selected_root = ""
        self.overwrite_all = False
        self.skip_all = False
        self.create_widgets()

    def create_widgets(self):
        # ----- Top Frame: Project Root input and Browser -----
        top_frame = tk.Frame(self)
        top_frame.pack(pady=10)

        tk.Label(top_frame, text="Project Root (editable):").pack(side=tk.LEFT, padx=5)
        self.project_root_var = tk.StringVar(value="")
        self.entry_root = tk.Entry(top_frame, textvariable=self.project_root_var, width=50)
        self.entry_root.pack(side=tk.LEFT, padx=5)

        tk.Button(top_frame, text="Browse", command=self.select_root).pack(side=tk.LEFT, padx=5)
        self.btn_set_root = tk.Button(top_frame, text="Set Root", command=self.set_root, state=tk.DISABLED)
        self.btn_set_root.pack(side=tk.LEFT, padx=5)

        # ----- Current Environment Display -----
        self.selected_location_label = tk.Label(self, text="Current Environment: (none)", fg="blue")
        self.selected_location_label.pack(pady=5)

        # ----- Option: Auto Create Default Layout (unselected by default) -----
        self.auto_create_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Auto Create Default Layout", variable=self.auto_create_var).pack(pady=5)

        # ----- Output Console with reversed colors -----
        self.log_text = tk.Text(self, height=10, bg="black", fg="white")
        self.log_text.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # ----- Progress Bar and Info Label -----
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=600, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.progress_info = tk.Label(self, text="Progress: 0%")
        self.progress_info.pack(pady=2)

        # ----- Tree View Frame: Display the project structure -----
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(tree_frame, text="Project Structure").pack()
        self.tree = ttk.Treeview(tree_frame, columns=("fullpath",), displaycolumns=())
        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # ----- Buttons for operations -----
        sub_btn_frame = tk.Frame(self)
        sub_btn_frame.pack(pady=5)
        tk.Button(sub_btn_frame, text="Refresh Tree", command=self.refresh_tree).pack(side=tk.LEFT, padx=5)
        tk.Button(sub_btn_frame, text="Add Subdirectory", command=self.add_subdirectory).pack(side=tk.LEFT, padx=5)
        tk.Button(sub_btn_frame, text="Add File in Selected Directory", command=self.add_subfile).pack(side=tk.LEFT,
                                                                                                       padx=5)
        tk.Button(sub_btn_frame, text="Rename Selected", command=self.rename_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(sub_btn_frame, text="Output Directory Tree", command=self.show_directory_tree).pack(side=tk.LEFT,
                                                                                                      padx=5)

        # Enable Set Root button if the editable field is not blank.
        self.project_root_var.trace("w", self.check_root_input)

    def check_root_input(self, *args):
        if self.project_root_var.get().strip():
            self.btn_set_root.config(state=tk.NORMAL)
        else:
            self.btn_set_root.config(state=tk.DISABLED)

    def select_root(self):
        """Open Explorer for navigation. Log the selected folder without modifying the editable input."""
        folder = filedialog.askdirectory(title="Select Project Root")
        if folder:
            self.selected_root = folder
            self.selected_location_label.config(text=f"Current Environment: {folder}")
            self.btn_set_root.config(state=tk.NORMAL)
            self.log(f"Browsed folder: {folder}")

    def log(self, message):
        """Append a message to the output console."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def set_root(self):
        """
        Set the project root using the editable input field.
        If blank, clear the tree view.
        """
        new_root = self.project_root_var.get().strip()
        if not new_root:
            self.project_root = ""
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.log("Project root is blank. Layout removed.")
            return

        self.project_root = os.path.abspath(new_root)
        if not os.path.exists(self.project_root):
            try:
                os.makedirs(self.project_root)
                self.log(f"Project root created: {self.project_root}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create project root: {e}")
                return

        self.log(f"Project root set to: {self.project_root}")
        self.refresh_tree()
        self.overwrite_all = False
        self.skip_all = False
        if self.auto_create_var.get():
            self.start_time = time.time()
            threading.Thread(target=self.background_structure_creation, daemon=True).start()
        else:
            self.log("Auto Create Default Layout is disabled. Manage your layout manually.")

    def background_structure_creation(self):
        """Build the default project structure in a background thread."""
        total_tasks = len(PROJECT_DIRECTORIES) + len(PROJECT_FILES)
        completed_tasks = 0
        for folder in PROJECT_DIRECTORIES:
            full_path = os.path.join(self.project_root, folder)
            self.create_directory_task(full_path)
            completed_tasks += 1
            self.after(0, self.update_progress, completed_tasks, total_tasks)
            time.sleep(0.1)
        for rel_path, content in PROJECT_FILES.items():
            file_path = os.path.join(self.project_root, rel_path)
            self.create_file_task(file_path, content)
            completed_tasks += 1
            self.after(0, self.update_progress, completed_tasks, total_tasks)
            time.sleep(0.1)
        self.after(0, self.progress_info.config, {"text": "Done! 100%"})
        self.after(0, self.refresh_tree)
        self.log("Project structure pre-creation completed.")
        self.log_layout_creation()

    def update_progress(self, completed, total):
        """Update the progress bar, percentage, and ETA."""
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = completed
        percent = int((completed / total) * 100)
        elapsed = time.time() - self.start_time
        avg_time = elapsed / completed if completed else 0
        remaining = total - completed
        eta_seconds = int(remaining * avg_time)
        mins, secs = divmod(eta_seconds, 60)
        eta_str = f"{mins:02d}:{secs:02d}"
        self.progress_info.config(text=f"Progress: {percent}% - ETA: {eta_str}")

    def log_layout_creation(self):
        """Log layout creation to a file named 'LayoutCreation.txt' with date, time, and author info."""
        timestamp = datetime.now().strftime("%b-%d-%Y %I:%M:%S %p")
        entry = f"Layout creation completed on {timestamp} By: JRAGelbolingo"
        self.log(entry)
        log_file_path = os.path.join(self.project_root, "logs", "LayoutCreation.txt")
        try:
            with open(log_file_path, "a") as lf:
                lf.write(entry + "\n")
        except Exception as e:
            self.log(f"Error writing to layout creation log: {e}")

    def prompt_overwrite(self, item_type, path):
        """Display a prompt asking whether to overwrite an existing item."""
        result = {}
        dialog = tk.Toplevel(self)
        dialog.title("Overwrite Confirmation")
        dialog.grab_set()
        msg = f"The {item_type} at:\n\n{path}\n\nalready exists.\nDo you want to overwrite it?"
        tk.Label(dialog, text=msg, justify=tk.LEFT, padx=10, pady=10).pack()

        def set_result(value):
            result["choice"] = value
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Yes", width=10, command=lambda: set_result("yes")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Yes to All", width=10, command=lambda: set_result("yes_all")).pack(side=tk.LEFT,
                                                                                                      padx=5)
        tk.Button(btn_frame, text="No", width=10, command=lambda: set_result("no")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="No to All", width=10, command=lambda: set_result("no_all")).pack(side=tk.LEFT,
                                                                                                    padx=5)
        self.wait_window(dialog)
        return result.get("choice", "no")

    def create_directory_task(self, path):
        if os.path.exists(path):
            if self.skip_all:
                self.log(f"Skipped directory: {path}")
                return
            if not self.overwrite_all:
                decision = self.prompt_overwrite("directory", path)
                if decision == "yes_all":
                    self.overwrite_all = True
                elif decision == "no_all":
                    self.skip_all = True
                    self.log(f"Skipped directory: {path}")
                    return
                elif decision == "no":
                    self.log(f"Skipped directory: {path}")
                    return
            try:
                shutil.rmtree(path)
                os.makedirs(path)
                self.log(f"Overwritten directory: {path}")
            except Exception as e:
                self.log(f"Error overwriting directory {path}: {e}")
        else:
            try:
                os.makedirs(path)
                self.log(f"Directory created: {path}")
            except Exception as e:
                self.log(f"Error creating directory {path}: {e}")

    def create_file_task(self, file_path, content):
        if os.path.exists(file_path):
            if self.skip_all:
                self.log(f"Skipped file: {file_path}")
                return
            if not self.overwrite_all:
                decision = self.prompt_overwrite("file", file_path)
                if decision == "yes_all":
                    self.overwrite_all = True
                elif decision == "no_all":
                    self.skip_all = True
                    self.log(f"Skipped file: {file_path}")
                    return
                elif decision == "no":
                    self.log(f"Skipped file: {file_path}")
                    return
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                self.log(f"Overwritten file: {file_path}")
            except Exception as e:
                self.log(f"Error overwriting file {file_path}: {e}")
        else:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)
                self.log(f"File created: {file_path}")
            except Exception as e:
                self.log(f"Error creating file {file_path}: {e}")

    def add_subdirectory(self):
        """Add a new subdirectory within the selected directory."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parent directory.")
            return
        parent_path = self.tree.item(selected[0], "values")[0]
        new_dir = filedialog.askdirectory(initialdir=parent_path, title="Select or create Subdirectory")
        if new_dir:
            if not new_dir.startswith(parent_path):
                messagebox.showwarning("Warning", "The selected directory is not within the parent.")
                self.log(f"Subdirectory selection aborted: {new_dir} not within {parent_path}")
                return
            if os.path.exists(new_dir):
                decision = self.prompt_overwrite("directory", new_dir)
                if decision in ("yes", "yes_all"):
                    try:
                        shutil.rmtree(new_dir)
                        os.makedirs(new_dir)
                        self.log(f"Overwritten subdirectory: {new_dir}")
                    except Exception as e:
                        self.log(f"Error overwriting subdirectory {new_dir}: {e}")
                else:
                    self.log(f"Skipped subdirectory: {new_dir}")
            else:
                try:
                    os.makedirs(new_dir)
                    self.log(f"Subdirectory created: {new_dir}")
                except Exception as e:
                    self.log(f"Error creating subdirectory {new_dir}: {e}")
            self.refresh_tree()

    def add_subfile(self):
        """Add a new file within the selected directory."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parent directory.")
            return
        parent_path = self.tree.item(selected[0], "values")[0]
        file_path = filedialog.asksaveasfilename(initialdir=parent_path, title="Select/Add File",
                                                 defaultextension=".py")
        if file_path:
            if not file_path.startswith(parent_path):
                messagebox.showwarning("Warning", "The selected file is not within the parent directory.")
                self.log(f"File selection aborted: {file_path} not within {parent_path}")
                return
            if os.path.exists(file_path):
                decision = self.prompt_overwrite("file", file_path)
                if decision in ("yes", "yes_all"):
                    try:
                        with open(file_path, "w") as f:
                            f.write("")
                        self.log(f"Overwritten file: {file_path}")
                    except Exception as e:
                        self.log(f"Error overwriting file {file_path}: {e}")
                else:
                    self.log(f"Skipped file: {file_path}")
            else:
                try:
                    directory = os.path.dirname(file_path)
                    os.makedirs(directory, exist_ok=True)
                    with open(file_path, "w") as f:
                        f.write("")
                    self.log(f"File created: {file_path}")
                except Exception as e:
                    self.log(f"Error creating file {file_path}: {e}")
            self.refresh_tree()

    def rename_selected(self):
        """Rename the selected folder or file."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to rename.")
            return
        old_path = self.tree.item(selected[0], "values")[0]
        current_name = os.path.basename(old_path)
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=current_name)
        if new_name and new_name != current_name:
            parent_dir = os.path.dirname(old_path)
            new_path = os.path.join(parent_dir, new_name)
            if os.path.exists(new_path):
                messagebox.showwarning("Warning", "An item with that name already exists.")
                return
            try:
                os.rename(old_path, new_path)
                self.log(f"Renamed '{old_path}' to '{new_path}'")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename: {e}")
            self.refresh_tree()

    def show_directory_tree(self):
        """
        Generate and display a text representation of the current project structure.
        A right-click context menu allows copying text.
        """
        if not self.project_root:
            messagebox.showwarning("Warning", "Project root is not set.")
            return
        tree_text = self.generate_tree(self.project_root)
        tree_window = tk.Toplevel(self)
        tree_window.title("Directory Tree")
        text_box = tk.Text(tree_window, wrap=tk.NONE, bg="white", fg="black")
        text_box.insert(tk.END, tree_text)
        text_box.config(state=tk.DISABLED)
        text_box.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_window, orient="vertical", command=text_box.yview)
        text_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        context_menu = tk.Menu(tree_window, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: self.copy_text(text_box))
        text_box.bind("<Button-3>", lambda event: context_menu.post(event.x_root, event.y_root))

    def copy_text(self, widget):
        """Copy selected text from the widget to the clipboard."""
        try:
            selection = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selection)
        except tk.TclError:
            pass

    def generate_tree(self, root, prefix=""):
        """Recursively generate a text tree of the directory structure."""
        lines = []
        if prefix == "":
            lines.append(os.path.basename(root) + "/")
        try:
            entries = sorted(os.listdir(root))
        except Exception as e:
            lines.append(prefix + f"Error reading directory: {e}")
            return "\n".join(lines)
        for i, entry in enumerate(entries):
            full_path = os.path.join(root, entry)
            connector = "└── " if i == len(entries) - 1 else "├── "
            sub_prefix = prefix + ("    " if i == len(entries) - 1 else "│   ")
            lines.append(prefix + connector + entry)
            if os.path.isdir(full_path):
                lines.append(self.generate_tree(full_path, sub_prefix))
        return "\n".join(lines)

    def refresh_tree(self):
        """Refresh the tree view to show the current project structure."""
        if not self.project_root:
            for item in self.tree.get_children():
                self.tree.delete(item)
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        root_text = os.path.basename(self.project_root) or self.project_root
        root_node = self.tree.insert("", "end", text=root_text, open=True, values=[self.project_root])
        self._populate_tree(root_node, self.project_root)

    def _populate_tree(self, parent, path):
        try:
            items = sorted(os.listdir(path))
        except Exception as e:
            self.log(f"Error reading directory {path}: {e}")
            return
        for item in items:
            abspath = os.path.join(path, item)
            node = self.tree.insert(parent, "end", text=item, open=False, values=[abspath])
            if os.path.isdir(abspath):
                self._populate_tree(node, abspath)


if __name__ == "__main__":
    app = App()
    app.mainloop()
