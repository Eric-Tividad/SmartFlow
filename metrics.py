# prints results for individual runs, and used for compare.py

# Helpers for the results of a run.
#   print_run_results()  -> prints the results of ONE run in the terminal (used by the window)
#   run_both()           -> runs the SAME traffic with both lights (used by compare.py and --headless)
#   build_table_rows()   -> puts both lights side by side as a table of text

import config
from model import IntersectionModel

# the metrics. "lower_is_better" is used to color the change column in the comparison table
METRIC_ROWS = [
    {"label": "Average wait", "key": "avg_wait_steps", "kind": "seconds", "lower_is_better": True},
    {"label": "Longest wait", "key": "max_wait_steps", "kind": "seconds", "lower_is_better": True},
    {"label": "Cars that had to stop", "key": "percent_stopped", "kind": "percent", "lower_is_better": True},
    {"label": "Avg cars waiting", "key": "avg_waiting_cars", "kind": "number", "lower_is_better": True},
    {"label": "Cars passed in", "key": "passed_by_end_of_arrivals", "kind": "cars", "lower_is_better": False},
    {"label": "Time to clear all", "key": "clear_time_steps", "kind": "seconds", "lower_is_better": True},
]

 # how many seconds cars keep arriving in this run
def get_arrival_seconds(params):
    return params["run_duration"] // config.STEPS_PER_SECOND

# the "Cars passed in" label gets the number of seconds added, like "Cars passed in 30 s"
def get_metric_label(metric, arrival_seconds):
    label = metric["label"]
    if metric["key"] == "passed_by_end_of_arrivals":
        label = label + " " + str(arrival_seconds) + " s"
    return label

# turns a number into the text shown in a table
def format_value(value, kind):
    if kind == "seconds":
        return str(round(value / config.STEPS_PER_SECOND, 1)) + " s"
    if kind == "percent":
        return str(round(value)) + "%"
    if kind == "number":
        return str(round(value, 1))
    return str(round(value))        # "cars"

# prints the results of one finished run in the terminal
def print_run_results(mode_name, results, arrival_seconds):
    line = "=" * 44
    print("")
    print(line)
    print(mode_name + " - run finished")
    print(line)
    print("Total cars".ljust(28) + str(results["total_cars"]).rjust(16))
    for metric in METRIC_ROWS:
        label = get_metric_label(metric, arrival_seconds)
        value_text = format_value(results[metric["key"]], metric["kind"])
        print(label.ljust(28) + value_text.rjust(16))
    print(line)
    print("")

# runs one full simulation with no window and returns its results
def run_headless(params):
    model = IntersectionModel(params)
    model.run(display=False)
    return model.get_results()

# runs the same traffic once with each light. Returns (normal_results, smartflow_results)
def run_both(params):
    normal_params = params.copy()
    normal_params["controller"] = "normal"
    smartflow_params = params.copy()
    smartflow_params["controller"] = "smartflow"
    return run_headless(normal_params), run_headless(smartflow_params)

# averages several results dictionaries (one per seed) into one
def average_results(list_of_results):
    averaged = {}
    for key in list_of_results[0]:
        total = 0
        for results in list_of_results:
            total = total + results[key]
        averaged[key] = total / len(list_of_results)
    return averaged

# compares SmartFlow to Normal. Returns the text (like "-35%") and whether it is "good", "bad" or "same"
def get_change(normal_value, smartflow_value, lower_is_better):
    if normal_value == 0:
        if smartflow_value == 0:
            return "0%", "same"
        return "-", "same"

    change_percent = 100 * (smartflow_value - normal_value) / normal_value
    rounded = round(change_percent)

    if rounded > 0:
        text = "+" + str(rounded) + "%"
    else:
        text = str(rounded) + "%"

    if rounded == 0:
        return text, "same"

    if lower_is_better == True:
        if rounded < 0:
            return text, "good"
        return text, "bad"
    else:
        if rounded > 0:
            return text, "good"
        return text, "bad"

# builds the rows of the comparison table (as text, ready to print)
def build_table_rows(normal_results, smartflow_results, arrival_seconds):
    rows = []
    for metric in METRIC_ROWS:
        normal_value = normal_results[metric["key"]]
        smartflow_value = smartflow_results[metric["key"]]
        change_text, change_kind = get_change(normal_value, smartflow_value, metric["lower_is_better"])

        row = {}
        row["label"] = get_metric_label(metric, arrival_seconds)
        row["normal"] = format_value(normal_value, metric["kind"])
        row["smartflow"] = format_value(smartflow_value, metric["kind"])
        row["change"] = change_text
        row["change_kind"] = change_kind
        rows.append(row)
    return rows