import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import re
from jupyter_dash import JupyterDash  # Use JupyterDash instead of dash.Dash
import dash
from dash import html
import dash_cytoscape as cyto
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Tk, Label, Button, filedialog, messagebox
from tkinter.filedialog import asksaveasfilename
from fpdf import FPDF # type: ignore
from graphviz import Digraph
from tkinter import messagebox, filedialog, ttk

def clean_column_name(name):
    # Convert to lowercase
    name = name.lower()
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove special characters (except underscores)
    name = re.sub(r'[^\w\s]', '', name)
    return name

# Function to process columns and split rows
def process_column(df, column_name):
    new_rows = []
    for index, row in df.iterrows():
         # Ensure the column values are strings
        value = str(row[column_name])
        # Split the values in the column based on spaces and strip any extra spaces
        values = [val.strip() for val in row[column_name].split() if val.strip()]
        
        # If there's more than one value, create a new row for each value
        if len(values) > 1:
            for value in values:
                new_row = row.copy()  # Copy the original row
                new_row[column_name] = value  # Update with the trimmed text
                new_rows.append(new_row)
        else:
            # Keep the original row if there's only one value (no split needed)
            new_rows.append(row)
    return pd.DataFrame(new_rows)

# Function to clean up repeated account numbers
def clean_account_no(value):
    if pd.isna(value):
        return value  # Return NaN if the value is NaN
    # Split the account number by space
    parts = value.split()
    print(parts)
    # Check if all the parts are the same
    if len(parts) > 1 and all(part == parts[0] for part in parts):
        print(99)
        # If they are the same, return only one instance
        return parts[0]
    # If not, return the original value (no change needed)
    return value

def clean_column_data(series):
    # Remove special characters and trim spaces
    series = series.apply(lambda x: re.sub(r'[^\w\s]', '', str(x)).strip() if pd.notna(x) else x)
    return series

def format_amount_indian(amount):
    # Convert the amount to a string and remove any existing commas
    amount_str = str(amount).replace(',', '')
    
    # Check if the number has more than 3 digits
    if len(amount_str) > 3:
        # Get the last 3 digits
        last_three = amount_str[-3:]
        # Get the remaining digits
        remaining = amount_str[:-3]
        # Group digits in thousands (group of 2 after the first group of 3)
        grouped = [remaining[max(0, i-2):i] for i in range(len(remaining), 0, -2)]
        # Reverse and join the grouped digits with commas
        formatted_remaining = ','.join(grouped[::-1])
        # Concatenate the formatted remaining part with the last three digits
        formatted_amount = f'{formatted_remaining},{last_three}'
    else:
        # For amounts less than or equal to 999, no formatting is needed
        formatted_amount = amount_str

    return formatted_amount

def split_text(text, max_width=30):
    """
    Split the text into lines, so that no line exceeds max_width characters.
    """
    words = text.split(' ')
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > max_width:  # +1 for space
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1  # +1 for space
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '<BR/>'.join(lines)

# Function to process the Excel file and generate PDF
def process_excel(excel_file):
    try:
        df = pd.read_excel(excel_file, dtype= str)
        print(excel_file)
        new_columns = [
            'S No.', 'acknowledgement_no', 'transaction_id', 'Layer', 'to_account_no', 
            'Action Taken by Bank/ (Wallet /PG/PA)/ Merchant// Insurance', 
            'Bank/ (Wallet /PG/PA)/ Merchant / Insurance', 'from_account_no', 'Ifsc Code', 
            'Cheque No', 'MID', 'TID', 'Approval Code', 'Merchant Name', 'Transaction Date', 
            'utr_number', 'amount', 'Reference No', 'Remarks', 'Date of Action', 
            'Action Taken By bank', 'Action Taken Name', 'Action Taken By Email', 
            'Branch Location', 'Branch Manager Name & Contact Details'
        ]
        # Get the current number of columns in the Excel file
        num_current_columns = len(df.columns)
        num_new_columns = len(new_columns)

        # Adjust new columns if necessary (truncate or extend)
        if num_current_columns > num_new_columns:
            # If more columns in the Excel, extend new_columns with 'Unnamed' columns
            extra_columns = [f"Unnamed {i+1}" for i in range(num_current_columns - num_new_columns)]
            adjusted_columns = new_columns + extra_columns
        else:
            # If fewer columns in the Excel, truncate the new_columns to match
            adjusted_columns = new_columns[:num_current_columns]

        # Replace the column headers with the adjusted columns
        df.columns = adjusted_columns

        df.columns = [clean_column_name(col) for col in df.columns]
        # Create a list to hold new rows
        new_rows = []
        # List of columns where you want to append '@'
        columns_to_append = ['acknowledgement_no','transaction_id','to_account_no', 'from_account_no','utr_number']

        # Prepend '@' to every value in the specified columns
        for column in columns_to_append:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: '`' + str(x) if pd.notnull(x) else x)
        print("column append complete")
        # List of columns to process
        columns_to_process = ['transaction_id', 'from_account_no'] # add to account no if there are dual records in it

        # Ensure columns are in string format
        for col in columns_to_process:
            if col in df.columns:
                df[col] = df[col].astype(str)
        print("column process completed")
        # Use str.replace() to remove the "[ Reported X times ]" pattern
        df['from_account_no'] = df['from_account_no'].str.replace(r'\[.*\]', '', regex=True)

        # Strip any extra spaces that might be left after removing the text
        df['from_account_no'] = df['from_account_no'].str.strip() 
        # Process each column and merge results
        processed_dfs = [process_column(df, col) for col in columns_to_process]
        # Merge all processed DataFrames
        final_df = pd.concat(processed_dfs, ignore_index=True)

        # Display the updated DataFrame to verify
        #print(final_df.head())

        # Save the modified DataFrame to a new CSV file if needed
        #final_df.to_csv('D:\\test\\excel2_Cleaned.csv', index=False)
        df = final_df
        df = df.drop_duplicates(keep='first')
        df['layer'] = df['layer'].astype(int)
        df = df.drop(['s_no'],axis=1)
        # Remove text within square brackets
        df['to_account_no'] = df['to_account_no'].str.replace(r'\s*\[.*?\]', '', regex=True)
        df['from_account_no'] = df['from_account_no'].str.replace(r'\s*\[.*?\]', '', regex=True)
        columns_to_clean = [
            'acknowledgement_no', 'transaction_id', 'layer',
            'from_account_no', 'utr_number', 'amount','to_account_no'
        ]
        # Apply the cleaning function to each specified column
        for col in columns_to_clean:
            if col in df.columns:
                df[col] = clean_column_data(df[col])
        print("Column clean completed")
        
        columns_to_update = ['to_account_no', 'from_account_no', 'ifsc_code', 'utr_number']

        # Replace empty strings and null values with 'NaaN'
        df[columns_to_update] = df[columns_to_update].replace('', 'NaaN').fillna('NaaN')
        df.isnull().sum() + (df == '').sum()
        df['layer'] = pd.to_numeric(df['layer'], errors='coerce')
        print(df['layer'].unique())
        df['reference_no'] = df['reference_no'].astype(object)
        print(df.info())
        ackno = df['acknowledgement_no'].unique()
        ackname = 'Transaction Flow Graph For (Ack No): ' + str(ackno)
        print(ackname)
        df['to_account_no'] = df['to_account_no'].apply(clean_account_no)
        df['from_account_no'] = df['from_account_no'].apply(clean_account_no)
        df = df.drop_duplicates(keep='first')
        #df.to_csv('D:\\test\\exegen_Cleaned.csv', index=False)
        # Create a directed graph using Graphviz with hierarchical layout
        dot = Digraph()

        # Set the graph layout to be hierarchical (left-right) and use L-shaped edges
        dot.attr(rankdir='LR', splines='ortho')

        # Get the distinct unique layers from the dataset
        layers = sorted(df['layer'].unique())

        # Add a title at the top
        dot.attr(label=ackname, fontsize='20', labelloc='t', fontcolor='black')

        with dot.subgraph(name='cluster_legend') as legend:
            legend.attr(label="Legend", fontsize='14', style='dashed', rank='source')  # Use rank='source' to push it to the top
            legend.node('withdrawal', label="Withdrawal (Blue)", shape='box', color='#0000ff')
            legend.node('on_hold', label="On Hold (Red)", shape='box', color='#ff0000')
            legend.node('normal', label="Normal Transaction (Black)", shape='box', color='black')
            legend.node('legend', label= f"""<<TABLE BORDER="0" CELLBORDER="0">
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="orange" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>Account No. (Orange)</TD>
                </TR>
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="#036100" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>Transaction ID (Green)</TD>
                </TR>
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="blue" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>IFSC_code (Black)</TD>
                </TR>
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="red" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>Amount (Red)</TD>
                </TR>
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="#6b3700" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>Transaction Date (Brown)</TD>
                </TR>
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="blue" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>Action Taken (Blue)</TD>
                </TR>
                <TR>
                    <TD><TABLE BORDER="0" CELLBORDER="0"><TR><TD BGCOLOR="black" WIDTH="20" HEIGHT="20"></TD></TR></TABLE></TD>
                    <TD>Remarks (Black)</TD>
                </TR>
            </TABLE>>""", shape='plaintext')  # Ensure this is in the correct format

        # Initialize the previous layer nodes (starting with an empty set)
        previous_layer_nodes = None

        # Set to track already added edges to avoid duplicates
        added_edges = set()

        # Loop through each distinct layer in the dataset
        for idx, layer in enumerate(layers):
            
            # Filter the records for the current layer
            layer_records = df[df['layer'] == layer]

            # Select relevant columns from the filtered dataset
            layer_nodes = layer_records[['from_account_no', 'to_account_no', 'transaction_id', 'transaction_date', 'ifsc_code', 'amount', 'remarks', 'action_taken_by_bank_wallet_pgpa_merchant_insurance']]
            
            # Add nodes for the current layer (from_account_no as nodes, with rectangular shape)
            for _, row in layer_nodes.iterrows():
                # Default color is black
                node_color = 'black'
                
                # Change node color if 'WITHDRAWAL' is in action_taken_by_bank_wallet_pgpa_merchant_insurance
                if 'WITHDRAWAL' in row['action_taken_by_bank_wallet_pgpa_merchant_insurance'].upper():
                    node_color = '#0000ff'  # Blue color for withdrawal
                    
                # Change node color if 'ON HOLD' is in action_taken_by_bank_wallet_pgpa_merchant_insurance
                elif 'ON HOLD' in row['action_taken_by_bank_wallet_pgpa_merchant_insurance'].upper():
                    node_color = '#ff0000'  # Red color for on hold
                # Create the HTML-like label for each node with colored text
                # Create the HTML-like label for each node with colored text
                label = f"""<<TABLE BORDER="0" CELLBORDER="0">
                    <TR><TD><FONT COLOR="orange" POINT-SIZE="12"><B>{row['from_account_no']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="#036100"><B>{row['transaction_id']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="blue"><B>{row['ifsc_code']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="red" POINT-SIZE="15"><B>{format_amount_indian(row['amount'])}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="#6b3700">{row['transaction_date']}</FONT></TD></TR>
                    <TR><TD><FONT COLOR="blue">{row['action_taken_by_bank_wallet_pgpa_merchant_insurance']}</FONT></TD></TR>
                </TABLE>>"""

                # Add node with the specific color and rectangular shape
                dot.node(
                    str(row['from_account_no']), 
                    label=label,
                    shape='box',
                    color=node_color
                )

                # Check for NaN in from_account_no
                if str(row['from_account_no']).upper() == "NAAN":
                    # Create a unique identifier for each NaN node based on its transaction details
                    nan_node_id = f"NaaN_{row['transaction_id']}"  # Unique ID for this specific NaaN transaction
                    node_color = '#cccccc'
                    if 'WITHDRAWAL' in row['action_taken_by_bank_wallet_pgpa_merchant_insurance'].upper():
                        node_color = '#0000ff'  # Blue color for withdrawal
                    
                    # Change node color if 'ON HOLD' is in action_taken_by_bank_wallet_pgpa_merchant_insurance
                    elif 'ON HOLD' in row['action_taken_by_bank_wallet_pgpa_merchant_insurance'].upper():
                        node_color = '#ff0000'  # Red color for on hold
                    remarks = split_text(row['remarks'], max_width=30) 
                    label = f"""<<TABLE BORDER="0" CELLBORDER="0">
                    <TR><TD><FONT COLOR="orange" POINT-SIZE="12"><B>{row['from_account_no']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="#036100"><B>{row['transaction_id']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="blue"><B>{row['ifsc_code']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="red" POINT-SIZE="15"><B>{format_amount_indian(row['amount'])}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="black">{row['transaction_date']}</FONT></TD></TR>
                    <TR><TD><FONT COLOR="#6b3700">{row['action_taken_by_bank_wallet_pgpa_merchant_insurance']}</FONT></TD></TR>
                    <TR><TD><FONT COLOR="black">{remarks}</FONT></TD></TR>
                </TABLE>>"""
                    dot.node(nan_node_id, label=label, shape='ellipse', color=node_color)

                    # Add an edge from the current node to the unique NaaN node
                    edge = (str(row['to_account_no']), nan_node_id)
                    if edge not in added_edges:
                        dot.edge(str(row['to_account_no']), nan_node_id)
                        added_edges.add(edge)

            # If this is not the first layer, add edges between the previous layer and the current one
            if previous_layer_nodes is not None:
                # Add edges based on "to_account_no" in the current layer matching "from_account_no" in the previous layer
                for _, row in layer_nodes.iterrows():
                    matching_previous_layer_nodes = previous_layer_nodes[previous_layer_nodes['from_account_no'] == row['to_account_no']]
                    
                    for _, prev_row in matching_previous_layer_nodes.iterrows():
                        # Create an identifier for the edge to check for duplicates
                        edge = (str(prev_row['from_account_no']), str(row['from_account_no']))
                        
                        # Add edge if it hasn't been added yet
                        if edge not in added_edges:
                            dot.edge(str(prev_row['from_account_no']), str(row['from_account_no']))
                            added_edges.add(edge)  # Track the added edge

            # Set the current layer as the previous layer for the next iteration
            previous_layer_nodes = layer_nodes

        # Save and view the graph (optional)
        dot.render('transaction_graph', format='png', cleanup=True)
        dot.view()

        messagebox.showinfo("Success", "PDF generated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Hardcoded username and password
USERNAME = "admin"
PASSWORD = "password123"
selected_file = None

def login():
    """Validate the username and password."""
    entered_username = username_entry.get()
    entered_password = password_entry.get()

    if entered_username == USERNAME and entered_password == PASSWORD:
        messagebox.showinfo("Login Success", "Welcome!")
        enable_buttons()  # Enable buttons after successful login
        login_frame.pack_forget()  # Hide login frame after successful login
        main_frame.pack(fill=tk.BOTH, expand=True)  # Show the main frame
    else:
        messagebox.showerror("Login Failed", "Incorrect Username or Password")

def enable_buttons():
    """Enable the Upload and Submit buttons after successful login."""
    btn_upload.config(state=tk.NORMAL)
    btn_process.config(state=tk.NORMAL)

def upload_file():
    """Function to select Excel file."""
    print("uploading file....")
    file_path = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        lbl_selected_file.config(text=file_path)
        global selected_file
        selected_file = file_path

def save_pdf():
    """Function to save the PDF."""
    if not selected_file:
        messagebox.showwarning("No File", "Please select an Excel file first.")
        return
    else:
        # Call your processing function here (assuming it exists)
        process_excel(selected_file)
         
import tkinter as tk
# Set up the Tkinter UI
root = tk.Tk()
root.title("Excel to PDF Processor")
root.geometry("400x300")

# Frame for Login
login_frame = ttk.Frame(root)
login_frame.pack(fill=tk.BOTH, expand=True)

# Username label and entry
ttk.Label(login_frame, text="Username:").pack(pady=5)
username_entry = ttk.Entry(login_frame)
username_entry.pack(pady=5)

# Password label and entry (password hidden)
ttk.Label(login_frame, text="Password:").pack(pady=5)
password_entry = ttk.Entry(login_frame, show="*")
password_entry.pack(pady=5)

# Login button
login_button = ttk.Button(login_frame, text="Login", command=login)
login_button.pack(pady=10)

# Frame for main application after login
main_frame = ttk.Frame(root)

# Selected file label
lbl_selected_file = ttk.Label(main_frame, text="No file selected", width=50)
lbl_selected_file.pack(pady=10)

# Upload button (initially disabled)
btn_upload = ttk.Button(main_frame, text="Upload Excel File", command=upload_file, state=tk.DISABLED)
btn_upload.pack(pady=5)

# Process and save button (initially disabled)
btn_process = ttk.Button(main_frame, text="Submit", command=save_pdf, state=tk.DISABLED)
btn_process.pack(pady=10)

# Run the Tkinter loop
root.mainloop()

