package util

import java.{util => ju}

object MathEx {
  private[this] var logCache: Array[Double] = new Array(2)
  private[this] var logFactorialCache: Array[Double] = new Array(2)
  private[this] def ensureFactorialExists(n: Int): Unit = {
    if (logFactorialCache.length <= n) {
      assert(n < Int.MaxValue)
      synchronized {
        if (logFactorialCache.length <= n) {
          val newLength = if (n < (1 << 30)) nextPowerOfTwo(n + 1) else Int.MaxValue
          val newLogArray, newFactArray = new Array[Double](newLength)
          System.arraycopy(logCache, 0, newLogArray, 0, logFactorialCache.length)
          System.arraycopy(logFactorialCache, 0, newFactArray, 0, logFactorialCache.length)
          var i = logFactorialCache.length
          while (i < newFactArray.length && i >= 0) {
            newLogArray(i) = math.log(i)
            newFactArray(i) = newFactArray(i - 1) + newLogArray(i)
            i += 1
          }
          logCache = newLogArray
          logFactorialCache = newFactArray
        }
      }
    }
  }

  def log(n: Int): Double = {
    ensureFactorialExists(n)
    logCache(n)
  }

  def logFactorial(n: Int): Double = {
    ensureFactorialExists(n)
    logFactorialCache(n)
  }

  def logChoose(n: Int, k: Int): Double = {
    ensureFactorialExists(n)
    logFactorialCache(n) - logFactorialCache(n - k) - logFactorialCache(k)
  }

  def nextPowerOfTwo(n: Int): Int = {
    require(n <= (1 << 30))
    1 << (32 - Integer.numberOfLeadingZeros(n - 1))
  }

  def expectedRuntimeOnBitStrings(n: Int, runtimeForFitnessOrDistance: Int => Double): Double = {
    var x = 0
    var theTotalRuntime = 0.0
    while (x <= n) {
      theTotalRuntime += runtimeForFitnessOrDistance(x) * math.exp(MathEx.logChoose(n, x) - math.log(2) * n)
      x += 1
    }
    theTotalRuntime
  }

  def multiply(array: Array[Double], value: Double): Unit = {
    var i = 0
    while (i < array.length) {
      array(i) *= value
      i += 1
    }
  }
}
