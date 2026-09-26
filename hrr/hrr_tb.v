`timescale 1ns/1ps

module hrr_tb;

    reg clk;
    reg rst;
    reg start;

    reg [11:0] a;
    reg [11:0] b;

    wire [11:0] r;
    wire done;

    integer fd;
    integer scan_result;
    integer a_int;
    integer b_int;
    integer expected_int;

    integer test_count;
    integer pass_count;
    integer fail_count;

    reg [1023:0] line;

    // ============================================
    // DUT
    // ============================================

    hrr dut (
        .clk   (clk),
        .rst   (rst),
        .start (start),
        .a     (a),
        .b     (b),
        .r     (r),
        .done  (done)
    );

    // ============================================
    // Clock: 10 ns period
    // ============================================

    always #5 clk = ~clk;

    // ============================================
    // VCD waveform generation
    // ============================================

    initial begin
        $dumpfile("hrr_waveform.vcd");

        // Dump testbench and DUT signals
        $dumpvars(0, hrr_tb);
    end

    // ============================================
    // Run one test
    // ============================================

    task run_test;
        input integer test_a;
        input integer test_b;
        input integer expected;

        begin
            @(negedge clk);

            a     = test_a;
            b     = test_b;
            start = 1'b1;

            @(negedge clk);
            start = 1'b0;

            // Wait for DUT to finish
            @(posedge done);

            test_count = test_count + 1;

            if (r == expected) begin
                pass_count = pass_count + 1;

                if (test_count <= 10)
                    $display(
                        "PASS: a=%0d b=%0d -> r=%0d",
                        test_a, test_b, r
                    );
            end
            else begin
                fail_count = fail_count + 1;

                $display(
                    "FAIL: a=%0d b=%0d -> expected=%0d, got=%0d",
                    test_a, test_b, expected, r
                );
            end

            // Give DUT time to return to IDLE
            @(negedge clk);
        end
    endtask

    // ============================================
    // Main test
    // ============================================

    initial begin

        clk = 1'b0;
        rst = 1'b1;
        start = 1'b0;
        a = 12'd0;
        b = 12'd0;

        test_count = 0;
        pass_count = 0;
        fail_count = 0;

        $display("==============================================");
        $display("HRR RTL VERIFICATION");
        $display("q = 3329, R = 4096");
        $display("==============================================");

        // Reset
        #20;
        rst = 1'b0;

        // Open test-vector file
        fd = $fopen("hrr_test_vectors.txt", "r");

        if (fd == 0) begin
            $display("ERROR: Could not open hrr_test_vectors.txt");
            $finish;
        end

        // Skip header line
        scan_result = $fgets(line, fd);

        // ========================================
        // Read vectors
        // ========================================

        while (!$feof(fd)) begin

            scan_result = $fscanf(
                fd,
                "%d %d %d",
                a_int,
                b_int,
                expected_int
            );

            if (scan_result == 3) begin
                run_test(
                    a_int,
                    b_int,
                    expected_int
                );
            end
            else begin
                // Consume bad/unreadable line
               scan_result = $fgets(line, fd);
            end

        end

        $fclose(fd);

        // ========================================
        // Results
        // ========================================

        $display("");
        $display("==============================================");
        $display("VERIFICATION COMPLETE");
        $display("==============================================");
        $display("Total tests : %0d", test_count);
        $display("Passed      : %0d", pass_count);
        $display("Failed      : %0d", fail_count);
        $display("==============================================");

        if (fail_count == 0)
            $display("RESULT: ALL TESTS PASSED");
        else
            $display("RESULT: TESTS FAILED");

        $display("==============================================");

        $finish;
    end

    // ============================================
    // Safety timeout
    // ============================================

    initial begin
        #1000000;

        $display("");
        $display("ERROR: Simulation timeout!");
        $display("The HRR module may not be asserting DONE.");
        $finish;
    end

endmodule
