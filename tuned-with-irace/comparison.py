import onell_algs
import onell_algs_rs
import numpy
import config

sizes = [10, 20, 30, 50, 80, 100, 200, 500, 1000, 2000]
rng = numpy.random.default_rng(config.seed)
trials = 500
def rint(rng):
  return rng.integers(1<<15, (1<<16)-1)

for size in sizes:
  print(f"for size = {size}")
  dynamic_theory_rs = sum([onell_algs_rs.onell_dynamic_theory(size, rint(rng), config.get_cutoff(size)) for _ in range(trials)]) / trials
  print(dynamic_theory_rs)
  dynamic_theory_py = sum([onell_algs.onell_dynamic_theory(size, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(dynamic_theory_py)
  dynamic_theory_py = sum([onell_algs.onell_dynamic_theory(size, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(dynamic_theory_py)

  print()
  static_lambda_value = (rng.random() * (size-1)) + 1
  static_lbd_rs = sum([onell_algs_rs.onell_lambda(size, [static_lambda_value]*size, rint(rng), config.get_cutoff(size)) for _ in range(trials)]) / trials
  print(static_lbd_rs)
  static_lbd_py = sum([onell_algs.onell_lambda(size, lbds=[static_lambda_value] * size, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(static_lbd_py)
  static_lbd_py = sum([onell_algs.onell_lambda(size, lbds=[static_lambda_value] * size, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(static_lbd_py)

  print()
  five_parameters_rs = sum([onell_algs_rs.onell_five_parameters(size, rint(rng), config.get_cutoff(size)) for _ in range(trials)]) / trials
  print(five_parameters_rs)
  five_parameters_py = sum([onell_algs.onell_dynamic_5params(size, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(five_parameters_py)
  five_parameters_py = sum([onell_algs.onell_dynamic_5params(size, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(five_parameters_py)

  print()
  dynamic_lbd_value = [rng.integers(1, size) for _ in range(size)]
  dynamic_lbd_rs = sum([onell_algs_rs.onell_lambda(size, dynamic_lbd_value, rint(rng), config.get_cutoff(size)) for _ in range(trials)]) / trials
  print(dynamic_lbd_rs)
  dynamic_lbd_py = sum([onell_algs.onell_lambda(size, lbds=dynamic_lbd_value, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(dynamic_lbd_py)
  dynamic_lbd_py = sum([onell_algs.onell_lambda(size, lbds=dynamic_lbd_value, seed=rint(rng), max_evals=config.get_cutoff(size))[2] for _ in range(trials)]) / trials
  print(dynamic_lbd_py)

