#!/bin/bash

# Basic binary compatibility test script for replace_landsurface.
# See INTEGRATION_README.md for details on test usage, data and options.

TEST_DATA_DIR=/g/data/vk83/testing/data/replace_landsurface/integration_tests
INPUT_DIR=$TEST_DATA_DIR/input_data
OUTPUT_DIR=$TEST_DATA_DIR/expected_outputs
DRIVING_DATA_DIR=$TEST_DATA_DIR/driving_data
CLEAN_OUTPUT=true

declare -A pids # Associative array (similar to a dictionary in Python)

# Create a temporary work directory
WORK_DIR=$(mktemp -d)
echo -e "Work directory: $WORK_DIR\n"
# Trap signals to clean up WORK directory depending on exit status
functrap() {
    exit_code="$?"
    if [ "$exit_code" -eq 0 ] && $CLEAN_OUTPUT; then # Job completed successfully and CLEAN_OUTPUT is true
        rm -rf "$WORK_DIR"
        echo "Work directory cleaned up."
    elif [ "$exit_code" -eq 2 ]; then # Job was terminated preventively (did not fail)
        kill -9 $(jobs -p) &> /dev/null # Kill all background jobs
        rm -rf "$WORK_DIR"
        echo "Script was terminated preventively."
        echo "Work directory cleaned up. Background jobs killed."
    fi
}
# Separate the cases when the script is interrupted, from the cases when it's not
trap "exit 2" SIGHUP SIGINT SIGQUIT SIGILL SIGABRT SIGTERM SIGSTOP
trap functrap EXIT

#Set up the work directory as a copy of the test data directory
echo "Setting up work directory..."
cp -r $INPUT_DIR/* $WORK_DIR
cd $WORK_DIR


function usage {
    cat << EOF
Basic binary compatibility test script for 'replace_landsurface'.
Checks that the outputs of the 'replace_landsurface' package entry points correspond to the expected outputs.

Usage: regression_tests.sh [-k/--keep]

Options:
-k, --keep            Keep output data upon test completion. 
                      If absent, output data will only be kept for failed tests.
EOF
}

while getopts ":-:hk" opt; do
    case ${opt} in
        -)
            case ${OPTARG} in
                help)
                    usage
                    exit 0
                ;;
                keep)
                    CLEAN_OUTPUT=false
                ;;
                *)
                    echo "Invalid option: \"--${OPTARG}\"." >&2
                    usage
                    exit 1
                ;;
            esac
        ;;
        h)
            usage
            exit 0
        ;;
        k)
            CLEAN_OUTPUT=true
        ;;
        \?)
            echo "Invalid option: \"-${OPTARG}\"." >&2
            usage
            exit 1
        ;;
    esac
done

# Check that no additional arguments were passed.
if [[ -n "${@:$OPTIND:1}" ]]; then
    echo "Invalid positional argument: \"${@:$OPTIND:1}\"." >&2
    exit 1
fi

# # -----------------------------------------------------------------
# # Run the tests
# # -----------------------------------------------------------------
echo "Running tests..."

export ROSE_DATA=$DRIVING_DATA_DIR
run_command() {
    MASK=$WORK_DIR/$test_dir/mask
    FILE=$WORK_DIR/$test_dir/file
    HRES_IC=$WORK_DIR/$test_dir/hres_ic
    eval "$entry_point --file ${FILE}.tmp --start $START --hres_ic $HRES_IC --type $TYPE"
}
compare() {
    test_num=${test_dir#test_}
    cmp $WORK_DIR/$test_dir/file $OUTPUT_DIR/output_${test_num}
    if [ $? -ne 0 ]; then
        echo "Test $test_num failed."
        exit 1
    fi
}
run_test() {
    run_command
    compare
}
# # -----------------------------------------------------------------
# Test hres_ic
entry_point=hres_ic

# Test 1: 'era5land'
# MASK=/scratch/tm70/cbe563/cylc-run/u-dg767/share/data/ancils/Lismore/d1000/qrparm.mask
# FILE=/g/data/tm70/cbe563/test_replace_land_surface/ERA5LAND/GAL9_astart
# HRES_IC=NOT_SET
test_dir=test_1
TYPE=era5land
START=202202260000

echo "### Test 1: hres_ic, type 'era5land' ###"
run_test > /dev/null & pids[1]+=$!

# # Test 2: 'barra'
# MASK=/scratch/tm70/cbe563/cylc-run/u-dg767.b/share/data/ancils/Lismore/d1100/qrparm.mask
# FILE=/g/data/tm70/cbe563/test_replace_land_surface/BARRAR2/GAL9_astart
# HRES_IC=NOT_SET
test_dir=test_2
TYPE=barra
START=202008090000

echo "### Test 2: hres_ic, type 'barra' ###"
run_test > /dev/null & pids[2]+=$!

# # Test 3: 'astart'
# MASK=/scratch/tm70/cbe563/cylc-run/u-dg767/share/data/ancils/Lismore/d0198/qrparm.mask
# FILE=/g/data/tm70/cbe563/test_replace_land_surface/ASTART/RAL3P2_astart
# HRES_IC=/scratch/tm70/cbe563/cylc-run/u-dg768.worked/share/cycle/20220226T0000Z/Lismore/d0198/RAL3P2/ics/RAL3P2_astart
test_dir=test_3
TYPE=astart
START=202112310000

echo "### Test 3: hres_ic, type 'astart' ###"
run_test > /dev/null & pids[3]+=$!

# Capture the exit status of each background processes dynamically
declare -A exit_statuses # Associative array (similar to a dictionary in Python)
for pid in "${pids[@]}"; do
    # Find which test the pid corresponds to
    for key in "${!pids[@]}"; do
        if [[ ${pids[$key]} == $pid ]]; then
            test_num=$key
            break
        fi
    done
    wait $pid  # Waits for the next job in the list to finish (not necessarily in order because it's used within a loop)
    exit_status=$?
    exit_statuses[$test_num]=$exit_status
done

# Exit with a status 1 if any of the tests failed
exit_value=0
for ind in ${!exit_statuses[@]}; do
    if [ ${exit_statuses[$ind]} -ne 0 ]; then
        echo "Test $ind failed."
        exit_value=1
    fi
done

if [ $exit_value -eq 0 ]; then
    echo "All tests passed."
else
    exit 1
fi