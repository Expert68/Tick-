list = []
with open(r'input/IF1204_20120418.txt','r',encoding='utf-8') as f:
    for line in f:
        data = line.split('\t')
        list.append(data)

print(list)