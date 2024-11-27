import pandas as pd
import re
from graphviz import Digraph
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkinter import filedialog
import logging
import os
from customtkinter import CTkTextbox

# In[80]:

LOG_FILE = "CII_application.log"
# Function to clean column names
def clean_column_name(name):
    # Convert to lowercase
    name = name.lower()
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove special characters (except underscores)
    name = re.sub(r'[^\w\s]', '', name)
    return name


# In[81]:


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


# In[82]:


# Function to clean data in a column
def clean_column_data(series):
    # Remove special characters and trim spaces
    series = series.apply(lambda x: re.sub(r'[^\w\s]', '', str(x)).strip() if pd.notna(x) else x)
    return series


# In[83]:


def clean_account_no(value):
    if pd.isna(value):
        return value  # Return NaN if the value is NaN
    # Split the account number by space
    parts = value.split()
    # Check if all the parts are the same
    if len(parts) > 1 and all(part == parts[0] for part in parts):
        # If they are the same, return only one instance
        return parts[0]
    # If not, return the original value (no change needed)
    return value


# In[84]:


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


# In[85]:


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


# In[ ]:

def graph_printing(new_df, ackname):    
# Initialize the Graphviz directed graph
    dot = Digraph(format='pdf')
    dot.attr(rankdir='LR', splines='ortho', nodesep='1.0', ranksep='1.5')  # Adjusted spacing between nodes and layers
    #dot.node('title', ackname, shape='plaintext', fontsize='40', fontcolor='blue')
    dot.attr(label=ackname, fontsize='30', labelloc='t', fontcolor='blue')
    # Set to keep track of unique nodes to avoid duplicates
    unique_nodes = set()

    # Dictionary to store the labels of nodes
    node_labels = {}

    # Create a dictionary to store accounts associated with each layer
    layer_accounts = {}

    # Dictionary to track edges and aggregate amounts for each from-to account pair
    edges_dict = {}

    try:
        # Loop through each unique layer with the specified action
        for i in new_df['layer'].unique():
            dt = new_df[(new_df['layer'] == i)]
            layer_records = pd.DataFrame(dt)

            # Filter the layer_nodes dataframe
            layer_nodes = layer_records[['from_account_no', 'to_account_no', 'amount', 'layer','utr_number','remarks','reported_info',
                                        'action_taken_by_bank_wallet_pgpa_merchant_insurance', 'transaction_date', 'ifsc_code', 'transaction_id']]

            # Get distinct from_account_no and their associated to_account_no
            unique_from = layer_nodes['from_account_no'].unique()
            unique_to = layer_nodes['to_account_no'].unique()

            # Create unified nodes for both 'from' and 'to' accounts in this layer
            for account in set(unique_from).union(set(unique_to)):
                if account not in unique_nodes:  # Check if node already exists
                    
                    # Collecting additional info for the node label
                    account_info = layer_nodes[layer_nodes['from_account_no'] == account]
                    if account_info.empty:
                        account_info = layer_nodes[layer_nodes['to_account_no'] == account]

                    # Ensure there is info to show
                    if not account_info.empty:
                        account_info = account_info.iloc[0]  # Access the first row
                        label = f"""<<TABLE BORDER="0" CELLBORDER="0">
                    <TR><TD><FONT COLOR="#8926B6" POINT-SIZE="12"><B>{account}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="#036100"><B>{account_info['utr_number']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="blue"><B>{account_info['ifsc_code']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="red" POINT-SIZE="15"><B>{format_amount_indian(account_info['amount'])}</B></FONT></TD><TD><FONT COLOR="red" POINT-SIZE="15"><B>{account_info['reported_info']}</B></FONT></TD></TR>
                    <TR><TD><FONT COLOR="#6b3700">{account_info['transaction_date']}</FONT></TD><TD><FONT COLOR="#6b3700">{account_info['layer']}</FONT></TD></TR>
                    <TR><TD><FONT COLOR="blue">{account_info['action_taken_by_bank_wallet_pgpa_merchant_insurance']}</FONT></TD></TR>
                    <TR><TD><FONT COLOR="black">{split_text(account_info['remarks'])}</FONT></TD></TR>
                </TABLE>>"""
                        
                        # Store the label in node_labels dictionary
                        node_labels[account] = label
                        
                        dot.node(f'account_{account}', 
                                label=label,
                                shape='box')
                        unique_nodes.add(account)  # Add to unique nodes set

            # Create edges based on transactions and sum amounts if necessary
            for _, row in layer_nodes.iterrows():
                from_node = f'account_{row["from_account_no"]}'
                to_node = f'account_{row["to_account_no"]}'
                # Only create an edge if the from and to accounts are different (avoid self-loop)
                if (from_node != to_node) & (to_node!='account_NaaN'): #if from_node != to_node:
                    # Create a key to represent the from-to account pair
                    edge_key = (from_node, to_node)
                    # If this edge already exists, sum the amounts
                    if edge_key in edges_dict:
                        edges_dict[edge_key]['amount'] += row['amount']  # Sum the amounts
                        edges_dict[edge_key]['transaction_ids'].append(row['utr_number'])  # Append the transaction ID
                        edges_dict[edge_key]['dates'].append(row['transaction_date'])  # Append the transaction date
                    else:
                        edges_dict[edge_key] = {
                            'amount': row['amount'],
                            'transaction_ids': [row['utr_number']],
                            'dates': [row['transaction_date']]
                        }

            # Store accounts for the current layer
            layer_accounts[i] = {
                'from': unique_from,
                'to': unique_to
            }

            # If there's a previous layer, connect accounts with the same number, avoiding self-loops
            if i > 1:  # Assuming layers are numbered sequentially starting from 1
                previous_layer = i - 1
                if previous_layer in layer_accounts:
                    # Connect from previous layer's "to" accounts to current layer's "from" accounts
                    for from_account in layer_accounts[i]['from']:
                        if from_account in layer_accounts[previous_layer]['to']:
                            # Avoid self-loop by making sure the node isn't connected to itself
                            if f'account_{from_account}' != f'account_{from_account}':
                                dot.edge(f'account_{from_account}', f'account_{from_account}', 
                                        xlabel=f'Layer connection from Layer {previous_layer} to Layer {i}', minlen='2')
        logging.info("10. Node generation at the function is done successfully")
        log_box.insert("end", "Node generation at the function is done successfully.\n")
        log_box.see("end")
    except Exception as e:
        logging.error("Error at generating nodes in Graph printing func ",e)
        log_box.insert("end", "Error at generating nodes in Graph printing func.\n")
        log_box.see("end")                            

    try:
        # Now create the edges without labels, but add the summed details to the target nodes
        for (from_node, to_node), edge_data in edges_dict.items():
            
            # Append the summed information to the 'to' node
            total_amount = format_amount_indian(edge_data['amount'])
            transactions = '@ '.join(edge_data['transaction_ids'])
            dates = '@ '.join(edge_data['dates'])

            # Extract the account number from the to_node
            to_account = to_node.split('_')[1]  # Extract account number from the node ID

            # Get the original label from node_labels
            if to_account in node_labels:
                original_label = node_labels[to_account]

                # Add summed details to the existing label
                additional_label = f"""
                <TR><TD><FONT COLOR="blue">Total Amount: {total_amount}</FONT></TD></TR>
                <TR><TD><FONT COLOR="blue">Transactions: {transactions}</FONT></TD></TR>
                <TR><TD><FONT COLOR="blue">Dates: {dates}</FONT></TD></TR>
                </TABLE>>"""
                
                updated_label = original_label.replace('</TABLE>>', additional_label)  # Replace closing tag with additional details
                
                # Update the node with the new label
                dot.node(to_node, label=updated_label)
                # Also update the dictionary to reflect the new label
                node_labels[to_account] = updated_label

            # Create the edge without label
            dot.edge(from_node, to_node, minlen='2')
        logging.info("11. Edge generation for the nodes in graph printing func is done successfully")
        log_box.insert("end", "Edge generation for the nodes in graph printing func is done successfully.\n")
        log_box.see("end")
    except Exception as e:
        logging.error("Error in Graph Printing func at edge generation ", e)
        log_box.insert("end", "Error in Graph Printing func at edge generation.\n")
        log_box.see("end")
    # --- Calculate the required details for the text below the graph ---
    try:
        # 1. Total number of accounts involved excluding Layer 1 'from_account_no'
        layer_1_from_accounts = new_df[new_df['layer'] == 1]['from_account_no'].unique()
        all_accounts = set(new_df['from_account_no'].unique()).union(new_df['to_account_no'].unique())
        total_accounts_excluding_layer_1 = all_accounts.difference(layer_1_from_accounts)

        # 2. Calculate number of days from the first to the last transaction
        all_dates = pd.to_datetime(new_df['transaction_date'], errors='coerce')  # Convert to datetime
        all_dates = all_dates.dropna()  # Drop invalid dates
        days_span = (all_dates.max() - all_dates.min()).days  # Calculate days difference

        # 3. Number of layers in the graph
        num_layers = len(new_df['layer'].unique())

        # 4. Count of unique transactions based on 'action_taken_by_bank_wallet_pgpa_merchant_insurance'
        transaction_modes = new_df['action_taken_by_bank_wallet_pgpa_merchant_insurance'].value_counts()

        # --- Show Unique Account Numbers and IFSC Codes ---
        unique_account_ifsc = new_df[['from_account_no', 'ifsc_code']].drop_duplicates()

        # --- Create a plaintext node to display the summary in a box in the bottom left corner ---
        summary_text = f"""<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2">
        <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="14"><B>Summary of Graph</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT">Total No. of Accounts (excluding Layer 1's 'from_account_no'): <B>{len(total_accounts_excluding_layer_1)}</B></TD></TR>
        <TR><TD ALIGN="LEFT">Time Span of Transactions: <B>{days_span} days</B></TD></TR>
        <TR><TD ALIGN="LEFT">Total No. of Layers: <B>{num_layers}</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>Unique Mode of Transactions</B></TD></TR>"""

        # Adding each mode and its count to the summary text
        for mode, count in transaction_modes.items():
            summary_text += f'<TR><TD ALIGN="LEFT">{mode}: <B>{count}</B></TD></TR>'

        # Adding unique accounts and IFSC codes to the summary
        summary_text += '<TR><TD ALIGN="LEFT"><B>Unique Accounts and IFSC Codes</B></TD></TR>'
        for idx, row in unique_account_ifsc.iterrows():
            summary_text += f'<TR><TD ALIGN="LEFT">Account: {row["from_account_no"]}, IFSC: {row["ifsc_code"]}</TD></TR>'

        summary_text += "</TABLE>>"
        logging.info("12. Calculated summary box to the Graph in Graph Printing func")
        log_box.insert("end", "Calculated summary box to the Graph in Graph Printing func.\n")
        log_box.see("end")
    except Exception as e:
        logging.warning("Error while generating Calculation for the summary box in Graph print func")
        log_box.insert("end", "Error while generating Calculation for the summary box in Graph print func.\n")
        log_box.see("end")
    # --- Add this summary text node at the bottom left corner (rank=sink) ---
    dot.node('summary', label=summary_text, shape='plaintext')
    
    # Render the combined graph after processing all layers
    filename = re.sub(r'[^a-zA-Z0-9]', '', ackname.replace('TransactionFlowGraphForAckNo', ''))
    dot.render(filename, format='pdf', cleanup=False)
    logging.info("13. PDF Generated Successfully")
    dot.view()


# In[ ]:


def main_func(file_path):
    df = pd.read_excel(file_path, dtype= str)
    new_columns = [
                'S No.', 'acknowledgement_no', 'transaction_id', 'Layer', 'from_account_no', 
                'Action Taken by Bank/ (Wallet /PG/PA)/ Merchant// Insurance', 
                'Bank/ (Wallet /PG/PA)/ Merchant / Insurance', 'to_account_no', 'Ifsc Code', 
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
        logging.warning("3. Extra columns are found and that case handled with unnamed text")
        log_box.insert("end", "Extra columns are found and that case handled with unnamed text.\n")
        log_box.see("end")
    else:
        # If fewer columns in the Excel, truncate the new_columns to match
        adjusted_columns = new_columns[:num_current_columns]
    # Replace the column headers with the adjusted columns
    df.columns = adjusted_columns
    try:
        df.columns = [clean_column_name(col) for col in df.columns]
        logging.info("4. Clean columns func executed successfully")
        log_box.insert("end", "Clean columns func executed successfully.\n")
        log_box.see("end")
    except Exception as e:
        logging.warning("Exception at cleaning columns ",e)
        log_box.insert("end", "Exception at cleaning columns.\n")
        log_box.see("end")
        # Ensure that the 'to_account_no' column is treated as a string
    df['to_account_no'] = df['to_account_no'].astype(str)
    try:
    # Perform the split and handle cases where there's no bracket '[' in the string
        df_split = df['to_account_no'].str.split(r'\[', n=1, expand=True)

        # Ensure that df_split has two columns by filling missing values with empty strings
        df_split[1] = df_split[1].fillna('')  # This handles rows without the '['
            # Assign the first part to 'to_account_no' and the second part to 'reported_info'
        df['to_account_no'] = df_split[0].str.strip()
        df['reported_info'] = df_split[1].str.replace(']', '').str.strip()

        # Extract only the number from 'reported_info' (e.g., 'Reported 1 times' -> '1')
        df['reported_info'] = df['reported_info'].str.extract(r'(\d+)')
        logging.info("5. Splitting to_account_no for reported times done successfully")
        log_box.insert("end", "Splitting to_account_no for reported times done successfully.\n")
        log_box.see("end")
    except Exception as e:
        logging.warning("Exception at splittig account no ",e)
        log_box.insert("end", "Exception at splittig account no.\n")
        log_box.see("end")


    df['amount']=df['amount'].astype(float)
    df['layer'] = df['layer'].astype(int)

    #df = df.drop(['unique_id'],axis=1)
    df = df.drop(['s_no'],axis=1)

    # Define the columns to clean
    columns_to_clean = [
        'acknowledgement_no', 'transaction_id', 'layer',
        'utr_number', 'amount','to_account_no','from_account_no'
    ]

    logging.info("6. Columns cleaning Successful")
    log_box.insert("end", "Columns cleaning Successful.\n")
    log_box.see("end")
    # Apply the cleaning function to each specified column
    for col in columns_to_clean:
        if col in df.columns:
            df[col] = clean_column_data(df[col])

    #df['unique_id'] = pd.Series(range(1, len(df) + 1))
    columns_to_update = ['to_account_no', 'from_account_no', 'ifsc_code', 'utr_number', 'remarks', 'transaction_id']
    df.isnull().sum() + (df == '').sum()

    df['from_account_no'] = df['from_account_no'].replace('nan','NaaN')
    df['to_account_no'] = df['to_account_no'].replace('nan','NaaN')

    
    # Replace empty strings and null values with 'NaaN'
    df[columns_to_update] = df[columns_to_update].replace('', 'NaaN').fillna('NaaN')
    df.isnull().sum() + (df == '').sum()

    logging.info("7. Replacing Null values with NaaN.")
    log_box.insert("end", "Replacing Null values with NaaN.\n")
    log_box.see("end")
    df['layer'] = pd.to_numeric(df['layer'], errors='coerce')
    try:
        df['to_account_no'] = df['to_account_no'].apply(clean_account_no)
        df['from_account_no'] = df['from_account_no'].apply(clean_account_no)
        logging.info("8. cleaning account numbers is done successfully")
        log_box.insert("end", "Cleaning account numbers is done successfully.\n")
        log_box.see("end")
    except Exception as e:
        logging.error("Error at exec clean_account_no func")
        log_box.insert("end", "Error at exec clean_account_no func.\n")
        log_box.see("end")
    ackno = df['acknowledgement_no'].unique()
    ackname = 'Transaction Flow Graph For (Ack No): ' + str(ackno)

    new_df=df[['from_account_no','layer', 'to_account_no', 'transaction_id', 'transaction_date', 'ifsc_code', 'amount', 'remarks', 'action_taken_by_bank_wallet_pgpa_merchant_insurance','reported_info', 'utr_number']]
    new_df['amount']=(new_df['amount'].astype(int))/10
    new_df['amount']= new_df['amount'].astype(int)
    try:
        logging.info("9. Dataframe created and passing to Graph Model")
        log_box.insert("end", "Dataframe created and passing to Graph Model.\n")
        log_box.see("end")
        graph_printing(new_df, ackname)
    except Exception as e:
        logging.info("Exception from the graph printing func ",e)
        log_box.insert("end", "Exception from the graph printing func.\n")
        log_box.see("end")


# Ensure log file exists or create it
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, "w").close()

# Configure the logger
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("1. Application started.")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Add log box below the submit button
log_box = None
# Constants for credentials
USERNAME = "Admin"
PASSWORD = "Efftronics"

# Login functionality
def login():
    username = username_entry.get()
    password = password_entry.get()
    
    if username == USERNAME and password == PASSWORD:
        login_frame.pack_forget()  # Hide the login frame
        upload_frame.pack(pady=20)  # Show the upload frame
    else:
        error_label.configure(text="Invalid credentials!", text_color="red")

# File upload functionality
def upload_file():
    global uploaded_file_path  # Store the file path for later processing
    uploaded_file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx")],
        title="Choose an Excel file"
    )
    
    if uploaded_file_path:
        try:
            # Validate file type if needed (e.g., check extension or content)
            uploaded_file_label.configure(
                text=f"Uploaded: {uploaded_file_path.split('/')[-1]}",
                text_color="green"
            )
            submit_btn.configure(state=ctk.NORMAL)  # Enable the submit button
            logging.info(f"2. File uploaded successfully: {uploaded_file_path}")
            messagebox.showinfo("Success", "File uploaded successfully!")
            log_box.insert("end", "File uploaded successfully.\n")
            log_box.see("end")
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            log_box.insert("end", f"Error uploading file: {e}\n")
            log_box.see("end")
            messagebox.showerror("Error", f"Failed to upload the file: {e}")

# File submission functionality
def submit_file():
    try:
        if not uploaded_file_path:
            raise FileNotFoundError("No file uploaded.")
        
        # Call the main processing function here
        main_func(uploaded_file_path)  # Replace this with your file processing logic
        uploaded_file_label.configure(text="File submitted successfully!", text_color="blue")
        logging.info("14. File submitted and processed successfully.")
        log_box.insert("end", "File submitted and processed successfully.\n")
        log_box.see("end")
        messagebox.showinfo("Submission", "File submitted and processed successfully!")
    except Exception as e:
        logging.error(f"Error during file submission or processing: {e}")
        log_box.insert("end", f"Error during file processing: {e}\n")
        log_box.see("end")
        messagebox.showerror("Error", f"Failed to process file: {e}")

# Initialize the main application window
ctk.set_appearance_mode("Dark")  # Light/Dark mode or System
ctk.set_default_color_theme("blue")  # Available: blue, dark-blue, green

root = ctk.CTk()
root.title("Upload Excel File")
root.geometry("600x500")

# Banner
banner = ctk.CTkFrame(root, fg_color="#060270", height=60)
banner.pack(fill="x")

title_label = ctk.CTkLabel(banner, text="CIA Transaction Data", font=("Arial", 20), text_color="white")
title_label.pack(pady=10)

# Login Frame
login_frame = ctk.CTkFrame(root)
login_frame.pack(pady=20)

# Username and password fields
username_label = ctk.CTkLabel(login_frame, text="Username:")
username_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
username_entry = ctk.CTkEntry(login_frame, placeholder_text="Enter your username")
username_entry.grid(row=0, column=1, padx=5, pady=5)

password_label = ctk.CTkLabel(login_frame, text="Password:")
password_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
password_entry = ctk.CTkEntry(login_frame, placeholder_text="Enter your password", show="*")
password_entry.grid(row=1, column=1, padx=5, pady=5)

# Error label for invalid login
error_label = ctk.CTkLabel(login_frame, text="", text_color="red")
error_label.grid(row=3, columnspan=2, pady=5)

# Login Button
login_btn = ctk.CTkButton(login_frame, text="Login", command=lambda: login())
login_btn.grid(row=2, columnspan=2, pady=20)

# Upload Frame (hidden initially)
upload_frame = ctk.CTkFrame(root)

upload_btn = ctk.CTkButton(upload_frame, text="Upload Excel File", command=lambda: upload_file())
upload_btn.pack(pady=20)

# Add informational label for file format
info_label = ctk.CTkLabel(upload_frame, text="Please upload .xlsx file only", text_color="gray")
info_label.pack(pady=5)

uploaded_file_label = ctk.CTkLabel(upload_frame, text="No file uploaded", text_color="gray")
uploaded_file_label.pack(pady=5)

submit_btn = ctk.CTkButton(upload_frame, text="Submit", command=lambda: submit_file(), state=ctk.DISABLED)
submit_btn.pack(pady=20)

# Add log box
log_box = ctk.CTkTextbox(upload_frame, width=500, height=250)
log_box.pack(pady=10)
log_box.insert("end", "Logs:\n")
log_box.configure(state="normal")

upload_frame.pack(pady=20)
# Run the application
root.mainloop()