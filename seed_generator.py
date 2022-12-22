import numpy as np
from config import seed, N, M

rng = np.random.default_rng(seed)

[(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1)) for i in range(N)]
seeds = []
for i in range(N): # Seed batch 1 
  seeds.append((list(rng.integers(1<<15, (1<<16)-1, 11)), list(rng.integers(1<<15, (1<<16)-1, 11))))
for i in range(N): # Seed batch 2
  one, two = seeds[i]
  if M > 11:
    one += list(rng.integers(1<<15, (1<<16)-1, M - 11))
    two += list(rng.integers(1<<15, (1<<16)-1, M - 11))
  else:
    one = one[:M]
    two = two[:M]
  seeds[i] = (one, two) 
for i in range(N):
  (i, list(rng.integers(1<<15, (1<<16)-1, M)), list(rng.integers(1<<15, (1<<16)-1, M)))
[(i, rng.integers(1<<15, (1<<16)-1), rng.integers(1<<15, (1<<16)-1)) for i in range(N)]
rng.integers(1<<15, (1<<16) - 1, 10)
rng.integers(1<<15, (1<<16) - 1, 12)
rng.integers(1<<15, (1<<16) - 1, 1)
rng.integers(1<<15, (1<<16) - 1, 24)
rng.integers(1<<15, (1<<16) - 1, 1)
rng.integers(1<<15, (1<<16) - 1, 18)
list(rng.integers(1<<15, (1<<16) - 1, 20))
rng.integers(1<<15, (1<<16) - 1, 2)
(list(rng.integers(1<<15, (1<<16) - 1, 2)))
(list(rng.integers(1<<15, (1<<16) - 1, 10)))
print(list(rng.integers(1<<15, (1<<16) - 1, 10)))

