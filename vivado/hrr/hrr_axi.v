`timescale 1ns / 1ps

// ============================================================================
// HRR AXI4-Lite slave wrapper for the ML-KEM-512 HRR accelerator.
//
// AXI4-Lite register map (32-bit registers, word aligned):
//   0x00  A       [11:0]  Operand A
//   0x04  B       [11:0]  Operand B
//   0x08  CONTROL [0]     START (write 1 to begin; self-clearing)
//   0x0C  STATUS  [0]     DONE (sticky until the next START)
//                   [1]   BUSY
//   0x10  RESULT  [11:0]  Result, valid when DONE=1
//
// Operation:
//   software writes A and B
//   software writes CONTROL.START=1
//   wrapper generates a one-clock start pulse to hrr
//   software polls STATUS.BUSY/DONE
//   software reads RESULT
//
// AXI clock/reset:
//   S_AXI_ACLK  : accelerator clock
//   S_AXI_ARESETN: active-low AXI reset
//
// The wrapped hrr module uses a synchronous active-high reset, so the wrapper
// converts S_AXI_ARESETN to hrr_rst = !S_AXI_ARESETN.
// ============================================================================

module hrr_axi #(
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 5
)(
    input  wire                                  S_AXI_ACLK,
    input  wire                                  S_AXI_ARESETN,

    input  wire [C_S_AXI_ADDR_WIDTH-1:0]         S_AXI_AWADDR,
    input  wire                                  S_AXI_AWVALID,
    output wire                                  S_AXI_AWREADY,

    input  wire [C_S_AXI_DATA_WIDTH-1:0]         S_AXI_WDATA,
    input  wire [(C_S_AXI_DATA_WIDTH/8)-1:0]     S_AXI_WSTRB,
    input  wire                                  S_AXI_WVALID,
    output wire                                  S_AXI_WREADY,

    output wire [1:0]                            S_AXI_BRESP,
    output wire                                  S_AXI_BVALID,
    input  wire                                  S_AXI_BREADY,

    input  wire [C_S_AXI_ADDR_WIDTH-1:0]         S_AXI_ARADDR,
    input  wire                                  S_AXI_ARVALID,
    output wire                                  S_AXI_ARREADY,

    output wire [C_S_AXI_DATA_WIDTH-1:0]         S_AXI_RDATA,
    output wire [1:0]                            S_AXI_RRESP,
    output wire                                  S_AXI_RVALID,
    input  wire                                  S_AXI_RREADY
);

    localparam integer STRB_WIDTH = C_S_AXI_DATA_WIDTH / 8;

    // ------------------------------------------------------------------------
    // AXI write channel state.
    // ------------------------------------------------------------------------
    reg aw_pending;
    reg w_pending;
    reg [C_S_AXI_ADDR_WIDTH-1:0] awaddr_reg;
    reg [C_S_AXI_DATA_WIDTH-1:0] wdata_reg;
    reg [STRB_WIDTH-1:0] wstrb_reg;

    reg bvalid_reg;

    // ------------------------------------------------------------------------
    // AXI read channel state.
    // ------------------------------------------------------------------------
    reg rvalid_reg;
    reg [C_S_AXI_DATA_WIDTH-1:0] rdata_reg;

    // ------------------------------------------------------------------------
    // Accelerator/register state.
    // ------------------------------------------------------------------------
    reg [11:0] a_reg;
    reg [11:0] b_reg;
    reg        hrr_start;
    reg        done_sticky;
    reg        busy;
    reg [11:0] result_reg;

    wire hrr_done;
    wire [11:0] hrr_result;
    wire hrr_rst;

    assign hrr_rst = ~S_AXI_ARESETN;

    // Accept AW and W independently, as required by AXI4-Lite.
    assign S_AXI_AWREADY = !aw_pending && !bvalid_reg;
    assign S_AXI_WREADY  = !w_pending  && !bvalid_reg;

    assign S_AXI_BVALID = bvalid_reg;
    assign S_AXI_BRESP  = 2'b00; // OKAY

    assign S_AXI_ARREADY = !rvalid_reg;
    assign S_AXI_RVALID  = rvalid_reg;
    assign S_AXI_RDATA   = rdata_reg;
    assign S_AXI_RRESP   = 2'b00; // OKAY

    // ------------------------------------------------------------------------
    // Byte-write helper.
    // ------------------------------------------------------------------------
    function [31:0] apply_wstrb;
        input [31:0] old_value;
        input [31:0] new_value;
        input [3:0]  wstrb;
        integer i;
        begin
            apply_wstrb = old_value;
            for (i = 0; i < 4; i = i + 1) begin
                if (wstrb[i])
                    apply_wstrb[i*8 +: 8] = new_value[i*8 +: 8];
            end
        end
    endfunction

    // ------------------------------------------------------------------------
    // AXI + register controller.
    // ------------------------------------------------------------------------
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            aw_pending  <= 1'b0;
            w_pending   <= 1'b0;
            awaddr_reg  <= {C_S_AXI_ADDR_WIDTH{1'b0}};
            wdata_reg   <= {C_S_AXI_DATA_WIDTH{1'b0}};
            wstrb_reg   <= {STRB_WIDTH{1'b0}};
            bvalid_reg  <= 1'b0;

            rvalid_reg  <= 1'b0;
            rdata_reg   <= {C_S_AXI_DATA_WIDTH{1'b0}};

            a_reg       <= 12'd0;
            b_reg       <= 12'd0;
            hrr_start   <= 1'b0;
            done_sticky <= 1'b0;
            busy        <= 1'b0;
            result_reg  <= 12'd0;
        end else begin
            // hrr_start is intentionally a one-cycle pulse.
            hrr_start <= 1'b0;

            // ------------------------------------------------------------
            // AXI write-address channel.
            // ------------------------------------------------------------
            if (S_AXI_AWVALID && S_AXI_AWREADY) begin
                awaddr_reg <= S_AXI_AWADDR;
                aw_pending <= 1'b1;
            end

            // ------------------------------------------------------------
            // AXI write-data channel.
            // ------------------------------------------------------------
            if (S_AXI_WVALID && S_AXI_WREADY) begin
                wdata_reg  <= S_AXI_WDATA;
                wstrb_reg  <= S_AXI_WSTRB;
                w_pending  <= 1'b1;
            end

            // ------------------------------------------------------------
            // Execute a write once both AW and W have arrived.
            // ------------------------------------------------------------
            if (aw_pending && w_pending && !bvalid_reg) begin
                case (awaddr_reg[4:2])
                    3'b000: begin // 0x00 A
                        if (wstrb_reg[0])
                            a_reg <= wdata_reg[11:0];
                    end

                    3'b001: begin // 0x04 B
                        if (wstrb_reg[0])
                            b_reg <= wdata_reg[11:0];
                    end

                    3'b010: begin // 0x08 CONTROL
                        // START is accepted only while idle.
                        if (wstrb_reg[0] && wdata_reg[0] && !busy) begin
                            hrr_start   <= 1'b1;
                            busy        <= 1'b1;
                            done_sticky <= 1'b0;
                        end
                    end

                    default: begin
                        // STATUS and RESULT are read-only; unmapped writes
                        // are accepted and ignored with an OKAY response.
                    end
                endcase

                aw_pending <= 1'b0;
                w_pending  <= 1'b0;
                bvalid_reg <= 1'b1;
            end

            // AXI write response handshake.
            if (bvalid_reg && S_AXI_BREADY)
                bvalid_reg <= 1'b0;

            // ------------------------------------------------------------
            // AXI read-address channel.
            // ------------------------------------------------------------
            if (S_AXI_ARVALID && S_AXI_ARREADY) begin
                case (S_AXI_ARADDR[4:2])
                    3'b000: rdata_reg <= {20'd0, a_reg};
                    3'b001: rdata_reg <= {20'd0, b_reg};
                    3'b010: rdata_reg <= 32'd0; // CONTROL is write-only
                    3'b011: rdata_reg <= {30'd0, busy, done_sticky};
                    3'b100: rdata_reg <= {20'd0, result_reg};
                    default: rdata_reg <= 32'd0;
                endcase
                rvalid_reg <= 1'b1;
            end

            // AXI read-data handshake.
            if (rvalid_reg && S_AXI_RREADY)
                rvalid_reg <= 1'b0;

            // ------------------------------------------------------------
            // Accelerator completion.
            // ------------------------------------------------------------
            if (hrr_done) begin
                result_reg  <= hrr_result;
                busy        <= 1'b0;
                done_sticky <= 1'b1;
            end
        end
    end

    // ------------------------------------------------------------------------
    // HRR accelerator instance.
    // ------------------------------------------------------------------------
    hrr u_hrr (
        .clk   (S_AXI_ACLK),
        .rst   (hrr_rst),
        .start (hrr_start),
        .a     (a_reg),
        .b     (b_reg),
        .r     (hrr_result),
        .done  (hrr_done)
    );

endmodule
