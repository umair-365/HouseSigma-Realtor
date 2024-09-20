import json
import os


def update_broker_list(broker_list):
    broker_file = 'database/brokers.json'
    
    if not os.path.exists(broker_file):
        file = open(broker_file, 'w')
        file.close()
    
    data = read_file(broker_file)
    
    if data:
        data = json.loads(data)
        unique_brokers = get_unique_brokers(data, broker_list)
    else:
        unique_brokers = get_unique_brokers(broker_list, list())

    save_file(broker_file, unique_brokers)


def save_file(filename, data):
    # Save Data in JSON
    file = open(filename, 'w')
    json.dump(data, file)
    file.close()


def read_file(filename):
    # Read data from JSON file
    file = open(filename, 'r')
    data = ''.join([v.strip() for v in file.readlines() if v.strip()])
    file.close()

    return data


def get_unique_brokers(broker_list1, broker_list2):
    """
        Remove Duplicate Brokers
    """
    done_brokers = list()
    unique_brokers = list()
    for broker in broker_list1+broker_list2:
        key = broker['name'] + str(broker['website'])
        if key not in done_brokers:
            done_brokers.append(key)
            unique_brokers.append(broker)

    return unique_brokers


def update_file(property_object):
    output_file = 'database/listings.json'

    if not os.path.exists(output_file):
        file = open(output_file, 'w')
        file.close()

    data = read_file(output_file)

    # Update JSON Data
    updated_list = list()
    property_found = False
    if data:
        data = json.loads(data)
        for _property in data:
            if _property['location'] == property_object['location']:
                property_found = True

                updated_data = dict()
                updated_data['location'] = property_object['location']
                updated_data['history'] = property_object['history']
                updated_data['brokers'] = get_unique_brokers(_property['brokers'], property_object['brokers'])
                updated_list.append(updated_data)

            else:
                updated_list.append(_property)

    if not property_found:
        updated_list.append(property_object)

    save_file(output_file, updated_list)




