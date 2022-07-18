
use std::{iter::{repeat_with, repeat}, ops::{Add, AddAssign}};

use pyo3::prelude::*;
use bitvec::prelude::*;
use rand::prelude::IteratorRandom;
use statrs::distribution::{Binomial, Discrete};
use rand::seq::SliceRandom;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())

}
#[derive(PartialEq, Eq, PartialOrd, Ord)]
#[pyclass]
struct NEvals(usize);

impl NEvals {
    fn new() -> NEvals {
        NEvals(0)
    }
    fn increament(&mut self) {
       self.0 += 1; 
    }
    fn make_big(&mut self) {
        self.0 *= 2;
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
    let l = *(0..parent.len()).collect::<Vec<usize>>().choose_weighted(rng, |i| {
        if *i == 0{
            0f64
        } else {
            bi.pmf((*i).try_into().unwrap()) / (1f64 - ((1f64 - p) as f64).powi(parent.len().try_into().unwrap()))
        }
    }).unwrap();
    let children = repeat_with(|| {
        let mut child = random_bits_with_ones(parent.len(), l, rng);
        child ^= parent;
        child
    }).take(n_child);

    let x_prime = children.max_by(|x, y| x.count_ones().cmp(&y.count_ones())).unwrap();

    (x_prime, NEvals(n_child))
}

fn crossover<R: rand::Rng>(parent: &BitVec, x_prime: &BitVec, p: f64, n_child: usize, rng: &mut R) -> (BitVec, NEvals){
    let mut n_evals = NEvals::new();
    let children = repeat_with(|| {
        let mut child = bitvec![usize, Lsb0;];
        child.extend(repeat(false).take(parent.len()));
        let mask = random_ones_with_p(parent.len(), p, rng);
        let parent_half = !mask.clone() & parent;
        let x_prime_half = mask & x_prime;
        child = parent_half | x_prime_half;
        if child.as_bitslice() != parent && child.as_bitslice() != x_prime {
            n_evals.increament();
        }
        child
    }).take(n_child);
    let y = children.max_by(|x, y| x.count_ones().cmp(&y.count_ones())).unwrap();
    let y = [y, x_prime.clone()].into_iter().max_by(|x, y| x.count_ones().cmp(&y.count_ones())).unwrap();
    (y, n_evals)
}

fn generation<R: rand::Rng>(x: &BitVec, lbd: f64, rng: &mut R) -> (BitVec, NEvals) {
    let p: f64 = lbd / (x.len() as f64);
    let (x_prime, ne1) = mutate(x, p, (lbd.round() as i64).try_into().unwrap(), rng);
    let (y, ne2) = crossover(x, &x_prime, p, (lbd.round() as i64).try_into().unwrap(), rng);        
    let n_evals = ne1 + ne2;
    let x = [x, &y].into_iter().max_by(|x, y| x.cmp(y)).unwrap(); 
    (x.clone(), n_evals)
}

#[pyfunction]
fn onell_lambda(n: usize, lbds: Vec<f64>, seed: u64, max_evals: usize) -> PyResult<usize> {
    let max_evals = NEvals(max_evals);
    let mut rng = fastrand::Rng::with_seed(seed);
    let mut x = random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    while x.count_ones() != n && n_evals < max_evals{
        let lbd = lbds[x.count_ones()];
        let ne;
        (x, ne) = generation(&x, lbd, &mut rng);
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
    let mut rng = fastrand::Rng::with_seed(seed);
    let mut x = random_bits(&mut rng, n);
    let mut n_evals = NEvals::new();
    while x.count_ones() != n && n_evals < max_evals {
        let lbd = (n as f64 / (n - x.count_ones()) as f64).sqrt();
        let ne;
        (x, ne) = generation(&x, lbd, &mut rng);
        n_evals += ne;
    }

    if x.count_ones() != n {
        n_evals.make_big()
    }
    Ok(n_evals.0)
}

/// A Python module implemented in Rust.
#[pymodule]
fn onell_algs_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(onell_lambda, m)?)?;
    m.add_function(wrap_pyfunction!(onell_dynamic_theory, m)?)?;
    m.add_class::<NEvals>()?;
    Ok(())
}