import json

def dump_info(data, filename):
    with open(f"out\\{filename}", "w") as output_file:
        output_file.write(json.dumps(data, indent=4))

    return data


def dump_stats(registered_dead_voters, dead_voters_who_voted):
    data = {
        "RegisteredDeadVoters": len(registered_dead_voters),
        "DeadVotersWhoVoted": len(dead_voters_who_voted),
        "Percent": "{:.2%}".format(float(len(dead_voters_who_voted)/len(registered_dead_voters)))
    }
    dump_info(data, "info_dump.json")

    return data


def read_file(filename, batch_size):
    batch = []
    batches = []
    count = 0

    with open(filename) as detroit_index:
        for line in detroit_index:
            if count < batch_size:
                batch.append(line)
                count += 1
            else:
                count = 0
                batches.append(batch)
                batch = []

    if len(batch) > 0:
        batches.append(batch)
    
    return batches