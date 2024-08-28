import streamlit as st
import psutil
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv
import os

# Caching the process data retrieval
@st.cache_data(ttl=5)
def get_process_data():
    processes = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'io_counters', 'num_threads', 'status'])
    process_data = [process.info for process in processes]
    return pd.DataFrame(process_data)

def plot_process_metrics(fig, ax, df, metric, top_n):
    ax.clear()
    if metric == 'io_counters':
        df['io_read_count'] = [tup[0] for tup in df['io_counters']]
        ax.bar(df['name'].head(top_n), df['io_read_count'].head(top_n))
        ax.set_ylabel('I/O Read Count')
    else:
        ax.bar(df['name'].head(top_n), df[metric].head(top_n))
        ax.set_ylabel(metric)
    ax.set_xlabel('Process')
    ax.set_title(f'Top {top_n} Processes by {metric}')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    return fig

def update_plot(frame, figs, axes, process_df, metrics, top_n):
    process_df = get_process_data()
    for fig, ax, metric in zip(figs, axes, metrics):
        plot_process_metrics(fig, ax, process_df, metric, top_n)
    return figs

def log_system_metrics(cpu_usage, memory_usage):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "system_metrics.csv"
    
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "CPU Usage", "Memory Usage"])
    
    with open(log_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, cpu_usage, memory_usage])

def main():
    st.set_page_config(page_title="Simple Task Manager", layout="wide")
    
    # Navigation
    page = st.sidebar.selectbox("Select a page", ["Task Manager", "About"])
    
    if page == "Task Manager":
        st.title("Task Manager")

        # Process Information
        st.sidebar.header("Process Filters")
        filter_options = ["All", "Running", "Stopped", "High CPU Usage", "High Memory Usage", "High I/O", "High Threads", "Low CPU Usage", "Low Memory Usage"]
        filter_choice = st.sidebar.selectbox("Filter processes by:", filter_options)
        top_n = st.sidebar.number_input("Number of processes to display", min_value=5, max_value=20, value=10, step=1)
        metric_options = ["cpu_percent", "memory_percent", "io_counters", "num_threads"]
        selected_metrics = st.sidebar.multiselect("Select process metrics to visualize:", metric_options)

        process_df = get_process_data()

        # Filter processes based on user selection
        if filter_choice == "High CPU Usage":
            process_df = process_df.nlargest(top_n, 'cpu_percent')
        elif filter_choice == "High Memory Usage":
            process_df = process_df.nlargest(top_n, 'memory_percent')
        elif filter_choice == "High I/O":
            process_df = process_df.nlargest(top_n, 'io_counters')
        elif filter_choice == "High Threads":
            process_df = process_df.nlargest(top_n, 'num_threads')
        elif filter_choice == "Low CPU Usage":
            process_df = process_df.nsmallest(top_n, 'cpu_percent')
        elif filter_choice == "Low Memory Usage":
            process_df = process_df.nsmallest(top_n, 'memory_percent')
        elif filter_choice == "Running":
            process_df = process_df[process_df['status'] == 'running'].head(top_n)
        elif filter_choice == "Stopped":
            process_df = process_df[process_df['status'] == 'stopped'].head(top_n)
        else:
            process_df = process_df.head(top_n)

        # Display processes
        st.dataframe(process_df)

        # Visualizations
        st.header("Process Metrics")

        # Create a figure and axis for each selected metric
        figs, axes = [], []
        for metric in selected_metrics:
            fig, ax = plt.subplots(figsize=(8, 6))
            figs.append(fig)
            axes.append(ax)

        # Update the plots every second
        metric_animation = animation.FuncAnimation(figs, update_plot, fargs=(figs, axes, process_df, selected_metrics, top_n), interval=1000)

        # Display the plots
        cols = st.columns(len(selected_metrics))
        for i, (fig, metric) in enumerate(zip(figs, selected_metrics)):
            with cols[i]:
                st.subheader(f"{metric.capitalize()} Usage")
                st.pyplot(fig)

        # Display additional information
        st.header("System Information")
        col1, col2 = st.columns(2)

        with col1:
            cpu_usage = psutil.cpu_percent(interval=1)
            st.metric("CPU Usage", f"{cpu_usage}%")

        with col2:
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            st.metric("Memory Usage", f"{memory_usage}%")

        st.write(f"Startup Time: {datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}")

        # Log system metrics
        log_system_metrics(cpu_usage, memory_usage)

    elif page == "About":
        st.title("About This Task Manager")
        
        st.markdown("""
        ## Technical Documentation

        This Task Manager is a Streamlit application that provides real-time monitoring of system processes and resources. Here's a detailed explanation of its components and functionality:

        ### 1. Libraries Used
        - `streamlit`: For creating the web application interface
        - `psutil`: For retrieving information about system processes and resources
        - `pandas`: For data manipulation and analysis
        - `matplotlib`: For creating visualizations
        - `csv`: For logging system metrics to a CSV file

        ### 2. Key Functions

        #### `get_process_data()`
        - Retrieves information about running processes using `psutil.process_iter()`
        - Returns a pandas DataFrame with process information
        - Cached using `@st.cache_data(ttl=5)` to improve performance (cache expires after 5 seconds)

        #### `plot_process_metrics()`
        - Creates bar plots for the selected process metrics
        - Handles special case for 'io_counters' metric

        #### `update_plot()`
        - Updates the plots with the latest process data
        - Called by `animation.FuncAnimation()` to create animated plots

        #### `log_system_metrics()`
        - Logs CPU and memory usage to a CSV file ('system_metrics.csv')
        - Creates the file if it doesn't exist, otherwise appends to it

        ### 3. Main Application Flow

        1. User selects filters and metrics in the sidebar
        2. Process data is retrieved and filtered based on user selection
        3. Filtered process data is displayed in a table
        4. Animated plots are created for selected metrics
        5. Overall system information (CPU usage, Memory usage, Startup time) is displayed
        6. System metrics are logged to a CSV file

        ### 4. Features

        - Real-time updating of process information and visualizations
        - Flexible filtering options for processes
        - Multi-metric visualization
- Caching of process data to improve performance
        - Logging of system metrics for historical analysis

        ### 5. Potential Improvements

        - Implement more advanced filtering and sorting options
        - Add network usage monitoring
        - Create historical views of system performance
        - Implement database storage for logged metrics instead of CSV
        - Add process termination functionality

        ### 6. Running the Application

        To run the application, ensure all required libraries are installed and run:

        ```
        streamlit run t3-sim-task-mgmr.py
        ```

        
        """)

if __name__ == "__main__":
    main()