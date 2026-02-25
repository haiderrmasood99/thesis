#!/bin/sh

# Bash script to run Cycles batch simulations with re-initialization of model
# variables from a baseline run

# Name of baseline simulation
BASELINE=test

# Day of year for re-initialization
DOY=1

# Name of multi-simulation file
MULTI_FILE=test.txt

# Read baseline model parameters
BASE_START_YEAR=$(grep "SIMULATION_START_YEAR" ./input/$BASELINE.ctrl |awk '{print $2}')
BASE_END_YEAR=$(grep "SIMULATION_END_YEAR" ./input/$BASELINE.ctrl |awk '{print $2}')
BASE_SOIL_FILE=$(grep "SOIL_FILE" ./input/$BASELINE.ctrl |awk '{print $2}')
BASE_SOIL_LAYER=$(grep "TOTAL_LAYERS" ./input/$BASE_SOIL_FILE |awk '{print $2}')

echo "Check multi-simulation file configuration..."
{
    read
    while IFS=" "  read -r SIM_CODE ROTYR START_YEAR END_YEAR REINIT CROPF OPERF SOILF WEATHERF REINITF INFIL
    do
        # Check if start year and end year are the same as the baseline simulation
        if [ $START_YEAR -ne $BASE_START_YEAR ] || [ $END_YEAR -ne $BASE_END_YEAR ]; then
            echo "Error: Start year and end year should be the same as the baseline for all simulations in $MULTI_FILE"
            exit 1
        fi

        # Check if number of soil layers are the same as the baseline simulation
        SOIL_LAYER=$(grep "TOTAL_LAYERS" ./input/$SOILF |awk '{print $2}')
        if [ $SOIL_LAYER -ne $BASE_SOIL_LAYER ]; then
            echo "Error: Number of soil layers in the soil file should be the same as the baseline for all simulations in $MULTI_FILE"
            exit 1
        fi

        # Check if re-initialization is enabled
        if [ $REINIT -ne 1 ]; then
            echo "Error: Re-initialization should be activated for all simulations in $MULTI_FILE"
            exit 1
        fi

        # Check if re-initialization file is correctly specified
        if [ "$REINITF" != "$BASELINE.reinit" ]; then
            echo "Error: Re-initialization file should be $BASELINE.reinit for all simulations in $MULTI_FILE"
            exit 1
        fi
        echo "$START_YEAR $END_YEAR $REINIT $REINITF"
    done
} < input/$MULTI_FILE

# Run baseline simulation in baseline model with spinup
echo "Run baseline simulation in spin-up mode and generate re-initialization file"
./Cycles -s -l $DOY $BASELINE

# Copy generated re-initialization file into input directory
mv output/$BASELINE/reinit.dat input/$BASELINE.reinit

# Run batch simulation with re-initialization
echo "Run batch simulations using re-initialization"
./Cycles -m $MULTI_FILE
