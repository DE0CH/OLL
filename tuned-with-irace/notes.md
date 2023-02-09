# Note for myself 

## Types
All baseline comparison 
1. Dynamic 
2. Dynamic Bin 
3. Static 

Binning Comparison
4. Binning Comparison

All inherit from irace_laucher/IraceCaller

Decide to separate dynamic bin and binning comparison because too much difference

1. Dynamic Comparison need to pass down the descend rate in the instances file. 
2. The name formats of the files need to change. 

This means need to change public API, breaking previous code
Overall, the duplication of code is minimal compared to the careful modification to update users of the API. 

## TODOs

- In binning comparison, both calculating the performance (the 500 trials) and pulling all the performance together into a png are both called grapher, run separately. Should give them different names
- performance... refers to baseline comparison but performance_binning_comparison refers to binning comparison, should refactor performance... to performance_baseline. 
