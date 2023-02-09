# Tuning One Lambda Lambda Algorithm with irace

## Installation

1. Install R and irace. See [irace Quickstart](https://github.com/mLopez-Ibanez/irace#quick-start) for more details.
1. Install the python dependencies with `pip install -r requirements.txt`
1. Build and install the One Lambda Lambda algorithm implemented in rust. Due to the highly developmental nature of this project, it is not pushed to pip and its distributed only as source code. So you will have to build it and install it manually. Sorry about that. 
    1. [Install rust and cargo](https://www.rust-lang.org/tools/install). 
    1. Navigate to `/onell_algs_rs` folder
    1. Install [maturin](https://pypi.org/project/maturin/). 
    1. Build the python wheel with `python -m maturin build`.
    1. Install the python wheel with `pip install /path/to/wheel.whl`. The output of maturing should tell you where the wheel is.

## Reproduction

With all the dependencies installed, you should be able to reproduce the results (with the caveat of [issue #18](https://github.com/DE0CH/OLL/issues/18)) by just running 

```bash 
python irace_load_distributor.py full
```

Wait for weeks, months, or even years. And then format the result into a nice json file with

```
python format_output.py --nl
```

I am sorry in advance for really messy code structure. It is the result of me trying to find the most lazy and hacky way to add some functionality or new configuration to the code while trying to not change the old code (lest it breaks), making improvements, and making sure that all the results can be reproduced with just one command. 

## Documentation

There is not much documentation because most of the code is very ad-hoc not reusable (again, sorry for the poor code quality) and me thinking that not many people would bother to read it. If you do have any question, please feel free to open an in the [github repo](https://github.com/DE0CH/OLL), I will be more than happy to answer you.
