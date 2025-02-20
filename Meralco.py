import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont, csv, json, os
from datetime import datetime as dt

# Global variables for Sub-Metering panels and the bill rate:
sub_detail_vars_global = None
sub_bottom_vars = None
sub_update_top_consumption = None
sub_update_sub = None
global_bill_rate = 0  # Stores "Rate This Month" from the Bill Detail tab


# --- Common Event Handler ---
def on_enter(event):
    widget = event.widget
    text = widget.get().strip()
    try:
        value = float(text.replace(",", ""))
        formatted = f"{value:,.2f}"
        widget.delete(0, tk.END)
        widget.insert(0, formatted)
    except ValueError:
        widget.event_generate("<FocusOut>")
    next_widget = widget.tk_focusNext()
    if next_widget:
        next_widget.focus_set()
    return "break"


# --- Utility Classes and Functions ---
class CreateToolTip:
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)
        self.top = None

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.top = tk.Toplevel(self.widget)
        self.top.overrideredirect(True)
        self.top.geometry(f"+{x}+{y}")
        tk.Label(self.top,
                 text=self.text,
                 justify='left',
                 background="#ffffe0",
                 relief='solid',
                 borderwidth=1,
                 font=("tahoma", "8", "normal")
                 ).pack(ipadx=1)

    def leave(self, event=None):
        if self.top:
            self.top.destroy()


def convert_date_strvar(event, var):
    val = var.get().strip()
    if not val:
        return
    norm = val.replace("-", "/").replace(".", "/").replace(" ", "/")
    try:
        parsed = dt.strptime(norm, "%d/%m/%Y")
    except ValueError:
        try:
            parsed = dt.strptime(norm, "%d/%m/%y")
        except ValueError:
            return
    var.set(parsed.strftime("%d-%b-%Y"))


def format_combo_date(var):
    value = var.get().strip()
    if value:
        norm = value.replace("-", "/").replace(".", "/").replace(" ", "/")
        try:
            parsed = dt.strptime(norm, "%d/%m/%Y")
        except ValueError:
            try:
                parsed = dt.strptime(norm, "%d/%m/%y")
            except ValueError:
                return
        var.set(parsed.strftime("%d-%b-%Y"))


def load_data(fn):
    left = {}
    with open(fn, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not any(cell.strip() for cell in row):
                continue
            left[row[0]] = row[1]
    return left, [], []


def load_specific_values(fn):
    with open(fn, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    try:
        prev = rows[4][1]
    except:
        prev = "0"
    try:
        curr = rows[6][1]
    except:
        curr = "0"
    try:
        tot = rows[7][1]
    except:
        try:
            tot = str(float(curr.replace(",", "")) - float(prev.replace(",", "")))
        except:
            tot = "0"
    return prev, curr, tot


# --- Bill Details Tab ---
def setup_gui(container):
    global global_bill_rate
    left, _, _ = load_data("bill_detail.csv")
    p, c, t = load_specific_values("bill_detail.csv")
    left["Previous kWh Reading"] = p
    left["Current kWh Reading"] = c
    left["Total Actual Consumption (kWh)"] = ""
    fields = [
        ("Consumer Name", 0),
        ("Account Number (CAN)", 1),
        ("Electric Meter Number", 2),
        ("Billing Period From", 3),
        ("Previous kWh Reading", 4),
        ("Billing Period Up To", 5),
        ("Current kWh Reading", 6),
        ("Total Actual Consumption (kWh)", 7),
        ("Rate This Month", 8),
        ("TOTAL Bill", 9)
    ]
    date_fields = ["Billing Period From", "Billing Period Up To"]
    form_frame = ttk.Frame(container, padding=10)
    form_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)
    field_vars = {}
    for f, _ in fields:
        field_vars[f] = tk.StringVar(value=left.get(f, ""))
    for f, r in fields:
        ttk.Label(form_frame, text=f).grid(row=r, column=0, sticky="w", padx=2, pady=2)
        state = "readonly" if f == "Total Actual Consumption (kWh)" else "normal"
        ent = ttk.Entry(form_frame, textvariable=field_vars[f], state=state)
        if f in date_fields:
            ent.bind("<FocusOut>", lambda e, var=field_vars[f]: convert_date_strvar(e, var))
        w = max(20, len(field_vars[f].get()) + 2)
        ent.config(width=w)
        field_vars[f].trace_add("write",
                                lambda *args, e=ent, var=field_vars[f]: e.config(width=max(20, len(var.get()) + 2)))
        ent.grid(row=r, column=1, sticky="ew", padx=2, pady=2)
        if f in date_fields:
            hlp = ttk.Label(form_frame, text="?", foreground="blue", cursor="question_arrow")
            hlp.grid(row=r, column=2, padx=2, pady=2, sticky="w")
            CreateToolTip(hlp, text="Enter date in format: DD/MM/YYYY")
        if state != "readonly":
            ent.bind("<Return>", on_enter)

    def update_consumption(*args):
        global global_bill_rate
        try:
            prev_val = float(field_vars["Previous kWh Reading"].get().replace(",", ""))
        except:
            prev_val = 0
        try:
            curr_val = float(field_vars["Current kWh Reading"].get().replace(",", ""))
        except:
            curr_val = 0
        consumption = curr_val - prev_val
        field_vars["Total Actual Consumption (kWh)"].set(f"{consumption:.2f}" if consumption != 0 else "")
        try:
            global_bill_rate = float(field_vars["Rate This Month"].get().replace(",", ""))
        except:
            global_bill_rate = 0

    field_vars["Previous kWh Reading"].trace_add("write", update_consumption)
    field_vars["Current kWh Reading"].trace_add("write", update_consumption)
    update_consumption()
    footer = ttk.Frame(container)
    footer.grid(row=1, column=0, sticky="w", padx=5, pady=5)

    def load_file():
        fn = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
        if fn:
            try:
                with open(fn, newline="", encoding="utf-8") as cf:
                    details = {row[0].strip(): row[1].strip() for row in csv.reader(cf) if len(row) >= 2}
                for f, var in field_vars.items():
                    if f in details:
                        var.set(details[f])
                update_consumption()
                global sub_detail_vars_global, sub_update_top_consumption
                if sub_detail_vars_global:
                    for key in sub_detail_vars_global:
                        if key in details:
                            sub_detail_vars_global[key].set(details[key])
                    if sub_update_top_consumption:
                        sub_update_top_consumption()
                messagebox.showinfo("Load File", "File loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def save_csv():
        for f, _ in fields:
            if not field_vars[f].get().strip():
                messagebox.showerror("Save CSV", f"Field '{f}' cannot be empty.")
                return
        rows = [[f, field_vars[f].get()] for f, _ in fields]
        consumer = rows[0][1] if rows[0][1] else "BillDetails"
        period_from = rows[3][1] if len(rows) > 3 else "From"
        period_to = rows[5][1] if len(rows) > 5 else "To"
        fn = f"{consumer}_{period_from}_{period_to}.csv".replace(" ", "_")
        save_dir = r"C:\Users\user\PycharmProjects\Utilities\Billing"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        full_path = os.path.join(save_dir, fn)
        try:
            with open(full_path, "w", newline="", encoding="utf-8") as cf:
                csv.writer(cf).writerows(rows)
            messagebox.showinfo("Save CSV", f"Saved as:\n{full_path}")
        except Exception as e:
            messagebox.showerror("Save CSV", f"Failed to save:\n{e}")

    ttk.Button(footer, text="Load File", command=load_file).pack(side="left", padx=5)
    ttk.Button(footer, text="Save as CSV", command=save_csv).pack(side="left", padx=5)


# --- Sub-Metering Tab ---
def setup_sub_metering(container):
    global sub_detail_vars_global, sub_bottom_vars, sub_update_top_consumption, sub_update_sub, global_bill_rate
    container.columnconfigure(0, weight=1)
    details_frame = ttk.Frame(container, padding=5, relief="ridge")
    details_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    left, _, _ = load_data("bill_detail.csv")
    p, c, t = load_specific_values("bill_detail.csv")
    left["Previous kWh Reading"] = p
    left["Current kWh Reading"] = c
    left["Total Actual Consumption (kWh)"] = ""
    fields_top = [
        ("Consumer Name", 0),
        ("Account Number (CAN)", 1),
        ("Electric Meter Number", 2),
        ("Billing Period From", 3),
        ("Previous kWh Reading", 4),
        ("Billing Period Up To", 5),
        ("Current kWh Reading", 6),
        ("Total Actual Consumption (kWh)", 7),
        ("Rate This Month", 8),
        ("TOTAL Bill", 9)
    ]
    date_fields_top = ["Billing Period From", "Billing Period Up To"]
    detail_vars = {}
    for f, r in fields_top:
        detail_vars[f] = tk.StringVar(value=left.get(f, ""))
        ttk.Label(details_frame, text=f).grid(row=r, column=0, sticky="w", padx=2, pady=2)
        state = "readonly" if f == "Total Actual Consumption (kWh)" else "normal"
        ent = ttk.Entry(details_frame, textvariable=detail_vars[f], state=state, width=30)
        if f in date_fields_top:
            ent.bind("<FocusOut>", lambda e, var=detail_vars[f]: convert_date_strvar(e, var))
        ent.grid(row=r, column=1, sticky="w", padx=2, pady=2)
        if state != "readonly":
            ent.bind("<Return>", on_enter)

    def update_top_consumption(*args):
        try:
            prev_val = float(detail_vars["Previous kWh Reading"].get().replace(",", ""))
        except:
            prev_val = 0
        try:
            curr_val = float(detail_vars["Current kWh Reading"].get().replace(",", ""))
        except:
            curr_val = 0
        cons = curr_val - prev_val
        detail_vars["Total Actual Consumption (kWh)"].set(f"{cons:.2f}" if cons != 0 else "")

    detail_vars["Previous kWh Reading"].trace_add("write", update_top_consumption)
    detail_vars["Current kWh Reading"].trace_add("write", update_top_consumption)
    update_top_consumption()
    sub_detail_vars_global = detail_vars

    # Authorized entry
    auth_frame = ttk.Frame(container, padding=5)
    auth_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    ttk.Label(auth_frame, text="Authorized:").grid(row=0, column=0, sticky="w")
    auth_entry = ttk.Entry(auth_frame, width=40)
    auth_entry.grid(row=0, column=1, sticky="w", padx=5)
    auth_frame.columnconfigure(1, weight=1)

    fields_bottom = [("Billing Period From", 0),
                     ("Previous kWh Reading", 1),
                     ("Billing Period Up To", 2),
                     ("Current kWh Reading", 3)]
    sub_vars = {f: tk.StringVar(value="") for f, _ in fields_bottom}
    sub_frame = ttk.Frame(container, padding=5, relief="groove")
    sub_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
    for f, r in fields_bottom:
        ttk.Label(sub_frame, text=f).grid(row=r, column=0, sticky="w", padx=2, pady=2)
        ent = ttk.Entry(sub_frame, textvariable=sub_vars[f], width=30)
        if f in {"Billing Period From", "Billing Period Up To"}:
            ent.bind("<FocusOut>", lambda e, var=sub_vars[f]: convert_date_strvar(e, var))
        ent.grid(row=r, column=1, sticky="w", padx=2, pady=2)
        ent.bind("<Return>", on_enter)
    total_consumption = tk.StringVar(value="0")
    total_amount = tk.StringVar(value="0")
    ttk.Label(sub_frame, text="Total Actual Consumption (kWh):").grid(row=4, column=0, sticky="w", padx=2, pady=2)
    ttk.Label(sub_frame, textvariable=total_consumption, width=30, relief="sunken").grid(row=4, column=1, sticky="w",
                                                                                         padx=2, pady=2)
    ttk.Label(sub_frame, text="Total Amount:").grid(row=5, column=0, sticky="w", padx=2, pady=2)
    ttk.Label(sub_frame, textvariable=total_amount, width=30, relief="sunken").grid(row=5, column=1, sticky="w", padx=2,
                                                                                    pady=2)

    def update_sub(*args):
        try:
            prev_val = float(sub_vars["Previous kWh Reading"].get().replace(",", ""))
        except:
            prev_val = 0
        try:
            curr_val = float(sub_vars["Current kWh Reading"].get().replace(",", ""))
        except:
            curr_val = 0
        cons = curr_val - prev_val
        total_consumption.set(f"{cons:.2f}")
        global global_bill_rate
        total_amount.set(f"{cons * global_bill_rate:.2f}")

    sub_vars["Previous kWh Reading"].trace_add("write", update_sub)
    sub_vars["Current kWh Reading"].trace_add("write", update_sub)
    update_sub()
    sub_bottom_vars = sub_vars
    sub_update_top_consumption = update_top_consumption
    sub_update_sub = update_sub

    # Filtering frame and comboboxes for JSON records
    footer_sub = ttk.Frame(container, padding=5)
    footer_sub.grid(row=3, column=0, sticky="w", padx=5, pady=5)
    filter_frame = ttk.Frame(footer_sub)
    filter_frame.pack(side="left", padx=5)

    # Create StringVars for comboboxes
    filekey_var = tk.StringVar()
    auth_var = tk.StringVar()
    bpf_var = tk.StringVar()
    bpu_var = tk.StringVar()

    ttk.Label(filter_frame, text="FileKey:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
    filekey_combo = ttk.Combobox(filter_frame, textvariable=filekey_var, values=[], state="normal", width=60)
    filekey_combo.grid(row=0, column=1, columnspan=3, padx=2, pady=2, sticky="w")

    ttk.Label(filter_frame, text="Auth:").grid(row=1, column=0, padx=2, pady=2, sticky="w")
    auth_combo = ttk.Combobox(filter_frame, textvariable=auth_var, values=[], state="normal", width=12)
    auth_combo.grid(row=1, column=1, padx=2, pady=2, sticky="w")

    def on_auth_selected(event):
        selected = auth_combo.get().strip()
        auth_entry.delete(0, tk.END)
        auth_entry.insert(0, selected)

    auth_combo.bind("<<ComboboxSelected>>", on_auth_selected)

    ttk.Label(filter_frame, text="From:").grid(row=1, column=2, padx=2, pady=2, sticky="w")
    bpf_combo = ttk.Combobox(filter_frame, textvariable=bpf_var, values=[], state="normal", width=12)
    bpf_combo.grid(row=1, column=3, padx=2, pady=2, sticky="w")
    ttk.Label(filter_frame, text="Up To:").grid(row=1, column=4, padx=2, pady=2, sticky="w")
    bpu_combo = ttk.Combobox(filter_frame, textvariable=bpu_var, values=[], state="normal", width=12)
    bpu_combo.grid(row=1, column=5, padx=2, pady=2, sticky="w")

    bpf_combo.bind("<Return>", lambda e: (format_combo_date(bpf_var), e.widget.tk_focusNext().focus_set(), "break"))
    bpf_combo.bind("<FocusOut>", lambda e: format_combo_date(bpf_var))
    bpu_combo.bind("<Return>", lambda e: (format_combo_date(bpu_var), e.widget.tk_focusNext().focus_set(), "break"))
    bpu_combo.bind("<FocusOut>", lambda e: format_combo_date(bpu_var))

    def populate_filters():
        try:
            with open("submeter.json", "r", encoding="utf-8") as jf:
                data = json.load(jf)
            filekey_values = set()
            auth_values = set()
            bpf_values = set()
            bpu_values = set()
            if isinstance(data, list):
                for rec in data:
                    fk = rec.get("FileKey", "")
                    if fk:
                        filekey_values.add(fk)
                    sub_data = rec.get("Sub_Meter", {})
                    auth_val = sub_data.get("Auth", "")
                    if auth_val:
                        auth_values.add(auth_val)
                    bpf_val = sub_data.get("Billing Period From", "")
                    if bpf_val:
                        bpf_values.add(bpf_val)
                    bpu_val = sub_data.get("Billing Period Up To", "")
                    if bpu_val:
                        bpu_values.add(bpu_val)
            else:
                fk = data.get("FileKey", "")
                if fk:
                    filekey_values.add(fk)
                sub_data = data.get("Sub_Meter", {})
                auth_val = sub_data.get("Auth", "")
                if auth_val:
                    auth_values.add(auth_val)
                bpf_val = sub_data.get("Billing Period From", "")
                if bpf_val:
                    bpf_values.add(bpf_val)
                bpu_val = sub_data.get("Billing Period Up To", "")
                if bpu_val:
                    bpu_values.add(bpu_val)
            filekey_list = sorted(filekey_values)
            auth_list = sorted(auth_values)
            bpf_list = sorted(bpf_values)
            bpu_list = sorted(bpu_values)
            filekey_combo['values'] = filekey_list
            auth_combo['values'] = auth_list
            bpf_combo['values'] = bpf_list
            bpu_combo['values'] = bpu_list
            if filekey_list:
                filekey_combo.set(filekey_list[0])
            if auth_list:
                auth_combo.set(auth_list[0])
            if bpf_list:
                bpf_combo.set(bpf_list[0])
            if bpu_list:
                bpu_combo.set(bpu_list[0])
        except Exception as e:
            print("Error populating filters:", e)
            filekey_combo['values'] = []
            auth_combo['values'] = []
            bpf_combo['values'] = []
            bpu_combo['values'] = []

    def load_json():
        f_filter = filekey_combo.get().strip()
        a_filter = auth_combo.get().strip()
        bpf_filter = bpf_combo.get().strip()
        bpu_filter = bpu_combo.get().strip()
        if not (f_filter and a_filter and bpf_filter and bpu_filter):
            messagebox.showerror("Load JSON", "All filter fields must be filled.")
            return
        try:
            with open("submeter.json", "r", encoding="utf-8") as jf:
                data = json.load(jf)
            record = None
            if isinstance(data, list):
                for rec in data:
                    if (rec.get("FileKey", "") == f_filter and
                            rec.get("Sub_Meter", {}).get("Auth", "") == a_filter and
                            rec.get("Sub_Meter", {}).get("Billing Period From", "") == bpf_filter and
                            rec.get("Sub_Meter", {}).get("Billing Period Up To", "") == bpu_filter):
                        record = rec
                        break
            else:
                if (data.get("FileKey", "") == f_filter and
                        data.get("Sub_Meter", {}).get("Auth", "") == a_filter and
                        data.get("Sub_Meter", {}).get("Billing Period From", "") == bpf_filter and
                        data.get("Sub_Meter", {}).get("Billing Period Up To", "") == bpu_filter):
                    record = data
            if record is None:
                messagebox.showinfo("Load JSON", "No record matches the provided filters.")
                return
            sub_data = record.get("Sub_Meter", {})
            for key in sub_vars:
                if key in sub_data:
                    sub_vars[key].set(sub_data[key])
            total_consumption.set(sub_data.get("Total Actual Consumption (kWh)", ""))
            total_amount.set(sub_data.get("Total Amount", ""))
            auth_entry.delete(0, tk.END)
            auth_entry.insert(0, sub_data.get("Auth", ""))
            messagebox.showinfo("Load JSON", "Record loaded successfully.")
        except Exception as e:
            messagebox.showerror("Load JSON", f"Error loading JSON:\n{e}")

    def save_sub_metering():
        sub_meter_data = {
            "Auth": auth_entry.get(),
            "Billing Period From": sub_vars["Billing Period From"].get(),
            "Previous kWh Reading": sub_vars["Previous kWh Reading"].get(),
            "Billing Period Up To": sub_vars["Billing Period Up To"].get(),
            "Current kWh Reading": sub_vars["Current kWh Reading"].get(),
            "Total Actual Consumption (kWh)": total_consumption.get(),
            "Total Amount": total_amount.get()
        }
        file_key = (detail_vars["Consumer Name"].get() + "_" +
                    detail_vars["Billing Period From"].get() + "_" +
                    detail_vars["Billing Period Up To"].get())
        new_record = {
            "FileKey": file_key,
            "Sub_Meter": sub_meter_data
        }
        try:
            records = []
            if os.path.exists("submeter.json"):
                with open("submeter.json", "r", encoding="utf-8") as jf:
                    try:
                        data = json.load(jf)
                        if isinstance(data, list):
                            records = data
                        else:
                            records = [data]
                    except Exception:
                        records = []
            records.append(new_record)
            with open("submeter.json", "w", encoding="utf-8") as jf:
                json.dump(records, jf, indent=4)
            messagebox.showinfo("Save", "Record appended to submeter.json")
            populate_filters()
            filekey_combo.set(new_record["FileKey"])
            auth_combo.set(new_record["Sub_Meter"]["Auth"])
            bpf_combo.set(new_record["Sub_Meter"]["Billing Period From"])
            bpu_combo.set(new_record["Sub_Meter"]["Billing Period Up To"])
            load_json()
        except Exception as e:
            messagebox.showerror("Save", f"Failed to save:\n{e}")

    loadjson_btn = ttk.Button(filter_frame, text="Load JSON", command=load_json)
    loadjson_btn.grid(row=1, column=6, padx=2, pady=2, sticky="w")
    save_btn = ttk.Button(filter_frame, text="Save", command=save_sub_metering)
    save_btn.grid(row=1, column=7, padx=2, pady=2, sticky="w")

    # --- "Copy" Button (Text) ---
    def copy_sub_metering_data():
        lines = []
        lines.append("=== Top Details ===")
        top_items = {}
        for key, var in sub_detail_vars_global.items():
            top_items[key] = var.get()
        top_items["Authorized"] = auth_entry.get()
        max_key_len = max(len(k) for k in top_items.keys())
        for key, value in top_items.items():
            lines.append(f"{key:<{max_key_len}} : {value}")
        lines.append("")
        lines.append("=== Sub-Metering Details ===")
        sub_items = {}
        for key, var in sub_vars.items():
            sub_items[key] = var.get()
        sub_items["Total Actual Consumption (kWh)"] = total_consumption.get()
        sub_items["Total Amount"] = total_amount.get()
        max_key_len_sub = max(len(k) for k in sub_items.keys())
        for key, value in sub_items.items():
            lines.append(f"{key:<{max_key_len_sub}} : {value}")
        data_str = "\n".join(lines)
        container.clipboard_clear()
        container.clipboard_append(data_str)
        messagebox.showinfo("Copy", "Sub-Metering data copied to clipboard.")

    copy_btn = ttk.Button(filter_frame, text="Copy", command=copy_sub_metering_data)
    copy_btn.grid(row=1, column=8, padx=2, pady=2, sticky="w")

    # --- "Copy as Image" Button ---
    def copy_sub_metering_as_image():
        import io
        try:
            import win32clipboard
        except ImportError:
            messagebox.showerror("Copy as Image", "pywin32 is required for copying images to the clipboard.")
            return

        # --- Build the text for each section ---

        # Top Details section
        top_heading = "=== Top Details ==="
        top_items = {key: var.get() for key, var in sub_detail_vars_global.items()}
        top_items["Authorized"] = auth_entry.get()
        max_key_len_top = max(len(k) for k in top_items.keys())
        top_lines = [f"{key:<{max_key_len_top}} : {value}" for key, value in top_items.items()]

        # Sub-Metering section
        sub_heading = "=== Sub-Metering Details ==="
        sub_items = {key: var.get() for key, var in sub_vars.items()}
        sub_items["Total Actual Consumption (kWh)"] = total_consumption.get()
        sub_items["Total Amount"] = total_amount.get()
        max_key_len_sub = max(len(k) for k in sub_items.keys())
        sub_lines = [f"{key:<{max_key_len_sub}} : {value}" for key, value in sub_items.items()]

        # Combine the sections with a blank line between them
        lines = []
        lines.append(top_heading)
        lines.extend(top_lines)
        lines.append("")  # Blank line for spacing
        lines.append(sub_heading)
        lines.extend(sub_lines)

        # --- Set up font and color ---
        from PIL import Image, ImageDraw, ImageFont
        font_size = 20
        try:
            # Use a monospaced font for perfect alignment (Courier New)
            font = ImageFont.truetype("Courier New.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
        background_color = "#FFFFFF"  # White background
        text_color = "#000000"  # Black text

        # --- Calculate the required image size ---
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        max_line_width = 0
        line_sizes = []
        for line in lines:
            # Get the size of each line using textbbox
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            line_sizes.append((w, h))
            if w > max_line_width:
                max_line_width = w

        line_spacing = 10  # Extra space between lines
        total_height = sum(h for _, h in line_sizes) + line_spacing * (len(lines) - 1)

        padding = 20
        img_width = max_line_width + 2 * padding
        img_height = total_height + 2 * padding

        # --- Create the final image and draw the text ---
        img = Image.new("RGB", (img_width, img_height), color=background_color)
        draw = ImageDraw.Draw(img)
        y = padding
        for i, line in enumerate(lines):
            w, h = line_sizes[i]
            # If the line is a section heading (starts and ends with ===), center it.
            if line.startswith("===") and line.endswith("==="):
                x = padding + (max_line_width - w) // 2
            else:
                x = padding
            draw.text((x, y), line, fill=text_color, font=font)
            y += h + line_spacing

        # --- Save the image to a bytes buffer and copy it to the clipboard ---
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Skip BMP header bytes

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            messagebox.showinfo("Copy as Image", "Sub-Metering data copied as image to clipboard.")
        except Exception as e:
            messagebox.showerror("Copy as Image", f"Failed to copy image to clipboard:\n{e}")

    copy_image_btn = ttk.Button(filter_frame, text="Copy as Image", command=copy_sub_metering_as_image)
    copy_image_btn.grid(row=1, column=9, padx=2, pady=2, sticky="w")

    populate_filters()


# --- Application Startup ---
def start_app():
    root = tk.Tk()
    root.title("Bill Detail")
    root.withdraw()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    splash_width, splash_height = 150, 80
    splash_x = (sw - splash_width) // 2
    splash_y = (sh - splash_height) // 2
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry(f"{splash_width}x{splash_height}+{splash_x}+{splash_y}")
    splash.attributes('-topmost', True)
    ttk.Label(splash, text="Loading...", font=("Arial", 16)).pack(expand=True)

    def show_main():
        splash.destroy()
        default_width, default_height = 950, 600
        x = (sw - default_width) // 2
        y = (sh - default_height) // 2
        root.geometry(f"{default_width}x{default_height}+{x}+{y}")
        root.resizable(True, True)
        root.attributes('-topmost', True)
        root.deiconify()

    root.after(3000, show_main)
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)
    bd = ttk.Frame(nb)
    nb.add(bd, text="Bill Detail")
    setup_gui(bd)
    sm = ttk.Frame(nb)
    nb.add(sm, text="Sub-Metering")
    setup_sub_metering(sm)
    root.mainloop()


if __name__ == "__main__":
    start_app()
