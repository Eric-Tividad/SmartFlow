# main program. run SmartFlow here

# by running this, terminal ask you to input:
#   1 = Normal traffic lights
#   2 = SmartFlow traffic lights

# then opens the Pygame window and runs that mode for 30 seconds
# when the run ends, the window closes, the results are printed in the terminal, and you are asked if you want to run again

# Headless (no window): runs ONE seeded run with both lights and prints the comparison table
#   python main.py --headless

# For results averaged over many runs, use compare.py

import argparse
import config
import metrics
from visualizer import Viewer

# terminal asking user which mode to use
def ask_mode():
    print("")
    print("SmartFlow traffic simulation")
    print("  1 = Normal traffic lights")
    print("  2 = SmartFlow traffic lights")

    while True:
        answer = input("Enter 1 or 2 (q to quit): ").strip().lower()
        if answer == "1":
            return "normal"
        if answer == "2":
            return "smartflow"
        if answer == "q":
            return None
        print("Please type 1 or 2.")

def ask_run_again():
    print("")
    while True:
        answer = input("Run again? (y/n): ").strip().lower()
        if answer == "y" or answer == "yes":
            return True
        if answer == "n" or answer == "no":
            return False
        print("Please type y or n.")

def run_with_window():
    while True:
        mode_name = ask_mode()
        if mode_name is None:
            break

        viewer = Viewer(mode_name)
        run_finished = viewer.run()

        if run_finished == True:
            metrics.print_run_results(viewer.model.controller.name, viewer.model.get_results(),
                                      viewer.arrival_seconds)
        else:
            print("")
            print("The run was stopped before it finished, so there are no results.")

        if ask_run_again() == False:
            break

    print("Bye!")

def run_headless(seed):
    params = config.DEFAULT_PARAMS.copy()
    params["seed"] = seed

    normal_results, smartflow_results = metrics.run_both(params)
    rows = metrics.build_table_rows(normal_results, smartflow_results, metrics.get_arrival_seconds(params))

    print("")
    print("Metric".ljust(28) + "Normal".rjust(14) + "SmartFlow".rjust(16) + "Change".rjust(12))
    print("-" * 70)
    for row in rows:
        print(row["label"].ljust(28) + row["normal"].rjust(14) + row["smartflow"].rjust(16) + row["change"].rjust(12))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seed", type=int, default=config.DEFAULT_PARAMS["seed"])
    args = parser.parse_args()

    if args.headless == True:
        run_headless(args.seed)
    else:
        try:
            run_with_window()
        except KeyboardInterrupt:
            # Ctrl+C in the terminal: leave quietly instead of showing an error.
            print("")
            print("Bye!")

if __name__ == "__main__":
    main()