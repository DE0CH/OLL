use std::{
    cmp::{max_by, min_by, Ordering},
    iter::{repeat, repeat_with},
    ops::{Add, AddAssign},
};

use bitvec::prelude::*;
use pyo3::prelude::*;
use rand::prelude::IteratorRandom;
use rand::seq::SliceRandom;
use rand::SeedableRng;
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
        self.0 = 9999999999;
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

struct OneMax(BitVec);

impl OneMax {
    fn len(&self) -> usize{
        self.0.len()
    }
    
    fn flip(&self, mask: Self) -> Self {
        Self(mask.0 ^ &self.0)
    }
    
    fn invert(mut self) -> Self {
        let mut ones = bitvec![usize, Lsb0;];
        ones.extend(repeat(true).take(self.len()));
        self.0 ^= ones;
        self
    }
    
    fn compare_one(&self, other: &Self) -> Ordering {
        self.0.count_ones().cmp(&other.0.count_ones())
    }
    
    fn crossover(left: &Self, right: &Self, mask: Self, n_evals: &mut NEvals) -> Self {
        let inverted_mask = mask.clone().invert();
        let left_half = left.flip(inverted_mask);
        let right_half = right.flip(mask);
        let res = Self(left_half.0 | right_half.0);
        if !(&res == left || &res == right) {
            n_evals.increament()
        }
        res
    }
    
    fn fitness(&self) -> usize {
        self.0.len()
    }
    
    // Checked
    fn random_bits_with_ones<R: rand::Rng>(length: usize, amount: usize, rng: &mut R) -> Self {
        let bits_indices = (0..length).choose_multiple(rng, amount);
        let mut res = bitvec![usize, Lsb0;];
        res.extend(repeat(false).take(length));
        bits_indices.iter().for_each(|i| res.set(*i, true));
        Self(res)
    }
    
    // Checked
    fn random_ones_with_p<R: rand::Rng>(length: usize, p: f64, rng: &mut R) -> Self {
        let mut res = bitvec![usize, Lsb0;];
        res.extend(repeat_with(|| rng.gen_bool(p)).take(length));
        Self(res)
    }
    
    fn random_bits<R: rand::Rng>(rng: &mut R, length: usize) -> Self {
        Self::random_ones_with_p(length, 0.5, rng)
    } 
}

impl Clone for OneMax {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}

impl PartialEq for OneMax {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq(&other.0)
    }

    fn ne(&self, other: &Self) -> bool {
        self.0.ne(&other.0)
    }
}

impl Eq for OneMax {
    
}

struct BinomialNoZero(Binomial);

impl BinomialNoZero {
    fn new(p: f64, n: usize) -> statrs::Result<Self> {
        let inner = Binomial::new(p, n.try_into().unwrap())?;
        Ok(Self(inner))
    } 
    
    fn pmf(&self, i: usize) -> f64 {
        let n = self.0.n().try_into().unwrap();
        let p = self.0.p();
        if i == 0 {
            0.0
        } else {
            self.0.pmf(i.try_into().unwrap()) / (1.0 - (1.0 - p).powi(n))
        }
    }
}

fn mutate<R: rand::Rng>(parent: &OneMax, p: f64, n_child: usize, rng: &mut R) -> (OneMax, NEvals) {
    let bi = BinomialNoZero::new(p, parent.len()).unwrap();
    let l = *(0..=parent.len())
    .collect::<Vec<usize>>()
    .choose_weighted(rng, |i| {
        bi.pmf(*i)
    })
    .unwrap();
    let children = repeat_with(|| {
        let mask = OneMax::random_bits_with_ones(parent.len(), l, rng);
        parent.flip(mask)
    })
    .take(n_child);
    
    let x_prime = children
    .max_by(|x, y| x.compare_one(y))
    .unwrap();
    
    (x_prime, NEvals(n_child))
}

fn crossover<R: rand::Rng>(
    parent: &OneMax,
    x_prime: OneMax,
    p: f64,
    n_child: usize,
    rng: &mut R,
) -> (OneMax, NEvals) {
    let mut n_evals = NEvals::new();
    let children = repeat_with(|| {
        let mask = OneMax::random_ones_with_p(parent.len(), p, rng);
        OneMax::crossover(parent, &x_prime, mask, &mut n_evals)
    })
    .take(n_child);
    let y = children
    .max_by(|x, y| x.compare_one(y))
    .unwrap();
    let y = [y, x_prime]
    .into_iter()
    .max_by(|x, y| x.compare_one(y))
    .unwrap();
    (y, n_evals)
}

fn generation_full<R: rand::Rng>(
    x: OneMax,
    p: f64,
    n_child_mutate: usize,
    c: f64,
    n_child_crossover: usize,
    rng: &mut R,
) -> (OneMax, NEvals) {
    let (x_prime, ne1) = mutate(&x, p, n_child_mutate, rng);
    let (y, ne2) = crossover(&x, x_prime, c, n_child_crossover, rng);
    let n_evals = ne1 + ne2;
    let x = [x, y]
    .into_iter()
    .max_by(|x, y| x.compare_one(y))
    .unwrap();
    (x, n_evals)
}

fn generation_with_lambda<R: rand::Rng>(x: OneMax, lbd: f64, rng: &mut R) -> (OneMax, NEvals) {
    let p = lbd / (x.len() as f64);
    let c = 1.0 / (lbd as f64);
    let n_child: usize = (lbd.round() as i64).try_into().unwrap();
    generation_full(x, p, n_child, c, n_child, rng)
}

fn get_rng(seed: u64) -> rand_mt::Mt64 {
    let rng: rand_mt::Mt64 = SeedableRng::seed_from_u64(seed);
    rng
}

#[pyfunction]
fn onell_lambda(n: usize, lbds: Vec<f64>, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng = get_rng(seed);
    let mut x = OneMax::random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    while x.fitness() != n && n_evals < max_evals {
        let lbd = lbds[x.fitness()];
        let ne;
        (x, ne) = generation_with_lambda(x, lbd, &mut rng);
        n_evals += ne;
    }
    
    if x.fitness() != n {
        n_evals.make_big()
    }
    Ok(n_evals.0)
}

#[pyfunction]
fn onell_dynamic_theory(n: usize, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng = get_rng(seed);
    let mut x = OneMax::random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    while x.fitness() != n && n_evals < max_evals {
        let lbd = (n as f64 / (n - x.fitness()) as f64).sqrt();
        let ne;
        (x, ne) = generation_with_lambda(x, lbd, &mut rng);
        n_evals += ne;
    }
    
    if x.fitness() != n {
        n_evals.make_big()
    }
    Ok(n_evals.0)
}

#[pyfunction]
fn onell_five_parameters(n: usize, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng = get_rng(seed);
    let mut x = OneMax::random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    let alpha = 0.45;
    let beta = 1.6;
    let gamma = 1.0;
    let a = 1.16;
    let b = 0.7;
    let mut lbd: f64 = 1.0;
    let min_prob = 1.0 / (n as f64);
    let max_prob = 0.99;
    while x.fitness() != n && n_evals < max_evals {
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
        let f_x = x.fitness();
        let ne;
        (x, ne) = generation_full(x, p, n_child_mutate, c, n_child_crossover, &mut rng);
        if f_x < x.fitness() {
            lbd = max_by(b * lbd, 1.0, |x, y| x.partial_cmp(y).unwrap());
        } else {
            lbd = min_by(a * lbd, (n - 1) as f64, |x, y| x.partial_cmp(y).unwrap());
        }
        n_evals += ne;
    }
    
    if x.fitness() != n {
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
