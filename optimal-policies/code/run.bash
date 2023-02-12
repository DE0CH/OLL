#!/bin/bash

JAR_NAME=code.jar
SCALA_OPTIONS="-J-Xmx1G"
SINGLE_CACHE_SIZE=500000000

OPTIMAL_STRATEGY_PATTERN="optimal-strategy-%d.csv"

function compile() {
    scalac -d "$JAR_NAME" -sourcepath . util/*.scala oll/*.scala oll/xover/*.scala
}

function maybe_compile() {
    if [[ ! -f "$JAR_NAME" ]]; then
        compile
    fi
}

function dynamic() {
    scala -cp "$JAR_NAME" $SCALA_OPTIONS oll.BestDynamicDoubleLambdaCheating $1 \
        --crossover-math=0check \
        --max-cache-byte-size=$SINGLE_CACHE_SIZE \
        --never-mutate-zero-bits=true --include-best-mutant=true --ignore-crossover-parent-duplicates=true \
        --print-summary=true --output=`printf "$OPTIMAL_STRATEGY_PATTERN" "$1"`
}

function landscape() {
    scala -cp "$JAR_NAME" $SCALA_OPTIONS oll.LandscapeAnalysis \
        --crossover-math=0check \
        --max-cache-byte-size=$SINGLE_CACHE_SIZE \
        --never-mutate-zero-bits=true --include-best-mutant=true --ignore-crossover-parent-duplicates=true
}

function binned() {
    FILENAME=`printf "$OPTIMAL_STRATEGY_PATTERN" "$1"`
    if [[ ! -f "$FILENAME" ]]; then
        echo "Cannot find the optimal dynamic policy in file '$FILENAME'!"
        echo "Please, compute it first"
        exit 1
    else
        scala -cp "$JAR_NAME" $SCALA_OPTIONS oll.BestBinnedDoubleLambda \
            --crossover-math=0check \
            --max-cache-byte-size=$SINGLE_CACHE_SIZE \
            --initial-sigma=0.1 --input="$FILENAME"
    fi
}

if [[ "$1" == "compile" ]]; then
    compile
elif [[ "$1" == "clean" ]]; then
    rm "$JAR_NAME"
elif [[ "$1" == "dynamic" ]]; then
    maybe_compile
    dynamic "$2"
elif [[ "$1" == "landscape" ]]; then
    maybe_compile
    landscape
elif [[ "$1" == "binned" ]]; then
    maybe_compile
    binned "$2"
else
    echo "Usage:"
    echo "    $0 compile: forces compilation of the sources"
    echo "    $0 clean: removes the compiled jar file"
    echo "    $0 dynamic <size>: computes the optimal dynamic policy for problem size <size>"
    echo "        Note: for size=100 and default memory options the computation runs in 15 seconds"
    echo "        on a 4-core CPU clocked at 3.4 GHz, except for compilation time."
    echo "    $0 landscape: runs the landscape analysis experiments"
    echo "        Node: the problem size is currently hardcoded to 500 and so are bin sizes."
    echo "        This runs under 4 minutes on a 4-core CPU clocked at 3.4 GHz."
    echo "    $0 binned <size>: computes the optimal binning policy for problem size <size>"
    echo "        Note: the optimal dynamic policy for that size should be computed."
    echo "        For size=100 and default memory options it runs in roughly 30 seconds"
    echo "        on a 4-core CPU clocked at 3.4 GHz, except for compilation time."
fi
