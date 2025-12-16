# Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# Analyze property files 
clear -all 

# Initialize coverage for both stimuli models and COI 
# check_cov -init -model all -type all -exclude_module ${TOP_MODULE}
check_cov -init -model all -type all

analyze -clear 
analyze -sv ${SV_PATH}
analyze -sva ${SVA_PATH}

# Elaborate design and properties 
# elaborate -top ${TOP_MODULE}
elaborate

# Define clock and reset signals and run proof

clock ${CLOCK}
reset ${RESET}

# Get design information to check general complexity
get_design_info

# Run proof on all assertions with a time limit 
prove -all -time_limit 1m

# Get proof results
set proofs_status [get_status [get_property_list -include {type {assert} disabled {0}}]]

# Output the proof results
puts "proofs: $proofs_status"

# Check if any properties failed (have status 'cex' or 'falsified')
set failed_props [get_property_list -include {type {assert} status {cex falsified}}]

if {[llength $failed_props] > 0} {
    puts "WARNING: Some properties failed with counterexample:"
    foreach prop $failed_props {
        puts "  - $prop"
    }
    puts "Continuing with coverage calculation despite property failures..."
}

# Measure coverage for both stimuli models and COI regardless of property failures
check_cov -measure -type all -verbose

# Coverage reporting script 
set coverage_models {functional statement toggle expression branch}
set coverage_types {stimuli coi}

puts "\nCOVERAGE REPORT"
puts "TYPE|MODEL|COVERAGE"
puts "--------------------"

foreach type $coverage_types {
    foreach model $coverage_models {
        if {$type == "coi"} {
            set coverage_data [check_cov -report -model $model -type checker -checker_mode coi]
        } else {
            set coverage_data [check_cov -report -model $model -type $type]
        }
        if {[regexp {([0-9.]+)%} $coverage_data match coverage]} {
            puts "$type|$model|$coverage"
        } else {
            puts "$type|$model|N/A"
        }
    }
}

puts "### COVERAGE_REPORT_START ###"    
set undetectable_coverage [check_cov -list -status undetectable -checker_mode coi]
puts "### UNDETECTABLE_START ###"
puts $undetectable_coverage
puts "### UNDETECTABLE_END ###"

set unprocessed_coverage [check_cov -list -status unprocessed -checker_mode coi]
puts "### UNPROCESSED_START ###"
puts $unprocessed_coverage
puts "### UNPROCESSED_END ###"

puts "### COVERAGE_REPORT_END ###"
