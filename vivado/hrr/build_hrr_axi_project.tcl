# =============================================================================
# build_hrr_axi_project.tcl
#
# Automates the remaining Vivado steps from the README's "Remaining" list:
#   - Zynq PS7 + AXI wrapper
#   - Final AXI register map (already fixed by hrr_axi.v's address decode)
#   - Bitstream + hardware handoff for the PYNQ-Z2
#
# Usage:
#   1. Put hrr.v, hrr_axi.v and this script in the same directory.
#   2. From that directory:  vivado -mode batch -source build_hrr_axi_project.tcl
#   3. Program the board, or hand write_hw.xsa to the PYNQ side for the
#      overlay (.bit + .hwh) the pynq_hrr_driver.py script expects.
#
# Adjust the variables in the "USER SETTINGS" block if your board files /
# part differ from a stock PYNQ-Z2 install.
# =============================================================================

# --------------------------- USER SETTINGS ----------------------------------
set origin_dir      [file normalize [file dirname [info script]]]
set proj_name        hrr_pynq
set proj_dir        "$origin_dir/${proj_name}_proj"
set ip_repo_dir     "$origin_dir/ip_repo/hrr_axi_1_0"
set fpga_part        xc7z020clg400-1

# Board-part version strings shift between Vivado releases (e.g. ...1.0 vs
# ...1.1), so look up whatever is actually installed rather than assuming.
set board_matches [get_board_parts -filter {NAME =~ "*pynq*z2*"}]
if {[llength $board_matches] == 0} {
    puts "ERROR: no PYNQ-Z2 board_part is installed."
    puts "Run install_pynq_board_files.tcl first, then re-run this script."
    exit 1
}
set board_part [lindex $board_matches 0]
puts "Using board_part: $board_part"

set hrr_sources     [list "$origin_dir/hrr.v" "$origin_dir/hrr_axi.v"]
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1. Package hrr.v + hrr_axi.v as a reusable AXI4-Lite IP.
#    Done inside a throwaway project so it doesn't collide with the real one.
# -----------------------------------------------------------------------------
file mkdir [file dirname $ip_repo_dir]
set pkg_proj_dir "$origin_dir/_ip_pkg_tmp"
file delete -force $pkg_proj_dir
create_project ip_pkg_tmp $pkg_proj_dir -part $fpga_part -force

add_files -norecurse $hrr_sources
update_compile_order -fileset sources_1
set_property top hrr_axi [current_fileset]

ipx::package_project -root_dir $ip_repo_dir -vendor user.org -library hrr \
    -taxonomy /UserIP -import_files -set_current false

# ipx::package_project already writes component.xml etc. to $ip_repo_dir;
# nothing further to save here.
close_project
file delete -force $pkg_proj_dir

# -----------------------------------------------------------------------------
# 2. Create the real project and point it at the IP repository above.
# -----------------------------------------------------------------------------
file delete -force $proj_dir
create_project $proj_name $proj_dir -part $fpga_part -force
set_property board_part $board_part [current_project]
set_property ip_repo_paths [file dirname $ip_repo_dir] [current_project]
update_ip_catalog -rebuild

# -----------------------------------------------------------------------------
# 3. Block design: ZYNQ7 PS + AXI interconnect (auto) + hrr_axi.
# -----------------------------------------------------------------------------
create_bd_design "hrr_bd"

set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0]
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset "1" \
              Master "Disable" Slave "Disable"} $ps

# Only the general-purpose AXI master to PL is needed for a single AXI-Lite
# peripheral; enable it explicitly in case the board preset left it off.
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1}] $ps

# hrr.v's Montgomery-reduction combinational path (mont_product/mont_red0)
# doesn't close timing at the PS7 default of 100 MHz (measured WNS ~ -2.1ns).
# 50 MHz doubles the period and clears that with margin, with no RTL changes.
set_property -dict [list CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {50}] $ps

set hrr [create_bd_cell -type ip -vlnv user.org:hrr:hrr_axi:1.0 hrr_axi_0]

# Wires up M_AXI_GP0 -> (auto-inserted AXI interconnect) -> hrr_axi_0,
# plus the FCLK_CLK0 / peripheral-reset connections.
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config { Master "/processing_system7_0/M_AXI_GP0" \
              Clk "Auto" } [get_bd_intf_pins hrr_axi_0/S_AXI]

validate_bd_design
save_bd_design

# -----------------------------------------------------------------------------
# 4. Wrapper, synthesis, implementation, bitstream, hardware export.
# -----------------------------------------------------------------------------
make_wrapper -files [get_files "$proj_dir/${proj_name}.srcs/sources_1/bd/hrr_bd/hrr_bd.bd"] -top
add_files -norecurse "$proj_dir/${proj_name}.gen/sources_1/bd/hrr_bd/hdl/hrr_bd_wrapper.v"
update_compile_order -fileset sources_1
set_property top hrr_bd_wrapper [current_fileset]

launch_runs synth_1 -jobs 4
wait_on_run synth_1

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# Address map: confirm hrr_axi_0 landed somewhere sane before you rely on it
# in pynq_hrr_driver.py. Prints e.g. "hrr_axi_0 : 0x43C00000".
puts "---- AXI address map ----"
foreach seg [get_bd_addr_segs -of_objects [get_bd_addr_spaces]] {
    if {[string match "*hrr_axi_0*" $seg]} {
        puts "$seg -> [get_property OFFSET $seg] (range [get_property RANGE $seg])"
    }
}

# Hardware handoff for the PYNQ side (gives you the .bit + .hwh once
# repackaged, or hand this .xsa straight to Vitis / pynq's Overlay()).
write_hw_platform -fixed -include_bit -force \
    -file "$proj_dir/${proj_name}_wrapper.xsa"

puts "Done. Bitstream + XSA are under: $proj_dir"
