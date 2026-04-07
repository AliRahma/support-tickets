import datetime
import random

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Show app title and description.
st.set_page_config(page_title="Support tickets", page_icon="🎫", layout="wide")
st.title("🎫 Support Ticket Management System")
st.write(
    """
    Experience a professional support ticket workflow. Manage, track, and analyze
    your tickets with ease.
    """
)

# Create a random Pandas dataframe with existing tickets.
if "df" not in st.session_state:

    # Set seed for reproducibility.
    np.random.seed(42)

    # Make up some fake issue descriptions.
    issue_descriptions = [
        "Network connectivity issues in the office",
        "Software application crashing on startup",
        "Printer not responding to print commands",
        "Email server downtime",
        "Data backup failure",
        "Login authentication problems",
        "Website performance degradation",
        "Security vulnerability identified",
        "Hardware malfunction in the server room",
        "Employee unable to access shared files",
        "Database connection failure",
        "Mobile application not syncing data",
        "VoIP phone system issues",
        "VPN connection problems for remote employees",
        "System updates causing compatibility issues",
        "File server running out of storage space",
        "Intrusion detection system alerts",
        "Inventory management system errors",
        "Customer data not loading in CRM",
        "Collaboration tool not sending notifications",
    ]

    # Generate the dataframe with 100 rows/tickets.
    data = {
        "ID": [f"TICKET-{i}" for i in range(1100, 1000, -1)],
        "Issue": np.random.choice(issue_descriptions, size=100),
        "Status": np.random.choice(["Open", "In Progress", "Closed"], size=100),
        "Priority": np.random.choice(["High", "Medium", "Low"], size=100),
        "Date Submitted": [
            (datetime.date(2023, 6, 1) + datetime.timedelta(days=random.randint(0, 182)))
            for _ in range(100)
        ],
    }
    df = pd.DataFrame(data)
    df["Resolution Date"] = pd.NA

    # Randomly assign resolution dates to closed tickets
    for i in range(len(df)):
        if df.loc[i, "Status"] == "Closed":
            df.loc[i, "Resolution Date"] = df.loc[i, "Date Submitted"] + datetime.timedelta(
                days=random.randint(1, 10)
            )

    # Save the dataframe in session state (a dictionary-like object that persists across
    # page runs). This ensures our data is persisted when the app updates.
    st.session_state.df = df


# Organize into tabs for a cleaner interface
tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📋 Manage Tickets", "➕ Add Ticket"])

with tab3:
    # Show a section to add a new ticket.
    st.header("Add a ticket")

    # We're adding tickets via an `st.form` and some input widgets. If widgets are used
    # in a form, the app will only rerun once the submit button is pressed.
    with st.form("add_ticket_form"):
        # Generate a suggested ticket ID
        if not st.session_state.df.empty:
            try:
                # Get the highest numeric ID if possible
                numeric_ids = []
                for tid in st.session_state.df.ID:
                    if isinstance(tid, str) and "-" in tid:
                        try:
                            numeric_ids.append(int(tid.split("-")[1]))
                        except (ValueError, IndexError):
                            pass
                if numeric_ids:
                    recent_ticket_number = max(numeric_ids)
                    suggested_id = f"TICKET-{recent_ticket_number+1}"
                else:
                    suggested_id = f"TICKET-{len(st.session_state.df)+1001}"
            except Exception:
                suggested_id = f"TICKET-{len(st.session_state.df)+1001}"
        else:
            suggested_id = "TICKET-1001"

        ticket_id = st.text_input("Ticket ID", value=suggested_id)
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")

    if submitted:
        # Check if Ticket ID is unique
        if ticket_id in st.session_state.df.ID.values:
            st.error(f"Ticket ID {ticket_id} already exists. Please use a unique ID.")
        elif not ticket_id:
            st.error("Ticket ID cannot be empty.")
        else:
            # Make a dataframe for the new ticket and append it to the dataframe in session
            # state.
            today = datetime.date.today()
            df_new = pd.DataFrame(
                [
                    {
                        "ID": ticket_id,
                        "Issue": issue,
                        "Status": "Open",
                        "Priority": priority,
                        "Date Submitted": today,
                        "Resolution Date": pd.NA,
                    }
                ]
            )

            # Show a little success message.
            st.success("Ticket submitted! Here are the ticket details:")
            st.dataframe(df_new, use_container_width=True, hide_index=True)
            st.session_state.df = pd.concat(
                [df_new, st.session_state.df], axis=0
            ).reset_index(drop=True)

with tab2:
    # Show section to view and edit existing tickets in a table.
    st.header("Existing tickets")

    # Use a layout for the management header
    col_mgmt1, col_mgmt2 = st.columns([4, 1])
    with col_mgmt1:
        st.write(f"Number of tickets: `{len(st.session_state.df)}`")
    with col_mgmt2:
        # Add a button to clear all tickets
        if st.button("🗑️ Clear All", help="Delete all tickets from the database"):
            st.session_state.df = pd.DataFrame(
                columns=[
                    "ID",
                    "Issue",
                    "Status",
                    "Priority",
                    "Date Submitted",
                    "Resolution Date",
                ]
            )
            st.rerun()

    st.info(
        "You can edit the tickets by double clicking on a cell. You can also delete rows "
        "by selecting them and pressing the 'Delete' key on your keyboard, or using the "
        "trash icon on the right.",
        icon="✍️",
    )

    # Show the tickets dataframe with `st.data_editor`. This lets the user edit the table
    # cells. The edited data is returned as a new dataframe.
    st.session_state.df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="Ticket status",
                options=["Open", "In Progress", "Closed"],
                required=True,
            ),
            "Priority": st.column_config.SelectboxColumn(
                "Priority",
                help="Priority",
                options=["High", "Medium", "Low"],
                required=True,
            ),
            "Resolution Date": st.column_config.DateColumn(
                "Resolution Date",
                help="Date the ticket was resolved",
                format="MM-DD-YYYY",
            ),
            "Date Submitted": st.column_config.DateColumn(
                "Date Submitted",
                format="MM-DD-YYYY",
            ),
        },
        # Disable editing the ID and Date Submitted columns.
        disabled=["ID", "Date Submitted"],
    )

with tab1:
    # Show some metrics and charts about the ticket.
    st.header("Statistics Dashboard")

    # Calculate metrics
    df = st.session_state.df
    num_open_tickets = len(df[df.Status == "Open"]) if not df.empty else 0
    num_in_progress_tickets = (
        len(df[df.Status == "In Progress"]) if not df.empty else 0
    )
    num_closed_tickets = len(df[df.Status == "Closed"]) if not df.empty else 0

    # Calculate average resolution time
    avg_res_time = 0
    if not df.empty and "Resolution Date" in df.columns:
        resolved_df = df[df["Resolution Date"].notna()].copy()
        if not resolved_df.empty:
            resolved_df["Resolution Date"] = pd.to_datetime(
                resolved_df["Resolution Date"]
            )
            resolved_df["Date Submitted"] = pd.to_datetime(
                resolved_df["Date Submitted"]
            )
            resolved_df["Resolution Time"] = (
                resolved_df["Resolution Date"] - resolved_df["Date Submitted"]
            ).dt.days
            avg_res_time = resolved_df["Resolution Time"].mean()

    # Show metrics side by side using `st.columns` and `st.metric`.
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Open Tickets", value=num_open_tickets)
    col2.metric(label="Closed Tickets", value=num_closed_tickets)
    col3.metric(label="Avg. Resolution (Days)", value=f"{avg_res_time:.1f}")

    # Show two Altair charts using `st.altair_chart`.
    st.write("")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("##### Ticket Status Trends")
        status_plot = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("month(Date Submitted):O", title="Month"),
                y=alt.Y("count():Q", title="Number of Tickets"),
                color=alt.Color(
                    "Status:N",
                    scale=alt.Scale(
                        domain=["Open", "In Progress", "Closed"],
                        range=["#ff4b4b", "#febf71", "#24a06b"],
                    ),
                ),
                tooltip=["month(Date Submitted)", "Status", "count()"],
            )
            .properties(height=300)
            .configure_legend(orient="bottom")
        )
        st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

    with col_chart2:
        st.write("##### Priority Distribution")
        priority_plot = (
            alt.Chart(df)
            .mark_arc(innerRadius=50)
            .encode(
                theta=alt.Theta("count():Q"),
                color=alt.Color(
                    "Priority:N",
                    scale=alt.Scale(
                        domain=["High", "Medium", "Low"],
                        range=["#de2d26", "#feb24c", "#addd8e"],
                    ),
                ),
                tooltip=["Priority", "count()"],
            )
            .properties(height=300)
            .configure_legend(orient="bottom")
        )
        st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")
