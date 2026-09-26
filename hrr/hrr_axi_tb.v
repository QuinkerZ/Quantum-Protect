`timescale 1ns / 1ps

// ============================================================================
// Self-checking AXI4-Lite testbench for hrr_axi.v + hrr.v
//
// Register map:
//   0x00 A       [11:0]
//   0x04 B       [11:0]
//   0x08 CONTROL [0] START
//   0x0C STATUS  [0] DONE, [1] BUSY
//   0x10 RESULT  [11:0]
//
// Icarus Verilog:
//   iverilog -g2012 -o hrr_axi_sim hrr.v hrr_axi.v hrr_axi_tb.v
//   vvp hrr_axi_sim
//
// Tests:
//   1. Reset
//   2. AXI register read/write
//   3. Normal AW+W write
//   4. AW-first write
//   5. W-first write
//   6. START/BUSY/DONE behavior
//   7. RESULT readback
//   8. Boundary cases
//   9. Randomized cases
//  10. Back-to-back operations
// ============================================================================

module hrr_axi_tb;

    localparam integer DATA_WIDTH = 32;
    localparam integer ADDR_WIDTH = 5;
    localparam integer Q = 3329;

    // ------------------------------------------------------------------------
    // Clock and reset
    // ------------------------------------------------------------------------
    reg clk;
    reg resetn;

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;       // 100 MHz
    end

    // ------------------------------------------------------------------------
    // AXI4-Lite signals
    // ------------------------------------------------------------------------
    reg  [ADDR_WIDTH-1:0] awaddr;
    reg                   awvalid;
    wire                  awready;

    reg  [DATA_WIDTH-1:0] wdata;
    reg  [(DATA_WIDTH/8)-1:0] wstrb;
    reg                   wvalid;
    wire                  wready;

    wire [1:0]            bresp;
    wire                  bvalid;
    reg                   bready;

    reg  [ADDR_WIDTH-1:0] araddr;
    reg                   arvalid;
    wire                  arready;

    wire [DATA_WIDTH-1:0] rdata;
    wire [1:0]            rresp;
    wire                  rvalid;
    reg                   rready;

    // ------------------------------------------------------------------------
    // Test counters
    // ------------------------------------------------------------------------
    integer pass_count;
    integer fail_count;
    integer test_count;

    integer i;
    integer rand_a;
    integer rand_b;
    integer actual;

    reg [31:0] rd_tmp;

    // ------------------------------------------------------------------------
    // DUT
    // ------------------------------------------------------------------------
    hrr_axi #(
        .C_S_AXI_DATA_WIDTH(DATA_WIDTH),
        .C_S_AXI_ADDR_WIDTH(ADDR_WIDTH)
    ) dut (
        .S_AXI_ACLK    (clk),
        .S_AXI_ARESETN (resetn),

        .S_AXI_AWADDR  (awaddr),
        .S_AXI_AWVALID (awvalid),
        .S_AXI_AWREADY (awready),

        .S_AXI_WDATA   (wdata),
        .S_AXI_WSTRB   (wstrb),
        .S_AXI_WVALID  (wvalid),
        .S_AXI_WREADY  (wready),

        .S_AXI_BRESP   (bresp),
        .S_AXI_BVALID  (bvalid),
        .S_AXI_BREADY  (bready),

        .S_AXI_ARADDR  (araddr),
        .S_AXI_ARVALID (arvalid),
        .S_AXI_ARREADY (arready),

        .S_AXI_RDATA   (rdata),
        .S_AXI_RRESP   (rresp),
        .S_AXI_RVALID  (rvalid),
        .S_AXI_RREADY  (rready)
    );

    // =========================================================================
    // CHECKING TASKS
    // =========================================================================

    task automatic check_equal;
        input integer got;
        input integer want;
        input [8*80-1:0] name;

        begin
            test_count = test_count + 1;

            if (got === want) begin
                pass_count = pass_count + 1;
                $display("[PASS] %0s : got %0d", name, got);
            end
            else begin
                fail_count = fail_count + 1;
                $display("[FAIL] %0s : got %0d, expected %0d",
                         name, got, want);
            end
        end
    endtask


    task automatic check_equal_hex;
        input [31:0] got;
        input [31:0] want;
        input [8*80-1:0] name;

        begin
            test_count = test_count + 1;

            if (got === want) begin
                pass_count = pass_count + 1;
                $display("[PASS] %0s : got 0x%08h", name, got);
            end
            else begin
                fail_count = fail_count + 1;
                $display("[FAIL] %0s : got 0x%08h, expected 0x%08h",
                         name, got, want);
            end
        end
    endtask


    // =========================================================================
    // AXI WRITE
    //
    // AW and W are presented together.
    // =========================================================================

    task automatic axi_write;
        input [ADDR_WIDTH-1:0] addr;
        input [31:0] data;
        reg aw_done;
        reg w_done;
        integer timeout;

        begin
            aw_done = 1'b0;
            w_done  = 1'b0;
            timeout = 0;

            @(negedge clk);

            awaddr  = addr;
            awvalid = 1'b1;

            wdata   = data;
            wstrb   = 4'b1111;
            wvalid  = 1'b1;

            // AW and W may handshake on the same clock edge.
            // Track both independently.
            while (!(aw_done && w_done)) begin
                @(posedge clk);

                if (awvalid && awready)
                    aw_done = 1'b1;

                if (wvalid && wready)
                    w_done = 1'b1;

                timeout = timeout + 1;
                if (timeout > 100) begin
                    $fatal(1, "AXI WRITE timeout waiting for AW/W: addr=0x%02h", addr);
                end

                @(negedge clk);

                if (aw_done)
                    awvalid = 1'b0;

                if (w_done)
                    wvalid = 1'b0;
            end

            // BREADY is asserted before waiting for BVALID.
            bready = 1'b1;
            timeout = 0;

            while (!bvalid) begin
                @(posedge clk);
                timeout = timeout + 1;

                if (timeout > 100) begin
                    $fatal(1, "AXI WRITE timeout waiting for BVALID: addr=0x%02h", addr);
                end
            end

            // Complete the BVALID/BREADY handshake.
            @(posedge clk);
            @(negedge clk);
            bready = 1'b0;
        end
    endtask


    // =========================================================================
    // AXI WRITE
    //
    // AW arrives first. W arrives two cycles later.
    // Both channels are still tracked by handshake, not by assumption.
    // =========================================================================

    task automatic axi_write_aw_first;
        input [ADDR_WIDTH-1:0] addr;
        input [31:0] data;
        reg aw_done;
        reg w_done;
        integer timeout;

        begin
            aw_done = 1'b0;
            w_done  = 1'b0;
            timeout = 0;

            @(negedge clk);

            awaddr  = addr;
            awvalid = 1'b1;

            while (!aw_done) begin
                @(posedge clk);

                if (awvalid && awready)
                    aw_done = 1'b1;

                timeout = timeout + 1;
                if (timeout > 100)
                    $fatal(1, "AXI AW-first timeout waiting for AWREADY");
            end

            @(negedge clk);
            awvalid = 1'b0;

            repeat (2)
                @(posedge clk);

            @(negedge clk);

            wdata   = data;
            wstrb   = 4'b1111;
            wvalid  = 1'b1;
            timeout = 0;

            while (!w_done) begin
                @(posedge clk);

                if (wvalid && wready)
                    w_done = 1'b1;

                timeout = timeout + 1;
                if (timeout > 100)
                    $fatal(1, "AXI AW-first timeout waiting for WREADY");
            end

            @(negedge clk);
            wvalid = 1'b0;

            bready = 1'b1;
            timeout = 0;

            while (!bvalid) begin
                @(posedge clk);
                timeout = timeout + 1;

                if (timeout > 100)
                    $fatal(1, "AXI AW-first timeout waiting for BVALID");
            end

            @(posedge clk);
            @(negedge clk);
            bready = 1'b0;
        end
    endtask


    // =========================================================================
    // AXI WRITE
    //
    // W arrives first. AW arrives two cycles later.
    // =========================================================================

    task automatic axi_write_w_first;
        input [ADDR_WIDTH-1:0] addr;
        input [31:0] data;
        reg aw_done;
        reg w_done;
        integer timeout;

        begin
            aw_done = 1'b0;
            w_done  = 1'b0;
            timeout = 0;

            @(negedge clk);

            wdata   = data;
            wstrb   = 4'b1111;
            wvalid  = 1'b1;

            while (!w_done) begin
                @(posedge clk);

                if (wvalid && wready)
                    w_done = 1'b1;

                timeout = timeout + 1;
                if (timeout > 100)
                    $fatal(1, "AXI W-first timeout waiting for WREADY");
            end

            @(negedge clk);
            wvalid = 1'b0;

            repeat (2)
                @(posedge clk);

            @(negedge clk);

            awaddr  = addr;
            awvalid = 1'b1;
            timeout = 0;

            while (!aw_done) begin
                @(posedge clk);

                if (awvalid && awready)
                    aw_done = 1'b1;

                timeout = timeout + 1;
                if (timeout > 100)
                    $fatal(1, "AXI W-first timeout waiting for AWREADY");
            end

            @(negedge clk);
            awvalid = 1'b0;

            bready = 1'b1;
            timeout = 0;

            while (!bvalid) begin
                @(posedge clk);
                timeout = timeout + 1;

                if (timeout > 100)
                    $fatal(1, "AXI W-first timeout waiting for BVALID");
            end

            @(posedge clk);
            @(negedge clk);
            bready = 1'b0;
        end
    endtask


    // =========================================================================
    // AXI READ
    // =========================================================================

    task automatic axi_read;
        input  [ADDR_WIDTH-1:0] addr;
        output [31:0] data;

        begin
            @(negedge clk);

            araddr  = addr;
            arvalid = 1'b1;

            while (!(arvalid && arready))
                @(posedge clk);

            @(negedge clk);

            arvalid = 1'b0;
            rready  = 1'b1;

            while (!rvalid)
                @(posedge clk);

            data = rdata;

            @(posedge clk);

            while (rvalid)
                @(posedge clk);

            @(negedge clk);
            rready = 1'b0;
        end
    endtask


    // =========================================================================
    // COMPLETE HRR OPERATION
    //
    // Writes A/B, starts accelerator, checks BUSY, polls DONE, reads RESULT.
    // =========================================================================

    task automatic run_hrr_test;
        input integer aa;
        input integer bb;

        reg [31:0] status;
        reg [31:0] result_data;

        integer expected_local;
        integer timeout;

        begin

            expected_local = (aa * bb) % Q;

            $display("");
            $display("--------------------------------------------");
            $display("HRR operation: A=%0d B=%0d expected=%0d",
                     aa, bb, expected_local);
            $display("--------------------------------------------");

            // ------------------------------------------------------------
            // Write A
            // ------------------------------------------------------------

            axi_write(5'h00, aa);

            // ------------------------------------------------------------
            // Write B
            // ------------------------------------------------------------

            axi_write(5'h04, bb);

            // ------------------------------------------------------------
            // START
            // ------------------------------------------------------------

            axi_write(5'h08, 32'h00000001);

            // ------------------------------------------------------------
            // Check BUSY
            // ------------------------------------------------------------

            axi_read(5'h0C, status);

            test_count = test_count + 1;

            if (status[1] === 1'b1) begin
                pass_count = pass_count + 1;

                $display("[PASS] BUSY asserted");
            end
            else begin
                fail_count = fail_count + 1;

                $display("[FAIL] BUSY was not asserted");
            end

            // ------------------------------------------------------------
            // Poll DONE
            // ------------------------------------------------------------

            timeout = 0;
            status  = 32'd0;

            while (!status[0] && timeout < 100) begin

                axi_read(5'h0C, status);

                timeout = timeout + 1;

            end

            test_count = test_count + 1;

            if (status[0] === 1'b1) begin
                pass_count = pass_count + 1;

                $display("[PASS] DONE asserted");
            end
            else begin
                fail_count = fail_count + 1;

                $display("[FAIL] DONE timeout");
            end

            // ------------------------------------------------------------
            // Read result
            // ------------------------------------------------------------

            axi_read(5'h10, result_data);

            actual = result_data[11:0];

            check_equal(
                actual,
                expected_local,
                "HRR RESULT"
            );

            // ------------------------------------------------------------
            // Check final STATUS
            //
            // DONE should remain sticky.
            // BUSY should be cleared.
            // ------------------------------------------------------------

            axi_read(5'h0C, status);

            test_count = test_count + 1;

            if ((status[0] === 1'b1) &&
                (status[1] === 1'b0)) begin

                pass_count = pass_count + 1;

                $display("[PASS] Final STATUS = 0x%08h", status);
            end
            else begin

                fail_count = fail_count + 1;

                $display("[FAIL] Final STATUS = 0x%08h", status);
            end

        end
    endtask


    // =========================================================================
    // MAIN TEST
    // =========================================================================

    // Global watchdog: never allow a broken handshake to hang simulation forever.
    initial begin
        #5000000;
        $fatal(1, "Global simulation timeout");
    end

    initial begin

        pass_count = 0;
        fail_count = 0;
        test_count = 0;

        // ------------------------------------------------------------
        // Initialize AXI signals.
        // ------------------------------------------------------------

        resetn  = 1'b0;

        awaddr  = 5'd0;
        awvalid = 1'b0;

        wdata   = 32'd0;
        wstrb   = 4'd0;
        wvalid  = 1'b0;

        bready  = 1'b0;

        araddr  = 5'd0;
        arvalid = 1'b0;

        rready  = 1'b0;

        // ------------------------------------------------------------
        // Header
        // ------------------------------------------------------------

        $display("");
        $display("============================================");
        $display(" HRR AXI4-Lite Wrapper Testbench");
        $display("============================================");
        $display("");

        // ------------------------------------------------------------
        // Reset
        // ------------------------------------------------------------

        repeat (4)
            @(posedge clk);

        @(negedge clk);
        resetn = 1'b1;

        @(posedge clk);
        #1;

        $display("Reset released.");
        $display("");

        // ------------------------------------------------------------
        // Check reset values.
        // ------------------------------------------------------------

        axi_read(5'h00, rd_tmp);
        check_equal_hex(
            rd_tmp,
            32'd0,
            "A reset value"
        );

        axi_read(5'h04, rd_tmp);
        check_equal_hex(
            rd_tmp,
            32'd0,
            "B reset value"
        );

        axi_read(5'h0C, rd_tmp);
        check_equal_hex(
            rd_tmp,
            32'd0,
            "STATUS reset value"
        );

        axi_read(5'h10, rd_tmp);
        check_equal_hex(
            rd_tmp,
            32'd0,
            "RESULT reset value"
        );

        // ------------------------------------------------------------
        // Basic A register test.
        // ------------------------------------------------------------

        axi_write(
            5'h00,
            32'h00000123
        );

        axi_read(
            5'h00,
            rd_tmp
        );

        check_equal_hex(
            rd_tmp,
            32'h00000123,
            "A read/write"
        );

        // ------------------------------------------------------------
        // Basic B register test.
        // ------------------------------------------------------------

        axi_write(
            5'h04,
            32'h00000456
        );

        axi_read(
            5'h04,
            rd_tmp
        );

        check_equal_hex(
            rd_tmp,
            32'h00000456,
            "B read/write"
        );

        // ------------------------------------------------------------
        // Test AW-first AXI write.
        // ------------------------------------------------------------

        axi_write_aw_first(
            5'h00,
            32'h00000222
        );

        axi_read(
            5'h00,
            rd_tmp
        );

        check_equal_hex(
            rd_tmp,
            32'h00000222,
            "AW-first write"
        );

        // ------------------------------------------------------------
        // Test W-first AXI write.
        // ------------------------------------------------------------

        axi_write_w_first(
            5'h04,
            32'h00000333
        );

        axi_read(
            5'h04,
            rd_tmp
        );

        check_equal_hex(
            rd_tmp,
            32'h00000333,
            "W-first write"
        );

        // ------------------------------------------------------------
        // Known HRR vectors.
        // ------------------------------------------------------------

        run_hrr_test(0,    0);
        run_hrr_test(0,    3328);
        run_hrr_test(1,    1);
        run_hrr_test(1,    3328);
        run_hrr_test(3328, 1);
        run_hrr_test(3328, 3328);
        run_hrr_test(123,  456);
        run_hrr_test(2048, 2048);
        run_hrr_test(3328, 3327);
        run_hrr_test(209,  257);

        // ------------------------------------------------------------
        // Randomized testing.
        //
        // $urandom_range is used with a deterministic seed.
        // ------------------------------------------------------------

        i = 0;

        while (i < 50) begin

            rand_a = $urandom_range(Q-1, 0);
            rand_b = $urandom_range(Q-1, 0);

            run_hrr_test(
                rand_a,
                rand_b
            );

            i = i + 1;

        end

        // ------------------------------------------------------------
        // Back-to-back operations.
        // ------------------------------------------------------------

        run_hrr_test(17,   19);
        run_hrr_test(1000, 2000);
        run_hrr_test(3328, 3328);

        // ------------------------------------------------------------
        // Final summary.
        // ------------------------------------------------------------

        $display("");
        $display("============================================");
        $display(" TEST SUMMARY");
        $display("============================================");

        $display(
            "Total checks : %0d",
            test_count
        );

        $display(
            "Passed       : %0d",
            pass_count
        );

        $display(
            "Failed       : %0d",
            fail_count
        );

        $display("============================================");

        if (fail_count == 0) begin

            $display("ALL TESTS PASSED");

            $finish;

        end
        else begin

            $display("TESTS FAILED");

            $fatal(1);

        end

    end

endmodule
