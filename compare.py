# comparing both modes through many runs with different random seeds, averages the results, 
# prints a table for each scenario, and saves results.csv

import config
import metrics

SEEDS = [1, 2, 3, 4, 5]

# each scenario changes some of the default settings (here: how busy each road is)
SCENARIOS = [
    {"name": "Default traffic (North/South busier)",
     "changes": {}},

    {"name": "Uneven traffic (North/South heavy, East/West light)",
     "changes": {"spawn_probs": {"N": 0.030, "S": 0.030, "E": 0.004, "W": 0.004}}},

    {"name": "Even traffic (same in every lane)",
     "changes": {"spawn_probs": {"N": 0.015, "S": 0.015, "E": 0.015, "W": 0.015}}},
]

def print_table(title, rows):
    print("")
    print(title)
    print("-" * 74)
    print("Metric".ljust(28) + "Normal".rjust(14) + "SmartFlow".rjust(16) + "Change".rjust(12))
    print("-" * 74)
    for row in rows:
        print(row["label"].ljust(28) + row["normal"].rjust(14) + row["smartflow"].rjust(16) + row["change"].rjust(12))

def main():
    csv_lines = ["scenario,metric,normal,smartflow,change"]

    for scenario in SCENARIOS:
        normal_list = []
        smartflow_list = []
        for seed in SEEDS:
            params = config.DEFAULT_PARAMS.copy()
            for key in scenario["changes"]:
                params[key] = scenario["changes"][key]
            params["seed"] = seed

            normal_results, smartflow_results = metrics.run_both(params)
            normal_list.append(normal_results)
            smartflow_list.append(smartflow_results)

        normal_average = metrics.average_results(normal_list)
        smartflow_average = metrics.average_results(smartflow_list)
        arrival_seconds = metrics.get_arrival_seconds(params)
        rows = metrics.build_table_rows(normal_average, smartflow_average, arrival_seconds)

        print_table(scenario["name"] + "  [average of " + str(len(SEEDS)) + " runs]", rows)
        for row in rows:
            csv_lines.append('"' + scenario["name"] + '","' + row["label"] + '",' +
                             row["normal"] + "," + row["smartflow"] + "," + row["change"])

    csv_file = open("results.csv", "w")
    for line in csv_lines:
        csv_file.write(line + "\n")
    csv_file.close()
    print("")
    print("Saved results.csv")


if __name__ == "__main__":
    main()