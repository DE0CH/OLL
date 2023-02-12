# Tuning the One Lambda Lambda Algorithm with irace

## One Lambda Lambda implemented in Rust

As an effort to to make the algorithm run faster, we have implemented the One Lambda Lambda algorithm in Rust and made a python binding so that it can be called from python. See `onell_algs_rs` for the source code.

## Tuning the One Lambda Lambda algorithm with irace

See the folder `tuned-with-irace` for the source code and checkout `tuned-with-irace/README.md` for more details.

## Exact Computation of Runtimes and Approximations of Best Policies

See the folder `optimal-policies` for the source code. Use the `run.bash` to reproduce experiments, which will take a lot of time though. Tested with Scala 2.13.
