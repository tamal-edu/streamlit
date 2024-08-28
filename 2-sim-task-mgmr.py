import streamlit as st
import psutil
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.animation as animation
from datetime import datetime
import logging

# Set up Seaborn style for better aesthetics
sns.set(style="darkgrid")

# Set up logging with timestamp
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Enable caching for process data
@st.cache_data(ttl=60)
def get_process_info():
    process_info = []
    for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'io_counters']):
        try:
            io_counters = process.info['io_counters']._asdict() if process.info['io_counters'] else {}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        process_info.append({
            'PID': process.info['pid'],
            'Name': process.info['name'],
            'CPU': process.info['cpu_percent'],
            'Memory': process.info['memory_percent'],
            **io_counters
        })
    return pd.DataFrame(process_info)

# Function to get system metrics
def get_system_metrics(selected_metrics):
    metrics = {'Time': datetime.now().strftime('%H:%M:%S')}
    if 'CPU Usage (%)' in selected_metrics:
        metrics['CPU Usage (%)'] = psutil.cpu_percent(interval=1)
    if 'Memory Usage (%)' in selected_metrics:
        metrics['Memory Usage (%)'] = psutil.virtual_memory().percent
    if 'Disk Usage (%)' in selected_metrics:
        metrics['Disk Usage (%)'] = psutil.disk_usage('/').percent
    if 'Network (Bytes Sent)' in selected_metrics:
        net_io = psutil.net_io_counters()
        metrics['Network (Bytes Sent)'] = net_io.bytes_sent
    if 'Network (Bytes Received)' in selected_metrics:
        net_io = psutil.net_io_counters()
        metrics['Network (Bytes Received)'] = net_io.bytes_recv
    if 'Network (Bytes Sent+Received)' in selected_metrics:
        net_io = psutil.net_io_counters()
        metrics['Network (Bytes Sent+Received)'] = net_io.bytes_sent + net_io.bytes_recv
    if 'Processes Count' in selected_metrics:
        metrics['Processes Count'] = len(psutil.pids())
    if 'Threads Count' in selected_metrics:
        metrics['Threads Count'] = sum(p.num_threads() for p in psutil.process_iter())
    if 'Battery (%)' in selected_metrics and psutil.sensors_battery():
        metrics['Battery (%)'] = psutil.sensors_battery().percent
    if 'Swap Memory Usage (%)' in selected_metrics:
        metrics['Swap Memory Usage (%)'] = psutil.swap_memory().percent
    if 'Disk Read Bytes' in selected_metrics:
        metrics['Disk Read Bytes'] = psutil.disk_io_counters().read_bytes
    if 'Disk Write Bytes' in selected_metrics:
        metrics['Disk Write Bytes'] = psutil.disk_io_counters().write_bytes
    if 'CPU Temperature' in selected_metrics:
        # Example: Assuming availability; adjust accordingly
        metrics['CPU Temperature'] = psutil.sensors_temperatures().get('coretemp', [{}])[0].current
    if 'Battery Time Left (Minutes)' in selected_metrics and psutil.sensors_battery():
        metrics['Battery Time Left (Minutes)'] = psutil.sensors_battery().secsleft // 60
    if 'Network Errors' in selected_metrics:
        net_io = psutil.net_io_counters()
        metrics['Network Errors'] = net_io.errin + net_io.errout
    if 'Network Drops' in selected_metrics:
        net_io = psutil.net_io_counters()
        metrics['Network Drops'] = net_io.dropin + net_io.dropout
    if 'CPU Frequency (Current)' in selected_metrics:
        metrics['CPU Frequency (Current)'] = psutil.cpu_freq().current
    if 'CPU Frequency (Min)' in selected_metrics:
        metrics['CPU Frequency (Min)'] = psutil.cpu_freq().min
    if 'CPU Frequency (Max)' in selected_metrics:
        metrics['CPU Frequency (Max)'] = psutil.cpu_freq().max
    if 'Virtual Memory Total (MB)' in selected_metrics:
        metrics['Virtual Memory Total (MB)'] = psutil.virtual_memory().total / (1024 * 1024)
    if 'Virtual Memory Available (MB)' in selected_metrics:
        metrics['Virtual Memory Available (MB)'] = psutil.virtual_memory().available / (1024 * 1024)
    if 'Disk Total Space (GB)' in selected_metrics:
        metrics['Disk Total Space (GB)'] = psutil.disk_usage('/').total / (1024 * 1024 * 1024)
    if 'Disk Free Space (GB)' in selected_metrics:
        metrics['Disk Free Space (GB)'] = psutil.disk_usage('/').free / (1024 * 1024 * 1024)

    return metrics

# Function to plot the metrics
def plot_metrics(metrics_df, selected_metrics):
    num_metrics = len(selected_metrics)
    num_rows = (num_metrics + 1) // 2  # Calculate rows needed

    fig, axs = plt.subplots(num_rows, 2, figsize=(12, num_rows * 4))
    axs = axs.flatten()  # Flatten in case of a single row

    for i, metric in enumerate(selected_metrics):
        sns.lineplot(x='Time', y=metric, data=metrics_df, ax=axs[i])
        axs[i].set_title(metric)

    for j in range(i + 1, len(axs)):
        fig.delaxes(axs[j])

    plt.tight_layout()
    st.pyplot(fig)

# Function to create and return the figure for each selected metric
def create_figure(metric, process_df, top_n):
    fig, ax = plt.subplots()
    top_processes = process_df.nlargest(top_n, metric)
    ax.barh(top_processes['Name'], top_processes[metric])
    ax.set_xlabel(metric)
    ax.set_title(f'Top {top_n} Processes by {metric}')
    return fig, ax

# Update plot for animation
def update_plot(frame, figs, axes, process_df, selected_metrics, top_n):
    process_df = get_process_info()
    for i, metric in enumerate(selected_metrics):
        top_processes = process_df.nlargest(top_n, metric)
        axes[i].clear()
        axes[i].barh(top_processes['Name'], top_processes[metric])
        axes[i].set_xlabel(metric)
        axes[i].set_title(f'Top {top_n} Processes by {metric}')

# Function to get processes info based on classification
def get_processes_info(classification):
    processes = []
    for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 
                                        'username', 'status', 'create_time', 'cpu_times', 'io_counters']):
        process_info = process.info
        process_info['create_time'] = pd.to_datetime(process_info['create_time'], unit='s')

        if classification == 'High CPU Usage':
            if process_info['cpu_percent'] > 10:  # Example threshold
                processes.append(process_info)
        elif classification == 'High Memory Usage':
            if process_info['memory_percent'] > 10:  # Example threshold
                processes.append(process_info)
        elif classification == 'Running':
            if process_info['status'] == 'running':
                processes.append(process_info)
        elif classification == 'Stopped':
            if process_info['status'] == 'stopped':
                processes.append(process_info)
        else:
            processes.append(process_info)
    
    return pd.DataFrame(processes)

# Page 1: Task Manager and System Metrics
def task_manager_page():
    st.title("Simulated Task Manager with System Metrics")

    # Metric selection with search functionality
    all_metrics = ['CPU Usage (%)', 'Memory Usage (%)', 'Disk Usage (%)',
                   'Network (Bytes Sent)', 'Network (Bytes Received)', 'Network (Bytes Sent+Received)', 
                   'Processes Count', 'Threads Count', 'Battery (%)', 'Swap Memory Usage (%)', 
                   'Disk Read Bytes', 'Disk Write Bytes', 'CPU Temperature', 'Battery Time Left (Minutes)', 
                   'Network Errors', 'Network Drops', 'CPU Frequency (Current)', 
                   'CPU Frequency (Min)', 'CPU Frequency (Max)', 'Virtual Memory Total (MB)', 
                   'Virtual Memory Available (MB)', 'Disk Total Space (GB)', 'Disk Free Space (GB)']

    selected_metrics = st.multiselect(
        "Select the metrics to monitor (type to search):",
        all_metrics, default=['CPU Usage (%)', 'Memory Usage (%)', 'Disk Usage (%)'])

    # Number of top processes to display
    top_n = st.slider('Select Number of Top Processes to Display', 1, 10, 5)

    # Sidebar for process classification
    st.sidebar.header("Process Filter")
    classification = st.sidebar.selectbox(
        "Select classification to view processes:",
        ["All", "High CPU Usage", "High Memory Usage", "Running", "Stopped"]
    )

    # Initialize session state for metrics
    if 'metrics_df' not in st.session_state:
        st.session_state['metrics_df'] = pd.DataFrame(columns=[
            'Time', 'CPU Usage (%)', 'Memory Usage (%)', 
            'Disk Usage (%)', 'Network (Bytes Sent)', 'Network (Bytes Received)', 
            'Network (Bytes Sent+Received)', 'Processes Count', 'Threads Count', 
            'Battery (%)', 'Swap Memory Usage (%)', 'Disk Read Bytes', 
            'Disk Write Bytes', 'CPU Temperature', 'Battery Time Left (Minutes)', 
            'Network Errors', 'Network Drops', 'CPU Frequency (Current)', 
            'CPU Frequency (Min)', 'CPU Frequency (Max)', 'Virtual Memory Total (MB)', 
            'Virtual Memory Available (MB)', 'Disk Total Space (GB)', 
            'Disk Free Space (GB)'])

    # Fetch and display the current system metrics
    metrics = get_system_metrics(selected_metrics)
    st.session_state['metrics_df'] = pd.concat([st.session_state['metrics_df'], pd.DataFrame([metrics])], ignore_index=True)

    # Display the current system metrics
    st.write("Current System Metrics:")
    st.write(pd.DataFrame([metrics]))

    # Plot the metrics over time
    plot_metrics(st.session_state['metrics_df'], selected_metrics)

    # Display the processes based on classification
    processes_df = get_processes_info(classification)
    st.write(f"Processes - {classification}:")
    st.dataframe(processes_df)

    # Button to start monitoring
    start_monitoring = st.button('Start Monitoring')

    if start_monitoring:
        process_df = get_process_info()

        # Create figures and axes for each metric
        figs, axes = [], []
        for metric in selected_metrics:
            fig, ax = create_figure(metric, process_df, top_n)
            figs.append(fig)
            axes.append(ax)

        # Display plots in Streamlit
        plot_columns = st.columns(len(selected_metrics))
        for i, fig in enumerate(figs):
            with plot_columns[i]:
                st.pyplot(fig)

        # Start animation
        for i, metric in enumerate(selected_metrics):
            animation.FuncAnimation(figs[i], update_plot, fargs=([figs[i]], [axes[i]], process_df, [metric], top_n), interval=1000)

# Page 2: README or About This Solution
def readme_page():
    st.title("README / About This Solution")
    
    st.markdown("""
    ## Overview
    This application is a simulated task manager that not only monitors system processes but also visualizes various system metrics such as CPU usage, memory usage, disk usage, and network usage.

    ## Features
    - **Real-time Monitoring**: Get up-to-date information on system performance and resource utilization.
    - **Process Filtering**: Filter processes based on criteria such as high CPU usage, high memory usage, running, and stopped processes.
    - **Interactive Visualization**: Use Seaborn for visually appealing real-time graphs of system metrics.
    - **Animated Charts**: Real-time animations for selected metrics to better understand system dynamics.

    ## How to Use
    1. Navigate to the "Task Manager" page to start monitoring system processes and metrics.
    2. Use the sidebar to filter processes according to your needs.
    3. Select metrics you want to visualize and set the number of top processes to display.
    4. Click "Start Monitoring" to begin the process.

    ## Technology Stack
    - **Streamlit**: The app framework used to build this interactive web application.
    - **Psutil**: Python library used to access system details and statistics.
    - **Seaborn & Matplotlib**: Used for plotting and visualizing data.

    ## Future Enhancements
    - Integrate more metrics like temperature, battery status, and more.
    - Add alerts for threshold breaches.
    - Provide historical data and trends.

    ## Author
    This solution is guided by tamal.maity@dxc.com. Feel free to contribute to this project or provide feedback.
    """)

# Main Function to Handle Page Navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select a Page", ["Task Manager", "README / About This Solution"])

    if page == "Task Manager":
        task_manager_page()
    elif page == "README / About This Solution":
        readme_page()

if __name__ == "__main__":
    main()
