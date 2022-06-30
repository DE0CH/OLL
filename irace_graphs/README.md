# Graphs for Irace

The json files are the data used to graph the image. They don't have labels because they are distinguished by their location in the list. From index 0 to index 7, they are the data for:

- Dynamic Lambda
- Dynamic Lambda with Binning
- Static Lambda 
- Random Dynamic Lambda 
- Random Static Lambda 
- Lambda = 1
- Dynamic Theory
- Five Parameters

With only the json file, you can reproduce the png by running (in the parent folder. i.e. the project root folder)

```bash
python3 irace_grapher_full.py irace_graphs
```

The code is not very easy to follow because it also contains logic for it to be integrated into the runner process. The important part that calls `matplotlib.pyplot` is in `config.graph` (the `graph` function in `config.py`). 
