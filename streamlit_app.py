import datetime
import altair as alt
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Support tickets", page_icon="🎫", layout="wide")
st.title("🎫 Support Ticket Management System")
st.write(
    """
    Experience a professional support ticket workflow. Manage, track, and analyze
    your tickets with ease.
    """
)

REQUIRED_COLUMNS = [
    "ID",
    "Issue",
    "Status",
    "Priority",
    "Date Submitted",
    "Resolution Date",
]


@st.cache_resource
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = df.copy()

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[REQUIRED_COLUMNS]

    if "Date Submitted" in df.columns:
        df["Date Submitted"] = pd.to_datetime(
            df["Date Submitted"], errors="coerce"
        ).dt.date

    if "Resolution Date" in df.columns:
        df["Resolution Date"] = pd.to_datetime(
            df["Resolution Date"], errors="coerce"
        ).dt.date

    return df


def load_data():
    conn = get_conn()
    try:
        df = conn.read(worksheet="Tickets", ttl=0)
        return normalize_df(df)
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {e}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)


def save_data(df: pd.DataFrame):
    conn = get_conn()
    df_to_save = df.copy()

    df_to_save["Date Submitted"] = pd.to_datetime(
        df_to_save["Date Submitted"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df_to_save["Resolution Date"] = pd.to_datetime(
        df_to_save["Resolution Date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df_to_save = df_to_save.fillna("")

    conn.update(worksheet="Tickets", data=df_to_save)
    st.cache_data.clear()


if "df" not in st.session_state:
    st.session_state.df = load_data()

tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📋 Manage Tickets", "➕ Add Ticket"])

with tab3:
    st.header("Add a ticket")

    with st.form("add_ticket_form"):
        if not st.session_state.df.empty:
            try:
                numeric_ids = []
                for tid in st.session_state.df["ID"]:
                    if isinstance(tid, str) and "-" in tid:
                        try:
                            numeric_ids.append(int(tid.split("-")[1]))
                        except (ValueError, IndexError):
                            pass

                if numeric_ids:
                    suggested_id = f"TICKET-{max(numeric_ids) + 1}"
                else:
                    suggested_id = f"TICKET-{len(st.session_state.df) + 1001}"
            except Exception:
                suggested_id = f"TICKET-{len(st.session_state.df) + 1001}"
        else:
            suggested_id = "TICKET-1001"

        ticket_id = st.text_input("Ticket ID", value=suggested_id)
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")

    if submitted:
        if ticket_id in st.session_state.df["ID"].astype(str).values:
            st.error(f"Ticket ID {ticket_id} already exists. Please use a unique ID.")
        elif not ticket_id.strip():
            st.error("Ticket ID cannot be empty.")
        else:
            today = datetime.date.today()
            df_new = pd.DataFrame(
                [
                    {
                        "ID": ticket_id.strip(),
                        "Issue": issue.strip(),
                        "Status": "Open",
                        "Priority": priority,
                        "Date Submitted": today,
                        "Resolution Date": pd.NaT,
                    }
                ]
            )

            st.session_state.df = pd.concat(
                [df_new, st.session_state.df], axis=0
            ).reset_index(drop=True)

            try:
                save_data(st.session_state.df)
                st.success("Ticket submitted and saved to Google Sheets.")
                st.dataframe(df_new, width='stretch', hide_index=True)
            except Exception as e:
                st.error(f"Ticket created in session, but failed to save to Google Sheets: {e}")

with tab2:
    st.header("Existing tickets")

    col_mgmt1, col_mgmt2 = st.columns([4, 1])
    with col_mgmt1:
        st.write(f"Number of tickets: `{len(st.session_state.df)}`")

    with col_mgmt2:
        if st.button("🗑️ Clear All", help="Delete all tickets from Google Sheets"):
            empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            try:
                save_data(empty_df)
                st.session_state.df = empty_df
                st.success("All tickets deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear tickets: {e}")

    st.info(
        "You can edit tickets by double-clicking a cell. "
        "Press Enter or click outside the cell before saving. "
        "Changes are saved only when you click 'Save Changes'.",
        icon="✍️",
    )

    edited_df = st.data_editor(
        st.session_state.df,
        width='stretch',
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
                format="YYYY-MM-DD",
            ),
            "Date Submitted": st.column_config.DateColumn(
                "Date Submitted",
                format="YYYY-MM-DD",
            ),
        },
        disabled=["ID", "Date Submitted"],
        key="ticket_editor",
    )

    col_save1, col_save2 = st.columns([1, 4])

    with col_save1:
        if st.button("💾 Save Changes", help="Save edits to Google Sheets"):
            try:
                st.session_state.df = normalize_df(edited_df)
                save_data(st.session_state.df)
                st.success("Changes saved to Google Sheets.")
            except Exception as e:
                st.error(f"Failed to save changes: {e}")

    with col_save2:
        csv = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="tickets.csv",
            mime="text/csv",
            help="Download the current table as CSV",
        )

with tab1:
    st.header("Statistics Dashboard")

    df = normalize_df(st.session_state.df)

    num_open_tickets = len(df[df["Status"] == "Open"]) if not df.empty else 0
    num_in_progress_tickets = len(df[df["Status"] == "In Progress"]) if not df.empty else 0
    num_closed_tickets = len(df[df["Status"] == "Closed"]) if not df.empty else 0

    avg_res_time = 0
    if not df.empty:
        resolved_df = df[df["Resolution Date"].notna()].copy()
        if not resolved_df.empty:
            resolved_df["Resolution Date"] = pd.to_datetime(resolved_df["Resolution Date"])
            resolved_df["Date Submitted"] = pd.to_datetime(resolved_df["Date Submitted"])
            resolved_df["Resolution Time"] = (
                resolved_df["Resolution Date"] - resolved_df["Date Submitted"]
            ).dt.days
            avg_res_time = resolved_df["Resolution Time"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Open Tickets", value=num_open_tickets)
    col2.metric(label="Closed Tickets", value=num_closed_tickets)
    col3.metric(label="Avg. Resolution (Days)", value=f"{avg_res_time:.1f}")

    st.write("")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("##### Ticket Status Trends")
        if not df.empty:
            chart_df = df.copy()
            chart_df["Date Submitted"] = pd.to_datetime(chart_df["Date Submitted"], errors="coerce")

            status_plot = (
                alt.Chart(chart_df)
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
            st.altair_chart(status_plot, width='stretch', theme="streamlit")
        else:
            st.info("No ticket data available.")

    with col_chart2:
        st.write("##### Priority Distribution")
        if not df.empty:
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
            st.altair_chart(priority_plot, width='stretch', theme="streamlit")
        else:
            st.info("No ticket data available.")
