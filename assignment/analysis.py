import json
import sys
from collections import defaultdict
def count_labels(f):
    input_json = json.load(f)
    labels = defaultdict(set)
    for f in input_json['functions']:
        name = f['name']
        for i in f['instrs']:
            if i.get("label"):
                labels[name].add(i['label'])
    ans = {}
    for k,v in labels.items():
        ans[k] = sorted(list(v))
    sys.stdout.write(str(ans))
    return ans

if __name__ == "__main__":
    f = open("/Users/fangchenxin/Desktop/bril/test/print/eight-queens.json")
    count_labels(f)


