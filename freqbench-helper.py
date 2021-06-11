import requests
import json
import urllib.request
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import os
import os.path
from os import path
import sys
import re
import statistics
import csv

sep = "-"
while True:
    print("\nDo your like to use your own Json data \nor would u like me to fetch it for you?\n")
    print(sep * 35 + "\n1 = fetch from online \n2 = no i will use my own Json file\n"+ sep * 35 +"\n")
    print("Please enter your choice:")
    response = input(">")
    if response not in ["2","1"]:
        print("\nWrong input, please choose a valid choice from the options")
        continue
    else:
        break


if response == '1':
    while True:
        try:
            print("\nFor which SOC you want to fetch data for?")
            name = input("> ")
            soc_url = ("https://github.com/kdrag0n/freqbench/tree/master/results/" + name)
            r = requests.get(soc_url)
            if 'Page not found' not in r.text:
                break
            print("Given SOC was not found on Freqbench data sets, try again")
        except Exception as e:
            print(e)

    num = 1
    object_list = []
    num_list = []
    print("\nchecking available result types\n")
    res = requests.get(soc_url)
    soup = BeautifulSoup(res.text, 'html5lib')
    print(sep * 35 + "\navailable Results for " + name + " are:\n")
    for items in soup.find_all('a', attrs={"class":"js-navigation-open Link--primary"}):
        item_list = (items.get("title"))
        lines = item_list.split("\n")
        for i in range(len(lines)):
            object_list.append(lines[i])
            lines[i] = (str(num) + ". " + lines[i])
            num_list.append(str(num))
            num = (num + 1)

        final_list = "\n".join(lines)
        print(final_list)
    print(sep * 35)

    while True:
        try:
            print("Please chose your choice of data from -> ", num_list)
            selec = input("> ")
            if selec in num_list:
                break
            print(str(selec) + " was not found in choice menu, Try again")
        except Exception as e:
            print(e)

    maker = (num_list.index(selec))
    final_type = (object_list[maker])

    print("Okay, so:")
    print(sep * 30)
    print("SOC -> " + name)
    print("Result Type -> " + final_type)
    print(sep * 30)
    nav_url = ("https://raw.githubusercontent.com/kdrag0n/freqbench/master/results" + "/" + name + "/" + final_type)

else:
    print("Please enter your Json file name")
    print("*Make sure you have file in the program directory*")
    file = input("> ")
    if path.exists(file):
        pass
    else:
        print("No file found with the name -> " + file)
        print("make sure you have the Json file inside program directory")
        quit()

def Enquiry(lis1):
    if lis1:
        return 1
    else:
        return 0

def var_check(my_var):
    try:
        my_var
    except NameError:
        my_var = None

def cal_efficient_freqs():
    print("efficient freq calculation is fully based on kdrag0n's script")
    if response == '1':
        final_url = (nav_url + "/results.json")
        with urllib.request.urlopen(final_url) as url:
            json_data = json.loads(url.read().decode())
    else:
        f = open(file,)
        json_data = json.load(f)
    cpus_data = json_data["cpus"]
    for cpu, cpu_data in cpus_data.items():
        cpu = int(cpu)
        print(f"cpu{cpu}:")

        eff_freqs = set()

        # Start with the most efficient freq
        freqs = cpu_data["freqs"]
        max_eff_freq, max_eff = max(
                        ((int(freq), freq_data["active"]["ulpmark_cm_score"]) for freq, freq_data in freqs.items()),
                        key=lambda opp: opp[1]
        )
        print("Most efficient freq: " + str(max_eff_freq), str(max_eff))
        eff_freqs.add(max_eff_freq)

        # Add the max freq
        max_freq = max(int(freq) for freq in freqs.keys())
        max_freq_eff = freqs[str(max_freq)]["active"]["ulpmark_cm_score"]
        eff_freqs.add(max_freq)

        # Add efficient intermediate freqs
        last_freq = max_eff_freq
        freq_keys = list(map(int, freqs.keys()))
        for freq_i, (freq, freq_data) in enumerate(freqs.items()):
            freq = int(freq)
            eff = freq_data["active"]["ulpmark_cm_score"]

            # Clock compensation: if 500 MHz passed with no freq step
            if freq - last_freq < 500000:
                # Ignore freqs slower than most efficient
                if freq < max_eff_freq:
                    continue

                # Less efficient than max freq
                if eff < max_freq_eff:
                    continue

            last_freq = freq
            eff_freqs.add(freq)
            print(freq)

        # Remove inefficient freqs
        ineff_freqs = freqs.keys() - eff_freqs
        for freq in ineff_freqs:
            del freqs[str(freq)]

        print()

def cal_energy_model(idle_cost_data):
    print("energy calculation is fully based on kdrag0n's script,")
    if response == '1':
        final_url = (nav_url + "/results.json")
        with urllib.request.urlopen(final_url) as url:
            json_data = json.loads(url.read().decode())
    else:
        f = open(file,)
        json_data = json.load(f)

    if len(sys.argv) > 2:
        key_type, value_type = sys.argv[2].split("/")
    else:
        key_type = "freq"
        value_type = "power"

    if len(sys.argv) > 3:
        old_model = {"core": [], "cluster": []}

        # Example:
        # {
        #     "core": [
        #         {
        #             "busy": [1, 2, 3, 4, 5, 6],
        #             "idle": [3, 2, 1],
        #         },
        #         {
        #             "busy": [10, 20, 30, 40, 50, 60],
        #             "idle": [5, 3, 2],
        #         },
        #     ],
        #     "cluster": [
        #         {
        #             "busy": [1, 1, 1, 2, 3, 3],
        #             "idle": [2, 2, 1],
        #         },
        #         {
        #             "busy": [2, 2, 3, 4, 4, 5],
        #             "idle": [4, 2, 1],
        #         },
        #     ],
        # }

        with open(sys.argv[3], "r") as f:
            old_dtsi = f.read().split("\n")

        # Rudimentary line-by-line DTS parser, will break with unexpected data
        cpu_i = -1
        data_block = None
        cost_block = None
        for line in old_dtsi:
            match = re.search(r"(core|cluster)-cost(\d+)\s+\{", line)
            if match:
                new_data_block = match.group(1)
                if new_data_block == data_block:
                    cpu_i += 1
                else:
                    cpu_i = 0

                data_block = new_data_block
                old_model[data_block].append({})
                continue

            match = re.search(r"(busy|idle)-cost-data\s+=", line)
            if match:
                cost_block = match.group(1)
                old_model[data_block][cpu_i][cost_block] = []
                continue

            if cost_block == "busy":
                match = re.search(r"^\s*(\d+)\s+(\d+)\s*$", line)
                if match:
                    key = int(match.group(1))
                    value = int(match.group(2))

                    # Ignore keys (cap/freq) and use indices instead
                    # Assumption: all freqs are present in both
                    old_model[data_block][cpu_i]["busy"].append(value)
            elif cost_block == "idle":
                if re.match(r"^\s*(?:\d+\s*)+$", line):
                    # Extend array to accommodate single-line costs, e.g. qcom format
                    idle_costs = [int(cost) for cost in re.split(r"\s+", line.strip())]
                    old_model[data_block][cpu_i]["idle"] += idle_costs

            if re.match(r"^\s*>;\s*$", line):
                cost_block = None
    else:
        old_model = None

    cpus_data = json_data["cpus"]
    DTS_HEADER = """/*
     * Auto-generated legacy EAS energy model for incorporation in SoC device tree.
     * Generated by freqbench post processing scripts using freqbench results.
     * More info at https://github.com/kdrag0n/freqbench
     */
    / {
    \tcpus {"""

    print(DTS_HEADER, end="")

    # Performance efficiency
    unscaled_cpu_cm_mhz = {}
    for cpu, cpu_data in cpus_data.items():
        last_freq, last_freq_data = max(cpu_data["freqs"].items(), key=lambda f: f[0])
        cm_mhz = last_freq_data["active"]["coremarks_per_mhz"]
        unscaled_cpu_cm_mhz[int(cpu)] = cm_mhz

    # Scale performance efficiency
    max_cm_mhz = max(unscaled_cpu_cm_mhz.values())
    scaled_cpu_cm_mhz = {
                    cpu: cm_mhz / max_cm_mhz * 1024
                    for cpu, cm_mhz in unscaled_cpu_cm_mhz.items()
    }

    # Pass 1: performance efficiency (for capacity scaling)
    for cpu, cpu_data in cpus_data.items():
        cpu = int(cpu)

        cm_mhz_norm = scaled_cpu_cm_mhz[cpu]

        lb = "{"
        rb = "}"
        print(f"""
\t\tcpu@{0 if cpu == 1 else cpu} {lb}
\t\t\tefficiency = <{cm_mhz_norm:.0f}>;
\t\t\tcapacity-dmips-mhz = <{cm_mhz_norm:.0f}>;
\t\t{rb};""")

    print("""\t};
    \tenergy_costs: energy-costs {
    \t\tcompatible = "sched-energy";""")

    max_perf = max(
                    max(freq["active"]["coremark_score"]
                    for freq in cpu["freqs"].values()) for cpu in cpus_data.values()
    )

    # Pass 2: core costs
    core_cost_keys = []
    for cpu_i, (cpu, cpu_data) in enumerate(cpus_data.items()):
        cpu = int(cpu)
        core_cost_keys.append([])

        lb = "{"
        rb = "}"
        print(f"""
\t\tCPU_COST_{cpu_i}: core-cost{cpu_i} {lb}
\t\t\tbusy-cost-data = <""")

        for freq, freq_data in cpu_data["freqs"].items():
            freq = int(freq)

            if value_type == "power":
                value = freq_data["active"]["power_mean"]
            elif value_type == "energy":
                value = freq_data["active"]["energy_millijoules"]

            if key_type == "freq":
                key = freq
                print(f"\t\t\t\t{key: 8.0f}{value: 5.0f}")
            elif key_type == "cap":
                # Floor to match CPU integer math
                key = freq_data["active"]["coremark_score"] / max_perf * 1024
                print(f"\t\t\t\t{key: 5.0f}{value: 5.0f}")

            core_cost_keys[cpu_i].append(key)

        if old_model:
            idle_costs = " ".join(map(str, old_model["core"][cpu_i]["idle"]))
        else:
            # Placeholder in lieu of real data
            idle_costs = idle_cost_data

        print(f"""\t\t\t>;
\t\t\tidle-cost-data = <
\t\t\t\t{idle_costs}
\t\t\t>;
\t\t{rb};""")

    # Pass 3: cluster costs
    if old_model:
        for cpu_i, new_keys in enumerate(core_cost_keys):
            lb = "{"
            rb = "}"
            print(f"""
\t\tCLUSTER_COST_{cpu_i}: cluster-cost{cpu_i} {lb}
\t\t\tbusy-cost-data = <""")

            for cost_i, cost in enumerate(old_model["cluster"][cpu_i]["busy"]):
                # Ignore silently for now instead of logging to stderr to make copy-pasting easier
                # This happens with qcom speed bin differences on newer SoCs
                if cost_i >= len(new_keys):
                    continue

                key = new_keys[cost_i]
                print(f"\t\t\t\t{key: 5.0f}{cost: 5.0f}")

            idle_costs = " ".join(map(str, old_model["cluster"][cpu_i]["idle"]))

            print(f"""\t\t\t>;
\t\t\tidle-cost-data = <
\t\t\t\t{idle_costs}
\t\t\t>;
\t\t{rb};""")

    print("""\t};
    };""")

def cal_minimal_energy_model():
    print("minimal energy model calculation is fully based on kdrag0n's script")
    if response == '1':
        final_url = (nav_url + "/results.json")
        with urllib.request.urlopen(final_url) as url:
            json_data = json.loads(url.read().decode())
    else:
        f = open(file,)
        json_data = json.load(f)

    cpus_data = json_data["cpus"]
    DTS_HEADER = """/*
     * Auto-generated simplified EAS energy model for incorporation in SoC device tree.
     * Generated by freqbench post processing scripts using freqbench results.
     * More info at https://github.com/kdrag0n/freqbench
     */
    / {
    \tcpus {"""

    print(DTS_HEADER)

    mode = "power"
    voltages = {}
    for arg in sys.argv[2:]:
        cluster, freq, voltage = map(int, re.split(r"\.|=", arg))
        voltages[(cluster, freq)] = voltage

    # Performance efficiency
    unscaled_cpu_cm_mhz = {}
    for cpu, cpu_data in cpus_data.items():
        last_freq, last_freq_data = max(cpu_data["freqs"].items(), key=lambda f: f[0])
        cm_mhz = last_freq_data["active"]["coremarks_per_mhz"]
        unscaled_cpu_cm_mhz[int(cpu)] = cm_mhz

    # Scale performance efficiency
    max_cm_mhz = max(unscaled_cpu_cm_mhz.values())
    scaled_cpu_cm_mhz = {
                    cpu: cm_mhz / max_cm_mhz * 1024
                    for cpu, cm_mhz in unscaled_cpu_cm_mhz.items()
    }

    for cpu, cpu_data in cpus_data.items():
        cpu = int(cpu)

        dpcs = []
        for freq, freq_data in cpu_data["freqs"].items():
            freq = int(freq)

            if (cpu, freq) not in voltages:
                continue

            if mode == "power":
                # µW
                cost = freq_data["active"]["power_mean"] * 1000
            elif mode == "energy":
                cost = freq_data["active"]["energy_millijoules"] * 10

            mhz = freq / 1000
            v = voltages[(cpu, freq)] / 1_000_000

            dpc = cost / mhz / v**2
            dpcs.append(dpc)

        cm_mhz_norm = scaled_cpu_cm_mhz[cpu]
        if dpcs:
            dpc = statistics.mean(dpcs)
        else:
            dpc = 0

        lb = "{"
        rb = "}"
        print(f"""\t\tcpu@{0 if cpu == 1 else cpu} {lb}
\t\t\tefficiency = <{cm_mhz_norm:.0f}>;
\t\t\tcapacity-dmips-mhz = <{cm_mhz_norm:.0f}>;
\t\t\tdynamic-power-coefficient = <{dpc:.0f}>;
\t\t{rb};
""")

    print("""\t};
    };""")

def int_freq_efficiency_graph():
    # create all empty lists and variables that we will need later
    one = "no"
    one_four = "no"
    one_four_seven = "no"
    one_four_six = "no"
    one_four_six_seven = "no"
    one_seven = "no"
    one_six = "no"
    one_six_seven = "no"
    cpu_freqs_1 = []
    cpu_freqs_4 = []
    cpu_freqs_6 = []
    cpu_freqs_7 = []
    cpu_effs_1 = []
    cpu_effs_4 = []
    cpu_effs_6 = []
    cpu_effs_7 = []

    if response == '1':
        final_url = (nav_url + "/results.json")
        with urllib.request.urlopen(final_url) as url:
            json_data = json.loads(url.read().decode())
    else:
        f = open(file,)
        json_data = json.load(f)
    cpus_data = json_data["cpus"]

    for cpu, cpu_data in cpus_data.items():
        cpu = str(cpu)
        cpu_data = cpus_data[cpu]
        for freqs in cpu_data.items():
            eff_freqs = set()

            # Start with the most efficient freq
            freqs = cpu_data["freqs"]
            max_eff_freq, max_eff = max(
                ((int(freq), freq_data["active"]["ulpmark_cm_score"]) for freq, freq_data in freqs.items()),
                key=lambda opp: opp[1]
            )
            #print("Most efficient freq: " + str(max_eff_freq), str(max_eff))
            eff_freqs.add(max_eff_freq)

            # Add the max freq
            max_freq = max(int(freq) for freq in freqs.keys())
            max_freq_eff = freqs[str(max_freq)]["active"]["ulpmark_cm_score"]
            eff_freqs.add(max_freq)

            # Add efficient intermediate freqs
            last_freq = max_eff_freq
            freq_keys = list(map(int, freqs.keys()))
            for freq_i, (freq, freq_data) in enumerate(freqs.items()):
                freq = str(freq)
                eff = freq_data["active"]["ulpmark_cm_score"]

                last_freq = freq
                eff_freqs.add(freq)

                # Append all freqs and efficiency score to list according to the core cluster they belong to
                if cpu == "1":
                    cpu_freqs_1.append(freq)
                    cpu_effs_1.append(eff)
                elif cpu == "4":
                    cpu_freqs_4.append(freq)
                    cpu_effs_4.append(eff)
                elif cpu == "6":
                    cpu_freqs_6.append(freq)
                    cpu_effs_6.append(eff)
                elif cpu == "7":
                    cpu_freqs_7.append(freq)
                    cpu_effs_7.append(eff)
    # detect what cluster core combination the soc has and name it according to it
    if Enquiry(cpu_freqs_1):
        if Enquiry(cpu_freqs_4):
            one_four = "yes"
            if Enquiry(cpu_freqs_6):
                one_four_six = "yes"
                if Enquiry(cpu_freqs_7):
                    one_four_six_seven = "yes"
            elif Enquiry(cpu_freqs_7):
                one_four_seven = "yes"

    if Enquiry(cpu_freqs_1):
        if Enquiry(cpu_freqs_6):
            one_six = "yes"
            if Enquiry(cpu_freqs_7):
                one_six_seven = "yes"

    if Enquiry(cpu_freqs_1):
        if Enquiry(cpu_freqs_7):
            one_seven = "yes"

    if (cpu_freqs_1):
        if not(cpu_freqs_4):
            if not(cpu_freqs_6):
                if not(cpu_freqs_7):
                    one = "yes"

    # Plot graph according to the Core cluster combination
    if (one == "yes"):
        freqs = cpu_freqs_1
        values = cpu_effs_1
        fig = plt.figure(figsize = (10, 5))
        plt.bar(freqs, values, color ='b',
        width = 0.4)
        plt.xlabel("All freqs of " + name)
        plt.ylabel("efficiency score")
        plt.title("efficiency score graph for all freqs in " + name)
        plt.show()

    elif(one_four_seven == "yes"):
        fig, axs = plt.subplots(3)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_4
        values = cpu_effs_4
        axs[1].bar(freqs, values, color='b', label='Big')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[1].set_ylabel("efficiency score")

        freqs = cpu_freqs_7
        values = cpu_effs_7
        axs[2].bar(freqs, values, color='g', label='Prime')
        axs[2].legend()
        axs[2].set_xlabel("All freqs of " + name + "'s Prime Core")
        axs[2].set_ylabel("efficiency score")
        plt.show()

    elif(one_four_six == "yes"):
        fig, axs = plt.subplots(3)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_4
        values = cpu_effs_4
        axs[1].bar(freqs, values, color='b', label='Big')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[1].set_ylabel("efficiency score")

        freqs = cpu_freqs_6
        values = cpu_effs_6
        axs[2].bar(freqs, values, color='g', label='Prime')
        axs[2].legend()
        axs[2].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[2].set_ylabel("efficiency score")
        plt.show()

    elif(one_six_seven == "yes"):
        fig, axs = plt.subplots(3)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_6
        values = cpu_effs_6
        axs[1].bar(freqs, values, color='b', label='Big')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[1].set_ylabel("efficiency score")

        freqs = cpu_freqs_7
        values = cpu_effs_7
        axs[2].bar(freqs, values, color='g', label='Prime')
        axs[2].legend()
        axs[2].set_xlabel("All freqs of " + name + "'s Prime Core")
        axs[2].set_ylabel("efficiency score")
        plt.show()

    elif(one_four_six_seven == "yes"):
        fig, axs = plt.subplots(4)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_4
        values = cpu_effs_4
        axs[1].bar(freqs, values, color='b', label='Big')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[1].set_ylabel("efficiency score")

        freqs = cpu_freqs_6
        values = cpu_effs_6
        axs[2].bar(freqs, values, color='y', label='Big')
        axs[2].legend()
        axs[2].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[2].set_ylabel("efficiency score")

        freqs = cpu_freqs_7
        values = cpu_effs_7
        axs[3].bar(freqs, values, color='g', label='Prime')
        axs[3].legend()
        axs[3].set_xlabel("All freqs of " + name + "'s Prime Core")
        axs[3].set_ylabel("efficiency score")
        plt.show()

    elif (one_four == "yes"):
        fig, axs = plt.subplots(2)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_4
        values = cpu_effs_4
        axs[1].bar(freqs, values, color='b', label='Big')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[1].set_ylabel("efficiency score")
        plt.show()

    elif (one_six == "yes"):
        fig, axs = plt.subplots(2)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_6
        values = cpu_effs_6
        axs[1].bar(freqs, values, color='b', label='Big')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Big Core")
        axs[1].set_ylabel("efficiency score")
        plt.show()

    elif (one_seven == "yes"):
        fig, axs = plt.subplots(2)
        freqs = cpu_freqs_1
        values = cpu_effs_1
        axs[0].bar(freqs, values, color='r', label='Little')
        axs[0].legend()
        axs[0].set_xlabel("All freqs of " + name + "'s Little Core")
        axs[0].set_ylabel("efficiency score")

        freqs = cpu_freqs_7
        values = cpu_effs_7
        axs[1].bar(freqs, values, color='g', label='Prime')
        axs[1].legend()
        axs[1].set_xlabel("All freqs of " + name + "'s Prime Core")
        axs[1].set_ylabel("efficiency score")
        plt.show()

    else:
        pass

# Menu table for taking input from user
while True:
    print("\nOkay, what do want to do? \n")
    print(sep * 100)
    print("1 = list all efficient freqs")
    print("2 = calculate Legacy Energy Model (for soc that uses kernel below Linux ver 4.19)")
    print("3 = calculate Simplified Energy Model (for soc that uses Linux ver 4.19 and above)")
    print("4 = Plot Graph for analyzing CPU freq efficiency")
    print(sep * 100 + '\n')
    print("Please enter your choice > ")
    work = input("> ")
    if work not in ["4","3","2","1"]:
        print("\nWrong input, please choose a valid choice from the options")
        continue
    else:
        break

if work == '1':
    cal_efficient_freqs()
elif work == '2':
    print("Please enter your CPU idle cost data")
    idle_cost_input = input("> ")
    cal_energy_model(idle_cost_input)
elif work == '3':
    cal_minimal_energy_model()
else:
    int_freq_efficiency_graph()
