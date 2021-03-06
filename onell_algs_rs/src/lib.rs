use std::{
    cmp::{max_by, min_by},
    iter::{repeat, repeat_with},
    ops::{Add, AddAssign},
};

use bitvec::prelude::*;
use pyo3::prelude::*;
use rand::prelude::IteratorRandom;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_mt::Mt64;
use statrs::distribution::{Binomial, Discrete};

#[derive(PartialEq, Eq, PartialOrd, Ord)]
struct NEvals(usize);

impl NEvals {
    fn new() -> NEvals {
        NEvals(0)
    }
    fn increament(&mut self) {
        self.0 += 1;
    }
    fn make_big(&mut self) {
        self.0 *= usize::max_value()
    }
}

impl Add for NEvals {
    type Output = Self;
    fn add(self, other: Self) -> Self {
        Self(self.0 + other.0)
    }
}

impl AddAssign for NEvals {
    fn add_assign(&mut self, rhs: Self) {
        self.0 += rhs.0;
    }
}

fn random_bits<R: rand::Rng>(rng: &mut R, length: usize) -> BitVec {
    let arch_len = std::mem::size_of::<usize>() * 8;
    let word_length = (length - 1) / arch_len + 1;
    let numbers = std::iter::repeat_with(|| rng.gen::<usize>()).take(word_length);
    let mut bv = bitvec![usize, Lsb0;];
    bv.extend(numbers);
    bv.truncate(length);
    bv
}

fn random_bits_with_ones<R: rand::Rng>(length: usize, amount: usize, rng: &mut R) -> BitVec {
    let bits_indices = (0..length).choose_multiple(rng, amount);
    let mut res = bitvec![usize, Lsb0;];
    res.extend(repeat(false).take(length));
    bits_indices.iter().for_each(|i| res.set(*i, true));
    res
}

fn random_ones_with_p<R: rand::Rng>(length: usize, p: f64, rng: &mut R) -> BitVec {
    let mut res = bitvec![usize, Lsb0;];
    res.extend(repeat_with(|| rng.gen_bool(p)).take(length));
    res
}

fn mutate<R: rand::Rng>(parent: &BitVec, p: f64, n_child: usize, rng: &mut R) -> (BitVec, NEvals) {
    let bi = Binomial::new(p, parent.len().try_into().unwrap()).unwrap();
    let l = *(0..=parent.len())
        .collect::<Vec<usize>>()
        .choose_weighted(rng, |i| {
            if *i == 0 {
                0f64
            } else {
                bi.pmf((*i).try_into().unwrap())
                    / (1f64 - ((1f64 - p) as f64).powi(parent.len().try_into().unwrap()))
            }
        })
        .unwrap();
    let children = repeat_with(|| {
        let mut child = random_bits_with_ones(parent.len(), l, rng);
        child ^= parent;
        child
    })
    .take(n_child);

    let x_prime = children
        .max_by(|x, y| x.count_ones().cmp(&y.count_ones()))
        .unwrap();

    (x_prime, NEvals(n_child))
}

fn crossover<R: rand::Rng>(
    parent: &BitVec,
    x_prime: BitVec,
    p: f64,
    n_child: usize,
    rng: &mut R,
) -> (BitVec, NEvals) {
    let mut n_evals = NEvals::new();
    let children = repeat_with(|| {
        let mut child = bitvec![usize, Lsb0;];
        child.extend(repeat(false).take(parent.len()));
        let mask = random_ones_with_p(parent.len(), p, rng);
        let parent_half = !mask.clone() & parent;
        let x_prime_half = mask & &x_prime;
        child = parent_half | x_prime_half;
        if child.as_bitslice() != parent && child.as_bitslice() != x_prime {
            n_evals.increament();
        }
        child
    })
    .take(n_child);
    let y = children
        .max_by(|x, y| x.count_ones().cmp(&y.count_ones()))
        .unwrap();
    let y = [y, x_prime]
        .into_iter()
        .max_by(|x, y| x.count_ones().cmp(&y.count_ones()))
        .unwrap();
    (y, n_evals)
}

fn generation_full<R: rand::Rng>(
    x: BitVec,
    p: f64,
    n_child_mutate: usize,
    c: f64,
    n_child_crossover: usize,
    rng: &mut R,
) -> (BitVec, NEvals) {
    let (x_prime, ne1) = mutate(&x, p, n_child_mutate, rng);
    let (y, ne2) = crossover(&x, x_prime, c, n_child_crossover, rng);
    let n_evals = ne1 + ne2;
    let x = [x, y]
        .into_iter()
        .max_by(|x, y| x.count_ones().cmp(&y.count_ones()))
        .unwrap();
    (x, n_evals)
}

fn generation_with_lambda<R: rand::Rng>(x: BitVec, lbd: f64, rng: &mut R) -> (BitVec, NEvals) {
    let p = lbd / (x.len() as f64);
    let c = 1.0 / (lbd as f64);
    let n_child: usize = (lbd.round() as i64).try_into().unwrap();
    generation_full(x, p, n_child, c, n_child, rng)
}

#[pyfunction]
fn onell_lambda(n: usize, lbds: Vec<f64>, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng: Mt64 = SeedableRng::seed_from_u64(seed);
    let mut x = random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    while x.count_ones() != n && n_evals < max_evals {
        let lbd = lbds[x.count_ones()];
        let ne;
        (x, ne) = generation_with_lambda(x, lbd, &mut rng);
        n_evals += ne;
    }

    if x.count_ones() != n {
        n_evals.make_big()
    }
    Ok(n_evals.0)
}

#[pyfunction]
fn onell_dynamic_theory(n: usize, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng: Mt64 = SeedableRng::seed_from_u64(seed);
    let mut x = random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    while x.count_ones() != n && n_evals < max_evals {
        let lbd = (n as f64 / (n - x.count_ones()) as f64).sqrt();
        let ne;
        (x, ne) = generation_with_lambda(x, lbd, &mut rng);
        n_evals += ne;
    }

    if x.count_ones() != n {
        n_evals.make_big()
    }
    Ok(n_evals.0)
}

#[pyfunction]
fn onell_five_parameters(n: usize, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng: Mt64 = SeedableRng::seed_from_u64(seed);
    let mut x = random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    let alpha = 0.45;
    let beta = 1.6;
    let gamma = 1.0;
    let a = 1.16;
    let b = 0.7;
    let mut lbd: f64 = 1.0;
    let min_prob = 1.0 / (n as f64);
    let max_prob = 0.99;
    while x.count_ones() != n && n_evals < max_evals {
        let p = alpha * lbd / (n as f64);
        let p = {
            if p < min_prob {
                min_prob
            } else if p > max_prob {
                max_prob
            } else {
                p
            }
        };
        let c = gamma / lbd;
        let c = {
            if c < min_prob {
                min_prob
            } else if c > max_prob {
                max_prob
            } else {
                c
            }
        };

        let n_child_mutate = (lbd.round() as i64).try_into().unwrap();
        let n_child_crossover = ((lbd * beta).round() as i64).try_into().unwrap();
        let f_x = x.count_ones();
        let ne;
        (x, ne) = generation_full(x, p, n_child_mutate, c, n_child_crossover, &mut rng);
        if f_x < x.count_ones() {
            lbd = max_by(b * lbd, 1.0, |x, y| x.partial_cmp(y).unwrap());
        } else {
            lbd = min_by(a * lbd, (n - 1) as f64, |x, y| x.partial_cmp(y).unwrap());
        }
        n_evals += ne;
    }

    if x.count_ones() != n {
        n_evals.make_big();
    }

    return Ok(n_evals.0);
}

/// A Python module implemented in Rust.
#[pymodule]
fn onell_algs_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(onell_lambda, m)?)?;
    m.add_function(wrap_pyfunction!(onell_dynamic_theory, m)?)?;
    m.add_function(wrap_pyfunction!(onell_five_parameters, m)?)?;
    Ok(())
}
