import json

def readinstances():
    f = open('instances.json')
    data = json.load(f)
    # for i in data:
    #     print(i['name'])
    return data

if __name__ == "__main__":
    readinstances()